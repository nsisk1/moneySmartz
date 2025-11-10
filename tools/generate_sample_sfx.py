import wave
import math
import struct
import os

# Generate a short click (impulse-like) and a short startup tone (sine sweep)

def write_wav(path, samples, framerate=44100):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(b''.join(struct.pack('<h', int(max(-32767, min(32767, s)))) for s in samples))


def generate_click(duration_ms=60, framerate=44100):
    samples = []
    # Click: short burst of decaying white-noise-like values
    length = int(framerate * (duration_ms / 1000.0))
    for i in range(length):
        # decaying envelope
        env = (1.0 - float(i) / length)
        # simple noise by a deterministic pseudo-random using sine of index
        val = math.sin(i * 12.9898) * 43758.5453
        noise = (val - math.floor(val)) * 2 - 1
        samples.append(int(noise * 16000 * env))
    return samples


def generate_startup(duration_ms=800, framerate=44100):
    samples = []
    length = int(framerate * (duration_ms / 1000.0))
    # simple rising sine tone from 300Hz to 1200Hz
    for i in range(length):
        t = float(i) / length
        freq = 300 + (1200 - 300) * t
        s = math.sin(2.0 * math.pi * freq * (i / framerate))
        # gentle fade-in and fade-out
        env = 0.5 * (1 - math.cos(math.pi * t))
        samples.append(int(s * 18000 * env))
    return samples


def main():
    root = os.path.dirname(os.path.dirname(__file__))
    sfx_dir = os.path.join(root, 'assets', 'sfx')
    os.makedirs(sfx_dir, exist_ok=True)
    click_path = os.path.join(sfx_dir, 'click.wav')
    startup_path = os.path.join(sfx_dir, 'startup.wav')
    print('Generating', click_path)
    write_wav(click_path, generate_click())
    print('Generating', startup_path)
    write_wav(startup_path, generate_startup())
    print('Done')

if __name__ == '__main__':
    main()

