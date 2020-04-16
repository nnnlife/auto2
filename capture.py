import time
import win32ui, win32gui, win32con, win32api
import winkey
from PIL import Image
import datetime, time

hwnd = None
title = ''


def enumHandler(h, lParam):
    global hwnd
    if win32gui.IsWindowVisible(h):
        #print(win32gui.GetWindowText(h))
        if title in win32gui.GetWindowText(h):
            hwnd = h
            print("Found window handle: {}".format(h))


class WinDep:
    def setting(self):
        win32gui.EnumWindows(enumHandler, None)
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        self.window_width = r - l
        self.window_height = b - t
        self.capture_time = datetime.datetime.now()
        print("Window Size: %dx%d" % (self.window_width, self.window_height))
        win32gui.SetForegroundWindow(hwnd)
        win32gui.ShowWindow(hwnd, 1)

    def __init__(self):
        pass

    def print_windows(self):
        win32gui.EnumWindows(enumHandler, None)

    def starter_found(self):
        if self.window_found('Starter'):
            return True
        
    def keyboard_security_found(self):
        if self.window_found('CREON', 408, 221):
            return True
            

    def window_found(self, name, width=-1, height=-1):
        global hwnd
        global title

        title = name
        win32gui.EnumWindows(enumHandler, None)
        if hwnd is not None:
            l, t, r, b = win32gui.GetWindowRect(hwnd)
            window_width = r - l
            window_height = b - t
            #print('****************OK')
            if (width == -1 and height == -1) or (window_width == width and window_height == height):
                win32gui.SetForegroundWindow(hwnd)
                win32gui.ShowWindow(hwnd, 1)
                hwnd = None
                title = None
                return l, t, window_width, window_height
        hwnd = None
        title = None
        return 0, 0

    def capture(self, x, y):
        dataBitMap = win32ui.CreateBitmap()
        w_handle_DC = win32gui.GetWindowDC(hwnd)
        windowDC = win32ui.CreateDCFromHandle(w_handle_DC)
        memDC = windowDC.CreateCompatibleDC()
        dataBitMap.CreateCompatibleBitmap(windowDC, self.window_width, self.window_height)
        memDC.SelectObject(dataBitMap)
        memDC.BitBlt((0, 0), (self.window_width, self.window_height), windowDC, (x, y), win32con.SRCCOPY)
        bmpinfo = dataBitMap.GetInfo()
        bmpstr = dataBitMap.GetBitmapBits(True)
        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        windowDC.DeleteDC()
        memDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, w_handle_DC)
        win32gui.DeleteObject(dataBitMap.GetHandle())
        # print("Took ", (datetime.datetime.now() - self.capture_time).total_seconds(), " s")
        self.capture_time = datetime.datetime.now()
        return im


def send_mouse_click(x, y):
    win32api.SetCursorPos((x,y))
    time.sleep(0.5)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
    time.sleep(0.5)


# Fixed width = 1214, 682
if __name__ == '__main__':
    import winkey

    count = 0
    action = 1
    win = WinDep()
    l, t, w, h = win.window_found('LINEAGE2M')
    print(l, t, w, h)

    win.window_width = w
    win.window_height = h
    l, t = 0, 0
    hangup_count = 0
    im = win.capture(l, t)
    im.save('hello.jpeg')
