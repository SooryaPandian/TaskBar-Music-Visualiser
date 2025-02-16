import numpy as np
import sounddevice as sd

class AudioProcessor:
    def __init__(self, shared_state, visualizer_widget):
        self.shared_state = shared_state
        self.visualizer_widget = visualizer_widget
        self.stream = None

    def start_stream(self):
        """Starts the audio processing stream."""
        selected_device_name = self.shared_state.get("selected_device")
        device_index = self.shared_state.get("device_map", {}).get(selected_device_name)

        if device_index is None:
            print("No valid audio device selected!")
            return

        self.shared_state["device_index"] = device_index

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
            print(f"Audio Stream started on: {selected_device_name}")
        except Exception as e:
            print(f"Error starting audio stream: {e}")

    def stop_stream(self):
        """Stops the audio processing stream."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            print("Audio Stream stopped.")

    def audio_callback(self, indata, frames, time, status):
        """Processes FFT from the audio input stream."""
        if status:
            print(status)
        fft = np.abs(np.fft.fft(indata[:, 0]))
        self.visualizer_widget.updateBars(fft)
