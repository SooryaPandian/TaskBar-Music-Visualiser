from settings import shared_state
from visualizer import TaskbarVisualizer
from ui_controls import launch_control_panel
import threading
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
visualizer = TaskbarVisualizer(shared_state)
threading.Thread(target=launch_control_panel, args=(shared_state, visualizer), daemon=True).start()
visualizer.show()
sys.exit(app.exec_())
