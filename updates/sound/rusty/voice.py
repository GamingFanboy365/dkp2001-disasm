#!/usr/bin/env python3
"""Rusty's voice (updates patch): his sounds, synthesised for this project (no recordings,
nothing of anyone else's). A cartoon rooster farmer: a raspy pitched voice through vowel
formants, with short noise bursts for the consonants.

    python3 updates/sound/rusty/voice.py [--wav DIR]

writes, next to this script, one signed 8-bit 8000 Hz sample per sound (NAME.bin, the
format of the game's sound effects), and with --wav also WAV files to listen to:
  crow        "cock-a-doodle-doo!"  power-up, picking him
  cheer       "buk-buk-BAWK!"       happy
  whoop       a bright rising cluck  happy
  yeehaw      "yee-haw!"            happy
  brawk       "BRAWK!"              hit
  squawk1/2   flustered squawks     random hits
  cluck       "buk"                 the select cursor landing on him
"""
import math
import os
import random
import struct
import sys
import wave

RATE = 8000
PITCH = 1.15                     # a touch higher than first drafted, for clarity
HERE = os.path.dirname(os.path.abspath(__file__))

VOWELS = {                       # formants (Hz) and bandwidths
    "aw": ((700, 1050, 2450), (110, 140, 220)),
    "ah": ((780, 1220, 2550), (110, 140, 220)),
    "uh": ((560, 1000, 2400), (100, 130, 200)),
    "oo": ((360, 820, 2300), (90, 120, 200)),
    "ee": ((300, 2250, 3000), (80, 160, 250)),
    "eh": ((520, 1800, 2550), (90, 150, 220)),
}


class Resonator:
    def __init__(self, f, bw):
        self.set(f, bw)
        self.y1 = self.y2 = 0.0

    def set(self, f, bw):
        r = math.exp(-math.pi * bw / RATE)
        self.a1 = 2 * r * math.cos(2 * math.pi * f / RATE)
        self.a2 = -r * r
        self.g = 1 - r

    def __call__(self, x):
        y = self.g * x + self.a1 * self.y1 + self.a2 * self.y2
        self.y2, self.y1 = self.y1, y
        return y


def voice(segments, rasp=0.18, seed=1):
    """segments: (duration s, vowel, pitch start Hz, pitch end Hz, amplitude, attack s).
    A glottal-ish pulse source with vibrato, jitter and rasp, formant-filtered; vowels glide
    into each other."""
    rnd = random.Random(seed)
    out = []
    phase = 0.0
    res = [Resonator(700, 100), Resonator(1100, 130), Resonator(2500, 200)]
    prev = VOWELS[segments[0][1]]
    for dur, vw, p0, p1, amp, att in segments:
        n = int(dur * RATE)
        tgt = VOWELS[vw]
        for i in range(n):
            t = i / max(1, n - 1)
            glide = min(1.0, i / (0.04 * RATE))
            for k in range(3):
                f = prev[0][k] + (tgt[0][k] - prev[0][k]) * glide
                b = prev[1][k] + (tgt[1][k] - prev[1][k]) * glide
                if i % 32 == 0:
                    res[k].set(f, b)
            pitch = (p0 + (p1 - p0) * t) * PITCH
            pitch *= 1 + 0.035 * math.sin(2 * math.pi * 6.5 * i / RATE) + 0.012 * (rnd.random() - 0.5)
            phase += pitch / RATE
            if phase >= 1:
                phase -= 1
            # a sharp vocal pulse (bright, many harmonics) with a little body
            src = 1.6 * math.exp(-phase * 9.0) - 0.18 + 0.25 * (1 - 2 * phase)
            src += rasp * (rnd.random() * 2 - 1) * (0.4 + 0.6 * math.exp(-phase * 6.0))
            env = min(1.0, i / max(1, att * RATE)) * min(1.0, (n - i) / (0.025 * RATE))
            y = res[0](src) * 1.0 + res[1](src) * 1.05 + res[2](src) * 0.85
            out.append(y * amp * env)
        prev = tgt
    return out


def burst(dur, f, bw, amp, seed=2):
    """A consonant: a short filtered noise burst (k, d, b)."""
    rnd = random.Random(seed)
    r = Resonator(f, bw)
    n = int(dur * RATE)
    return [r(rnd.random() * 2 - 1) * amp * (1 - i / n) ** 2 for i in range(n)]


def silence(dur):
    return [0.0] * int(dur * RATE)


def cat(*parts):
    out = []
    for p in parts:
        out += p
    return out


def normalise(x, peak=1.0, drive=2.6):
    """Bright and loud, as the game's voice samples are: a pre-emphasis lift on the highs,
    then a soft-clip compressor up to full scale."""
    y, prev = [], 0.0
    for v in x:
        y.append(v - 0.82 * prev)
        prev = v
    m = max(1e-9, max(abs(v) for v in y))
    y = [math.tanh(drive * v / m) for v in y]
    m = max(1e-9, max(abs(v) for v in y))
    return [v * peak / m for v in y]


def sounds():
    s = {}
    s["crow"] = cat(burst(0.025, 1900, 900, 0.8), voice([(0.11, "uh", 430, 520, 0.8, 0.01)]),
                    burst(0.02, 1900, 900, 0.7), voice([(0.09, "ah", 520, 600, 0.85, 0.01)]),
                    burst(0.015, 2600, 1200, 0.5), voice([(0.12, "oo", 600, 680, 0.85, 0.01)]),
                    burst(0.015, 2600, 1200, 0.5), voice([(0.08, "uh", 640, 600, 0.75, 0.01)]),
                    burst(0.015, 2600, 1200, 0.5),
                    voice([(0.18, "oo", 640, 820, 1.0, 0.02), (0.38, "oo", 820, 560, 0.95, 0.0)], rasp=0.24))
    buk = lambda p, a, seed: cat(burst(0.018, 700, 500, 0.9, seed), voice([(0.075, "uh", p, p * 0.9, a, 0.004)], seed=seed))
    s["cheer"] = cat(buk(420, 0.8, 3), silence(0.05), buk(440, 0.85, 4), silence(0.05),
                     burst(0.02, 700, 500, 0.9, 5), voice([(0.1, "aw", 500, 820, 1.0, 0.005), (0.18, "aw", 820, 520, 0.95, 0.0)], rasp=0.3, seed=5))
    s["whoop"] = cat(buk(460, 0.8, 6), silence(0.03),
                     voice([(0.12, "ah", 480, 900, 0.95, 0.005), (0.12, "eh", 900, 760, 0.9, 0.0)], rasp=0.2, seed=7))
    s["yeehaw"] = cat(voice([(0.08, "ee", 520, 700, 0.8, 0.01), (0.14, "ee", 700, 880, 0.95, 0.0)], rasp=0.2, seed=8),
                      silence(0.04), burst(0.04, 1200, 1400, 0.5, 9),
                      voice([(0.08, "ah", 760, 720, 0.95, 0.005), (0.22, "aw", 720, 480, 0.95, 0.0)], rasp=0.26, seed=9))
    s["brawk"] = cat(burst(0.02, 700, 500, 1.0, 10),
                     voice([(0.06, "ah", 700, 980, 1.0, 0.003), (0.16, "aw", 980, 560, 1.0, 0.0)], rasp=0.42, seed=10))
    s["squawk1"] = cat(burst(0.015, 2400, 1200, 0.6, 11),
                       voice([(0.05, "eh", 760, 1000, 0.9, 0.003), (0.09, "aw", 1000, 680, 0.95, 0.0)], rasp=0.38, seed=11))
    s["squawk2"] = cat(buk(520, 0.85, 12), silence(0.02), buk(600, 0.9, 13), silence(0.02),
                       voice([(0.1, "ah", 640, 520, 0.9, 0.004)], rasp=0.35, seed=14))
    s["cluck"] = buk(430, 0.9, 15)
    return {k: normalise(v) for k, v in s.items()}


def main():
    wavdir = sys.argv[sys.argv.index("--wav") + 1] if "--wav" in sys.argv else None
    for name, x in sounds().items():
        pcm = bytes((max(-128, min(127, int(round(v * 127)))) & 0xFF) for v in x)
        open(os.path.join(HERE, name + ".bin"), "wb").write(pcm)
        if wavdir:
            os.makedirs(wavdir, exist_ok=True)
            w = wave.open(os.path.join(wavdir, name + ".wav"), "wb")
            w.setnchannels(1), w.setsampwidth(1), w.setframerate(RATE)
            w.writeframes(bytes((max(-128, min(127, int(round(v * 127)))) + 128) & 0xFF for v in x))
            w.close()
        print(f"{name}: {len(pcm)} samples ({len(pcm) / RATE:.2f} s)")


if __name__ == "__main__":
    main()
