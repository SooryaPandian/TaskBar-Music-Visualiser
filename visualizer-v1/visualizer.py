import sys
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QColor, QLinearGradient
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from audio_processor import AudioProcessor

class TaskbarVisualizer(QMainWindow):
    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state
        self.is_running = False

        self.initUI()
        self.audio_processor = AudioProcessor(shared_state, self.visualizerWidget)
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateVisualizer)

    def initUI(self):
        """Initializes the taskbar UI."""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(0, screen_geometry.height() - 40, screen_geometry.width() // 4, 40)

        self.visualizerWidget = VisualizerWidget(self, self.shared_state)
        self.setCentralWidget(self.visualizerWidget)

    def startVisualizer(self):
        """Starts the visualizer and audio processing."""
        self.audio_processor.start_stream()
        self.timer.start(30)
        self.is_running = True
        print("Visualizer started!")

    def stopVisualizer(self):
        """Stops the visualizer and audio processing."""
        self.audio_processor.stop_stream()
        self.timer.stop()
        self.is_running = False
        print("Visualizer stopped!")

    def updateVisualizer(self):
        """Redraws the visualizer."""
        self.visualizerWidget.repaint()

    def closeEvent(self, event):
        """Handles cleanup on close."""
        self.stopVisualizer()
        event.accept()

class VisualizerWidget(QWidget):
    def __init__(self, parent, shared_state):
        super().__init__(parent)
        self.shared_state = shared_state
        self.bars = [0] * 50

    def updateBars(self, fft):
        """Updates bars based on FFT data."""
        sensitivity = self.shared_state.get("sensitivity", 0.1)
        scaled_fft = [value * sensitivity for value in fft]
        step = len(scaled_fft) // len(self.bars)
        self.bars = [
            min(max(scaled_fft[i * step:(i + 1) * step]), 10000) / 10000
            for i in range(len(self.bars))
        ]
        self.repaint()

    def paintEvent(self, event):
        """Handles visual rendering."""
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
            rect = QRect(int(i * width), int(self.height() - bar_height), int(width - 2), int(bar_height))
            painter.fillRect(rect, gradient)
