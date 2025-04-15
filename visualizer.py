import sys
import numpy as np
import sounddevice as sd
import threading
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QColor, QLinearGradient
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
import tkinter as tk
from tkinter import colorchooser, Scale, HORIZONTAL, Button, Label, OptionMenu, StringVar


class TaskbarVisualizer(QMainWindow):
    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state
        self.is_running = False
        self.stream = None

        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateVisualizer)
#POLAYAADIMONE
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(0, screen_geometry.height() - 40, screen_geometry.width() // 4, 40)

        self.visualizerWidget = VisualizerWidget(self, self.shared_state)
        self.setCentralWidget(self.visualizerWidget)

    def startVisualizer(self):
        selected_device_name = self.shared_state.get("selected_device")
        device_index = self.shared_state.get("device_map", {}).get(selected_device_name)

        if device_index is None:
            print("No valid audio device selected!")
            return

        self.shared_state["device_index"] = device_index

        self.stopVisualizer()  # Ensure the previous stream is stopped before restarting

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
            self.shared_state["toggle_button"].config(text="Stop Visualizer")  # Update button text
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
            self.shared_state["toggle_button"].config(text="Start Visualizer")  # Update button text

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


def detect_audio_devices():
    """Detects available system audio & microphones."""
    devices = sd.query_devices()
    device_map = {}

    for idx, device in enumerate(devices):
        name = device["name"]
        device_map[name] = idx
    return device_map


def launch_control_panel(shared_state, visualizer):
    """Launches the Tkinter control panel for user settings."""
    
    def update_device(device_name):
        shared_state["selected_device"] = device_name
        print(f"Selected Audio Device: {device_name}")
        visualizer.startVisualizer()  # Auto-restart the visualizer when a new device is selected

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

    def toggle_visualizer():
        """Toggles between start and stop states."""
        if visualizer.is_running:
            visualizer.stopVisualizer()
        else:
            visualizer.startVisualizer()

    root = tk.Tk()
    root.title("Visualizer Control Panel")
    root.geometry("350x300")

    # Audio Device Selection
    Label(root, text="Select Audio Device:").pack()
    device_map = shared_state.get("device_map", {})
    selected_device_var = StringVar(root)
    
    if device_map:
        first_device = next(iter(device_map))  # Get first device as default
        selected_device_var.set(first_device)
        shared_state["selected_device"] = first_device  # Store first as default
    else:
        selected_device_var.set("No valid device found")

    device_dropdown = OptionMenu(root, selected_device_var, *device_map.keys(), command=update_device)
    device_dropdown.pack(pady=5)

    # Color Settings
    Button(root, text="Set Start Color", command=update_color_start).pack(pady=5)
    Button(root, text="Set End Color", command=update_color_end).pack(pady=5)

    # Sensitivity Slider
    Label(root, text="Sensitivity").pack()
    sensitivity_scale = Scale(root, from_=1, to=100, orient=HORIZONTAL, command=update_sensitivity)
    sensitivity_scale.set(10)
    sensitivity_scale.pack()

    # Toggle Start/Stop Button
    toggle_button = Button(root, text="Start Visualizer", command=toggle_visualizer)
    toggle_button.pack(pady=5)
    shared_state["toggle_button"] = toggle_button  # Store button reference

    root.mainloop()


if __name__ == '__main__':
    shared_state = {
        "color_start": (255, 105, 180),
        "color_end": (255, 0, 0),
        "sensitivity": 0.1,
        "device_map": detect_audio_devices()
    }

    app = QApplication(sys.argv)
    visualizer = TaskbarVisualizer(shared_state)

    control_panel_thread = threading.Thread(target=launch_control_panel, args=(shared_state, visualizer), daemon=True)
    control_panel_thread.start()

    visualizer.show()
    sys.exit(app.exec_())
