from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from scw.config import Config

import os


class ConfigFileWatcher:

    class EventHandler(FileSystemEventHandler):
        def __init__(self, config: Config):
            self.config = config
            self.config_path = os.path.abspath(config.config_path)
            self.dir_name = os.path.dirname(self.config_path)

        def on_modified(self, event):
            if not isinstance(event, FileModifiedEvent):
                # Ignore file changes
                return

            if event.src_path != self.config_path:
                return

            self.config.reload()

    def __init__(self, config: Config):
        config_path = os.path.abspath(config.config_path)
        config_dir = os.path.dirname(config_path)

        self.handler = ConfigFileWatcher.EventHandler(config)
        self.observer = Observer()
        self.observer.schedule(self.handler, path=config_dir)

    def __enter__(self):
        self.observer.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.observer.stop()
        self.observer.join()
