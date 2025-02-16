import sounddevice as sd

def detect_audio_devices():
    """Detects available system audio & microphones."""
    devices = sd.query_devices()
    device_map = {device["name"]: idx for idx, device in enumerate(devices)}
    return device_map

# Shared state
shared_state = {
    "color_start": (255, 105, 180),  # Default pink gradient start
    "color_end": (255, 0, 0),        # Default red gradient end
    "sensitivity": 0.1,
    "device_map": detect_audio_devices(),
    "selected_device": None,  # Selected audio device
}
