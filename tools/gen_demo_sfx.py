"""Generate simple demo SFX WAV files into assets/sfx.
Creates: click.wav, startup.wav, success.wav, error.wav
"""
import os
import wave
import struct
import math

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'sfx')
os.makedirs(OUT_DIR, exist_ok=True)

def write_wave(filename, samples, sample_rate=44100):
    path = os.path.join(OUT_DIR, filename)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(struct.pack('<h', int(max(-32767, min(32767, s)))) for s in samples))
    print('Wrote', path)

def sine_wave(freq, duration, volume=0.5, sample_rate=44100):
    samples = []
    total = int(sample_rate * duration)
    for i in range(total):
        t = i / sample_rate
        # simple envelope: quick attack & release
        env = 1.0
        if t < 0.01:
            env = t / 0.01
        elif t > duration - 0.01:
            env = max(0.0, (duration - t) / 0.01)
        samples.append(int(volume * env * 32767 * math.sin(2 * math.pi * freq * t)))
    return samples

# click: short broadband-ish using two sine partials
click = []
click += sine_wave(1200, 0.03, 0.7)
click += sine_wave(2200, 0.02, 0.35)
write_wave('click.wav', click)

# startup: warm chord-ish arpeggio
startup = []
startup += sine_wave(440, 0.18, 0.45)
startup2 = sine_wave(660, 0.12, 0.35)
# mix startup2 into startup with offset
for i, s in enumerate(startup2):
    if i < len(startup):
        startup[i] = int(startup[i] * 0.8 + s * 0.2)
write_wave('startup.wav', startup)

# success: rising short tone
success = []
success += sine_wave(660, 0.08, 0.6)
success += sine_wave(880, 0.08, 0.45)
write_wave('success.wav', success)

# error: short low thud + quick dissonant
error = []
error += sine_wave(120, 0.12, 0.8)
err2 = sine_wave(260, 0.06, 0.4)
for i, s in enumerate(err2):
    if i < len(error):
        error[i] = int(error[i] * 0.7 + s * 0.3)
write_wave('error.wav', error)

print('Demo SFX generation complete.')

