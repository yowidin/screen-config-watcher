from typing import List

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QGuiApplication, QScreen
from PySide6.QtWidgets import QMainWindow, QApplication

import sys
import signal
import subprocess
import json

from sys import platform

from scw.log import Log
from scw.options import Options
from scw.config import Config
from scw.config_file_watcher import ConfigFileWatcher

from obwsc.cli.obws_command import main


# noinspection PyUnresolvedReferences
class MainWindow(QMainWindow):
    config_changed = Signal()

    @staticmethod
    def print_screen_info(screen: QScreen):
        Log.info(f"name='{screen.name()}', manufacturer='{screen.manufacturer()}', "
                 f"model='{screen.model()}', s/n='{screen.serialNumber()}'")

    def __init__(self, options: Options, **kwargs):
        super().__init__(**kwargs)

        self.options = options

        self.app = QGuiApplication.instance()
        self.app.screenAdded.connect(self.screen_added)
        self.app.screenRemoved.connect(self.screen_removed)

        self.apply_changes_timer = QTimer()
        self.apply_changes_timer.setSingleShot(True)
        self.apply_changes_timer.timeout.connect(self.apply_changes)

        self.options.config.subscribe_to_changes(self.handle_config_change)
        self.config_changed.connect(self._restart_timer)

        Log.info('Listing current screens...')
        screens = self.app.screens()  # type: List[QScreen]
        for screen in screens:
            self.print_screen_info(screen)

        self.last_screens = [x.name() for x in screens]

        self.screen_change_observer = self._subscribe_to_screen_change_events()
        self.screen_lock_listener = self._subscribe_to_screen_lock_events()

    def _manual_recheck(self):
        Log.debug(f'Display configuration changed, getting a fresh display list')

        code = """from scw.screen_change.windows import get_display_list
get_display_list() 
        """
        try:
            get_res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout
        except subprocess.CalledProcessError as e:
            Log.error("Error while running the target function:", e)
            return

        monitors_json = json.loads(get_res)
        new_list = [x['name'] for x in monitors_json]

        if sorted(self.last_screens) != sorted(new_list):
            Log.info('Software configuration changed')
            self._restart_timer()

        self.last_screens = new_list

    def _subscribe_to_screen_lock_events(self):
        if sys.platform == 'darwin':
            from scw.screen_lock.macos import MacOS
            return MacOS(on_lock=self._on_screen_locked, on_unlock=self._on_screen_unlocked)

        # TODO: Linux and Windows

    def _subscribe_to_screen_change_events(self):
        if platform == 'win32':
            # Handle screen configuration changes on Windows: Qt somehow doesn't generate a new list of screens
            from scw.screen_change.windows import ScreenChangeObserver

            def screen_change(*_):
                self._manual_recheck()

            return ScreenChangeObserver(screen_change)

    def _run_obws_command(self, *args):
        Log.debug(f'Running OBWS command: {" ".join(args)}')
        if self.options.dry_run:
            Log.debug('Dry run, skipping')
            return

        try:
            # noinspection PyTypeChecker
            main(args)
        except RuntimeError as e:
            Log.error(f'Command error: {e}')

    def _on_screen_locked(self):
        self._run_obws_command('--config', self.options.config.obwsc_config, 'pause-record')

    def _on_screen_unlocked(self):
        self._run_obws_command('--config', self.options.config.obwsc_config, 'resume-record')

    def _restart_timer(self):
        self.apply_changes_timer.start(self.options.config.grace_period * 1000)

    def handle_config_change(self, _: Config):
        self.config_changed.emit()

    def start(self):
        self._restart_timer()

    def screen_added(self, screen: QScreen):
        Log.info('Screen added')
        MainWindow.print_screen_info(screen)
        self.last_screens = [x.name() for x in self.app.screens()]
        self._restart_timer()

    def screen_removed(self, screen: QScreen):
        Log.info('Screen removed')
        MainWindow.print_screen_info(screen)
        self.last_screens = [x.name() for x in self.app.screens()]
        self._restart_timer()

    def apply_changes(self):
        Log.debug('Applying changes...')

        presets = self.options.config.find_matching_preset(self.last_screens)
        if len(presets) == 0:
            Log.warning(f'No preset found for {self.last_screens}')
            return

        if len(presets) > 1:
            Log.warning(f'Multiple presets found for {self.last_screens}: {[x.name for x in presets]}')
            return

        preset = presets[0]

        Log.debug(f'Applying preset: {preset.name}. Profile: {preset.profile_name}, '
                  f'Scene Collection: {preset.scene_collection_name}')

        self._run_obws_command('--config', self.options.config.obwsc_config, 'switch-profile-and-scene-collection',
                               preset.profile_name, preset.scene_collection_name)

    def closeEvent(self, event):
        if self.screen_change_observer is not None:
            self.observer.destroy()

        event.accept()


# noinspection PyUnresolvedReferences
class ScreenConfigWatcherApp:
    INSTANCE = None  # type: ScreenConfigWatcherApp
    SIGNAL_TIMER_MS = 100

    def __init__(self, options: Options):
        self.hide_dock()
        self.app = QApplication(sys.argv)

        signal.signal(signal.SIGINT, ScreenConfigWatcherApp.signal_handler)
        signal.signal(signal.SIGTERM, ScreenConfigWatcherApp.signal_handler)
        if platform != 'win32':
            signal.signal(signal.SIGQUIT, ScreenConfigWatcherApp.signal_handler)
        else:
            self.app.setAttribute(Qt.ApplicationAttribute.AA_NativeWindows, True)

        # Let the interpreter run each 500 ms, otherwise we can't receive signals
        self.signal_timer = QTimer()
        self.signal_timer.timeout.connect(lambda: None)

        self.widget = MainWindow(options)

        ScreenConfigWatcherApp.INSTANCE = self

    # noinspection PyPackageRequirements
    @staticmethod
    def hide_dock():
        if sys.platform == 'darwin':
            import AppKit
            info = AppKit.NSBundle.mainBundle().infoDictionary()
            info["LSBackgroundOnly"] = "1"

    @staticmethod
    def signal_handler(signal_number, _):
        Log.debug(f'Received signal: {signal_number}. Quitting...')
        ScreenConfigWatcherApp.INSTANCE.app.quit()

    def run(self):
        with ConfigFileWatcher(config=self.widget.options.config):
            self.signal_timer.start(ScreenConfigWatcherApp.SIGNAL_TIMER_MS)
            self.widget.start()
            res = self.app.exec()

        sys.exit(res)
