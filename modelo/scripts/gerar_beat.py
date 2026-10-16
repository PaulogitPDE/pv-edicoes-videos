"""Gera uma batida escura estilo phonk (120 bpm), 100% sintetizada, sem direitos autorais.
Uso: python3 scripts/gerar_beat.py public/beat.wav [segundos] [semente]"""
import sys, wave
import numpy as np

out = sys.argv[1] if len(sys.argv) > 1 else 'public/beat.wav'
dur = float(sys.argv[2]) if len(sys.argv) > 2 else 40
rng = np.random.default_rng(int(sys.argv[3]) if len(sys.argv) > 3 else 7)
SR = 44100
bpm = 120
beat = 60 / bpm
n = int(dur * SR)
mix = np.zeros(n)

def put(sig, t, g=1.0):
    i = int(t * SR)
    if i >= n: return
    e = min(n, i + len(sig))
    mix[i:e] += sig[: e - i] * g

def env(L, a=0.002, d=0.2):
    t = np.arange(int(L * SR)) / SR
    return np.minimum(t / a, 1) * np.exp(-t / d)

def kick808(freq=46, L=0.9):
    t = np.arange(int(L * SR)) / SR
    f = freq + 120 * np.exp(-t * 35)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * env(L, 0.001, 0.45)
    return np.tanh(s * 2.2)

def clap(L=0.25):
    s = rng.standard_normal(int(L * SR)) * env(L, 0.001, 0.06)
    return np.convolve(s, np.ones(6) / 6, 'same')

def hat(L=0.05):
    s = rng.standard_normal(int(L * SR))
    s = np.diff(np.concatenate([[0], s]))
    return s * env(L, 0.0005, 0.012)

def cowbell(freq, L=0.35):
    t = np.arange(int(L * SR)) / SR
    s = (np.sign(np.sin(2 * np.pi * freq * t)) + np.sign(np.sin(2 * np.pi * freq * 1.48 * t))) * 0.5
    return s * env(L, 0.001, 0.09)

# escala menor (Fá#) para o cowbell
notas = [740, 880, 831, 740, 659, 740, 554, 622]
padrao = rng.permutation(len(notas))
b = 0
t = 0.0
while t < dur:
    bar = b // 4
    pos = b % 4
    if pos in (0, 2) or (pos == 3 and bar % 2 == 1):
        put(kick808(46 if bar % 4 < 2 else 41), t, 0.9)
    if pos in (1, 3):
        put(clap(), t, 0.45)
    for k in range(2):
        put(hat(), t + k * beat / 2, 0.18 if k else 0.12)
    if bar >= 1:
        for k in range(2):
            idx = padrao[(b * 2 + k) % len(notas)]
            put(cowbell(notas[idx]), t + k * beat / 2, 0.16)
    b += 1
    t = b * beat

# pad grave contínuo
tt = np.arange(n) / SR
pad = (np.sin(2 * np.pi * 92.5 * tt) + 0.5 * np.sin(2 * np.pi * 138.6 * tt)) * 0.08 * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 8))
mix += pad
mix = np.tanh(mix * 1.3)
mix /= np.max(np.abs(mix)) * 1.05
pcm = (mix * 32767).astype(np.int16)
with wave.open(out, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', out, dur)
