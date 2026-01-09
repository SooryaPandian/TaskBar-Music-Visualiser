import sounddevice as sd

print("=== NORMAL DEVICES ===")
for i, d in enumerate(sd.query_devices()):
    print(i, d['name'], "| in:", d['max_input_channels'], "out:", d['max_output_channels'])

print("\n=== LOOPBACK DEVICES (WASAPI ONLY) ===")
try:
    for i, d in enumerate(sd.query_devices(kind='loopback')):
        print(i, d['name'], "| in:", d['max_input_channels'])
except TypeError:
    print("Your sounddevice version is too old for kind='loopback'")
