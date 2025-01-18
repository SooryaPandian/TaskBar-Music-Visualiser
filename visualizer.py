import sys
import numpy as np
import sounddevice as sd
import threading
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QColor, QLinearGradient
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
import tkinter as tk
from tkinter import colorchooser, Scale, HORIZONTAL


class TaskbarVisualizer(QMainWindow):
    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state
        self.initUI()
        self.initAudio()
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateVisualizer)
        self.timer.start(30)  # Update every 30ms

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen_geometry = QApplication.desktop().screenGeometry()
        taskbar_height = QApplication.desktop().availableGeometry().height() - screen_geometry.height()
        self.setGeometry(0, screen_geometry.height() - 40, screen_geometry.width() // 4, 40)

        self.visualizerWidget = VisualizerWidget(self, self.shared_state)
        self.setCentralWidget(self.visualizerWidget)

    def initAudio(self):
        self.CHUNK = 1024
        self.RATE = 44100
        self.channels = 2

        devices = sd.query_devices()
        for device in devices:
            if 'Stereo Mix' in device['name'] or 'virtual cable' in device['name'].lower():
                self.device_index = device['index']
                break
        else:
            print("No system audio input device found. Please check your system settings.")
            sys.exit(1)

        self.stream = sd.InputStream(
            device=self.device_index,
            channels=self.channels,
            samplerate=self.RATE,
            blocksize=self.CHUNK,
            dtype=np.int16,
            callback=self.audio_callback
        )
        self.stream.start()

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        fft = np.abs(np.fft.fft(indata[:, 0]))
        self.visualizerWidget.updateBars(fft)

    def updateVisualizer(self):
        pass

    def closeEvent(self, event):
        self.stream.stop()
        event.accept()


class VisualizerWidget(QWidget):
    def __init__(self, parent, shared_state):
        super().__init__(parent)
        self.shared_state = shared_state
        self.bars = [0] * 50

    def updateBars(self, fft):
        sensitivity = self.shared_state.get("sensitivity", 0.1)
        scaled_fft = [value * sensitivity for value in fft]
        step = len(scaled_fft) // len(self.bars)
        self.bars = [
            min(max(scaled_fft[i * step:(i + 1) * step]), 10000) / 10000
            for i in range(len(self.bars))
        ]
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        color_start = QColor(*self.shared_state.get("color_start", (255, 105, 180)))
        color_end = QColor(*self.shared_state.get("color_end", (255, 0, 0)))

        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, color_start)
        gradient.setColorAt(1, color_end)

        painter.setBrush(gradient)
        width = self.width() / len(self.bars)

        for i, height in enumerate(self.bars):
            bar_height = height * self.height()
            rect = QRect(
                int(i * width),
                int(self.height() - bar_height),
                int(width - 2),
                int(bar_height)
            )
            painter.fillRect(rect, gradient)


def launch_control_panel(shared_state):
    def update_color_start():
        color = colorchooser.askcolor()[0]
        if color:
            shared_state["color_start"] = tuple(map(int, color))

    def update_color_end():
        color = colorchooser.askcolor()[0]
        if color:
            shared_state["color_end"] = tuple(map(int, color))

    def update_sensitivity(value):
        shared_state["sensitivity"] = float(value) / 100

    root = tk.Tk()
    root.title("Visualizer Control Panel")
    root.geometry("300x200")

    tk.Button(root, text="Set Start Color", command=update_color_start).pack(pady=10)
    tk.Button(root, text="Set End Color", command=update_color_end).pack(pady=10)

    tk.Label(root, text="Sensitivity").pack()
    sensitivity_scale = Scale(root, from_=1, to=100, orient=HORIZONTAL, command=update_sensitivity)
    sensitivity_scale.set(10)
    sensitivity_scale.pack()

    root.mainloop()


if __name__ == '__main__':
    shared_state = {
        "color_start": (255, 105, 180),
        "color_end": (255, 0, 0),
        "sensitivity": 0.1
    }

    control_panel_thread = threading.Thread(target=launch_control_panel, args=(shared_state,), daemon=True)
    control_panel_thread.start()

    app = QApplication(sys.argv)
    visualizer = TaskbarVisualizer(shared_state)
    visualizer.show()
    sys.exit(app.exec_())
