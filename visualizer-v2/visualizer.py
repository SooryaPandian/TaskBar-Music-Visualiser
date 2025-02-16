import sys
import numpy as np
import sounddevice as sd
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QColor, QLinearGradient
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget


class TaskbarVisualizer(QMainWindow):
    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state
        self.is_running = False
        self.stream = None

        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateVisualizer)

    def initUI(self):
        """Creates the visualizer UI."""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, 300, 40)  # Default size, will be resized in taskbar

        self.visualizerWidget = VisualizerWidget(self, self.shared_state)
        self.setCentralWidget(self.visualizerWidget)

    def startVisualizer(self):
        """Starts audio processing."""
        selected_device_name = self.shared_state.get("selected_device")
        device_index = self.shared_state.get("device_map", {}).get(selected_device_name)

        if device_index is None:
            print("No valid audio device selected!")
            return

        self.shared_state["device_index"] = device_index
        self.stopVisualizer()  # Ensure the previous stream is stopped

        try:
            self.stream = sd.InputStream(
                device=device_index,
                channels=2,
                samplerate=44100,
                blocksize=1024,
                dtype=np.int16,
                callback=self.audio_callback
            )
            self.stream.start()
            self.timer.start(30)
            self.is_running = True
            print(f"Visualizer started on: {selected_device_name}")
        except Exception as e:
            print(f"Error starting audio stream: {e}")

    def stopVisualizer(self):
        """Stops the visualizer."""
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

        width = self.width() / len(self.bars)
        for i, height in enumerate(self.bars):
            bar_height = height * self.height()
            rect = QRect(int(i * width), int(self.height() - bar_height), int(width - 2), int(bar_height))
            painter.fillRect(rect, gradient)
