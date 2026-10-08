"""Скриншоты окон десктоп-приложения (для отчёта и сайта).

Запуск: python make_screenshots.py [каталог_вывода]
По умолчанию пишет в <корень>/report/images.
"""
import ctypes
import os
import sys
import time

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import ImageGrab  # noqa: E402
import win32gui  # noqa: E402

from main import App  # noqa: E402


def grab_window(app, path):
    hwnd = app.winfo_id()
    hwnd = win32gui.GetAncestor(hwnd, 2)  # GA_ROOT
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    time.sleep(0.3)
    image = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    image.save(path)
    print("save:", path, image.size)


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        BASE, "report", "images")
    os.makedirs(out_dir, exist_ok=True)

    app = App()
    app.update_idletasks()
    app.attributes("-topmost", True)
    app.lift()
    app.focus_force()
    app.update()
    time.sleep(1.0)
    app.update()

    grab_window(app, os.path.join(out_dir, "desktop_services.png"))

    app.tabview.set("Заявки")
    app.update()
    time.sleep(0.5)
    app.update()
    grab_window(app, os.path.join(out_dir, "desktop_requests.png"))

    app.tabview.set("Отчёты")
    app.update()
    time.sleep(0.5)
    app.update()
    grab_window(app, os.path.join(out_dir, "desktop_reports.png"))

    app.destroy()


if __name__ == "__main__":
    main()
