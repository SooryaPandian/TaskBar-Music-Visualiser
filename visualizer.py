import sys
import numpy as np
import sounddevice as sd
import threading
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QColor, QLinearGradient
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
import tkinter as tk
from tkinter import colorchooser, Scale, HORIZONTAL, Button

class TaskbarVisualizer(QMainWindow):
    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state
        self.is_running = False  # Track visualizer state (stopped by default)
        self.stream = None

        self.initUI()
        self.initAudio()

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateVisualizer)
        
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

        # Select system audio input (Stereo Mix / Virtual Cable)
        devices = sd.query_devices()
        self.device_index = None
        for idx, device in enumerate(devices):
            if 'Stereo Mix' in device['name'] or 'virtual cable' in device['name'].lower():
                self.device_index = idx
                break

        if self.device_index is None:
            print("No system audio input device found. Please check your system settings.")
            sys.exit(1)

    def startVisualizer(self):
        if not self.is_running:
            try:
                self.stream = sd.InputStream(
                    device=self.device_index,
                    channels=self.channels,
                    samplerate=self.RATE,
                    blocksize=self.CHUNK,
                    dtype=np.int16,
                    callback=self.audio_callback
                )
                self.stream.start()
                self.timer.start(30)  # Update every 30ms
                self.is_running = True
                print("Visualizer started!")
            except Exception as e:
                print(f"Error starting audio stream: {e}")

    def stopVisualizer(self):
        if self.is_running:
            self.timer.stop()
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            self.is_running = False
            print("Visualizer stopped!")

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        fft = np.abs(np.fft.fft(indata[:, 0]))
        self.visualizerWidget.updateBars(fft)

    def updateVisualizer(self):
        self.visualizerWidget.repaint()

    def closeEvent(self, event):
        self.stopVisualizer()
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


def launch_control_panel(shared_state, visualizer):
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
    root.geometry("300x250")

    tk.Button(root, text="Set Start Color", command=update_color_start).pack(pady=5)
    tk.Button(root, text="Set End Color", command=update_color_end).pack(pady=5)

    tk.Label(root, text="Sensitivity").pack()
    sensitivity_scale = Scale(root, from_=1, to=100, orient=HORIZONTAL, command=update_sensitivity)
    sensitivity_scale.set(10)
    sensitivity_scale.pack()

    # Start & Stop Buttons
    Button(root, text="Start Visualizer", command=visualizer.startVisualizer).pack(pady=5)
    Button(root, text="Stop Visualizer", command=visualizer.stopVisualizer).pack(pady=5)

    root.mainloop()


if __name__ == '__main__':
    shared_state = {
        "color_start": (255, 105, 180),
        "color_end": (255, 0, 0),
        "sensitivity": 0.1
    }

    print(sd.query_devices())  # List available audio devices

    app = QApplication(sys.argv)
    visualizer = TaskbarVisualizer(shared_state)

    control_panel_thread = threading.Thread(target=launch_control_panel, args=(shared_state, visualizer), daemon=True)
    control_panel_thread.start()

    visualizer.show()
    sys.exit(app.exec_())
