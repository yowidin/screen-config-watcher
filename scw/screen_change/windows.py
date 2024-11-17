from typing import Callable

import win32con
from win32gui import CreateWindowEx, WNDCLASS, RegisterClass, DefWindowProc, DestroyWindow
from win32api import GetModuleHandle


class ScreenChangeObserver:
    """ Hidden window-based observer to capture WM_DISPLAYCHANGE messages. """

    def __init__(self, callback: Callable[[int, int, int], None]):
        self.callback = callback
        self.hwnd = self._create_hidden_window()

    def destroy(self):
        if self.hwnd is not None:
            DestroyWindow(self.hwnd)
            self.hwnd = None

    def _create_hidden_window(self):
        class_name = "SCWHiddenDisplayChangeObserver"
        hinstance = GetModuleHandle(None)

        wndclass = WNDCLASS()
        wndclass.lpfnWndProc = self._window_proc
        wndclass.lpszClassName = class_name
        wndclass.hInstance = hinstance
        RegisterClass(wndclass)

        hwnd = CreateWindowEx(0, class_name, None, win32con.WS_OVERLAPPED, win32con.CW_USEDEFAULT,
                              win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, None, None,
                              hinstance, None)

        return hwnd

    def _window_proc(self, hwnd, msg, wparam, lparam):
        """
        Window procedure to handle messages.
        """
        if msg == win32con.WM_DISPLAYCHANGE:
            # Extract resolution and bit depth
            screen_width = lparam & 0xFFFF
            screen_height = (lparam >> 16) & 0xFFFF
            bpp = wparam
            self.callback(screen_width, screen_height, bpp)

        return DefWindowProc(hwnd, msg, wparam, lparam)


def get_display_list():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QScreen
    from typing import List
    import json

    app = QApplication([])
    screens = app.screens()  # type: List[QScreen]

    res = []
    for screen in screens:
        res.append({
            'name': screen.name(),
            'model': screen.model(),
            'serial': screen.serialNumber(),
            'manufacturer': screen.manufacturer(),
        })

    print(json.dumps(res))
