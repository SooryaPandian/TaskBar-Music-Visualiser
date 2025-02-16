import sys
import threading
import win32gui
from PyQt5.QtWidgets import QApplication
from visualizer import TaskbarVisualizer
from control_panel import launch_control_panel
from taskbar import set_visualizer_taskbar


if __name__ == '__main__':
    shared_state = {
        "color_start": (255, 105, 180),
        "color_end": (255, 0, 0),
        "sensitivity": 0.1,
        "device_map": {},  # Populate this dynamically
    }

    app = QApplication(sys.argv)
    visualizer = TaskbarVisualizer(shared_state)
    
    threading.Thread(target=launch_control_panel, args=(shared_state, visualizer), daemon=True).start()

    set_visualizer_taskbar(int(visualizer.winId()))
    visualizer.show()
    sys.exit(app.exec_())
