import win32gui
import win32con
import win32api


def set_visualizer_taskbar(hwnd):
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    ex_style |= win32con.WS_EX_TOOLWINDOW
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 300, 40, win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW)

    taskbar_hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
    win32gui.SetParent(hwnd, taskbar_hwnd)
