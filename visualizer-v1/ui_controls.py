import tkinter as tk
from tkinter import colorchooser, Scale, HORIZONTAL, Button, Label, OptionMenu, StringVar

def launch_control_panel(shared_state, visualizer):
    """Launches the Tkinter control panel for user settings."""
    
    def update_device(device_name):
        shared_state["selected_device"] = device_name
        visualizer.startVisualizer()

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
    root.geometry("350x300")

    Label(root, text="Select Audio Device:").pack()
    device_map = shared_state.get("device_map", {})
    selected_device_var = StringVar(root, next(iter(device_map), "No Device"))
    device_dropdown = OptionMenu(root, selected_device_var, *device_map.keys(), command=update_device)
    device_dropdown.pack(pady=5)

    Button(root, text="Set Start Color", command=update_color_start).pack()
    Button(root, text="Set End Color", command=update_color_end).pack()

    Label(root, text="Sensitivity").pack()
    Scale(root, from_=1, to=100, orient=HORIZONTAL, command=update_sensitivity).pack()

    root.mainloop()
