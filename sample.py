import tkinter as tk
import threading
import time
import numpy as np
from PIL import Image, ImageDraw
import pystray
import win32gui
import win32con
import win32api


class VisualizerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # no border
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        bar_height = 40
        # docked at bottom (taskbar overlay)
        self.root.geometry(f"{screen_w}x{bar_height}+0+{screen_h - bar_height}")

        self.canvas = tk.Canvas(self.root, bg="black", height=bar_height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Control panel (hidden initially)
        self.control_panel = tk.Toplevel(self.root)
        self.control_panel.title("Music Visualizer Controls")
        self.control_panel.geometry("300x200")
        self.control_panel.withdraw()

        tk.Label(self.control_panel, text="Control Panel").pack(pady=10)
        tk.Button(self.control_panel, text="Enable Mic Visualizer", command=self.enable_mic).pack(pady=5)
        tk.Button(self.control_panel, text="Disable Mic Visualizer", command=self.disable_mic).pack(pady=5)
        tk.Button(self.control_panel, text="Quit", command=self.quit).pack(pady=5)

        # state
        self.running = True
        self.use_mic = False  # off by default
        self.bar_count = 30

        # make overlay click-through
        self.make_clickthrough()

        # start visualizer loop
        threading.Thread(target=self.animate, daemon=True).start()

        # setup tray
        threading.Thread(target=self.setup_tray, daemon=True).start()

        self.root.mainloop()

    def make_clickthrough(self):
        hwnd = win32gui.FindWindow(None, str(self.root.title()))
        # get current style
        styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        # add layered + transparent
        styles |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, styles)
        # set opacity (255 fully opaque)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)

    def animate(self):
        while self.running:
            self.canvas.delete("all")
            width = self.root.winfo_width() // self.bar_count
            if self.use_mic:
                # TODO: implement mic FFT capture here
                heights = np.random.randint(5, 40, size=self.bar_count)
            else:
                # default random animation
                heights = np.random.randint(5, 40, size=self.bar_count)

            bar_height = self.root.winfo_height()
            for i, h in enumerate(heights):
                x0, y0 = i * width, bar_height - h
                x1, y1 = (i + 1) * width, bar_height
                self.canvas.create_rectangle(x0, y0, x1, y1, fill="lime", width=0)

            time.sleep(0.1)

    def setup_tray(self):
        image = Image.new("RGB", (64, 64), "black")
        dc = ImageDraw.Draw(image)
        dc.rectangle([16, 16, 48, 48], fill="lime")

        def show_panel(icon, item):
            self.root.after(0, self.control_panel.deiconify)

        def quit_app(icon, item):
            self.root.after(0, self.quit)

        menu = pystray.Menu(
            pystray.MenuItem("Open Control Panel", show_panel),
            pystray.MenuItem("Quit", quit_app)
        )

        icon = pystray.Icon("musicviz", image, "Music Visualizer", menu)
        icon.run()

    def enable_mic(self):
        self.use_mic = True

    def disable_mic(self):
        self.use_mic = False

    def quit(self):
        self.running = False
        self.root.quit()


if __name__ == "__main__":
    VisualizerApp()
