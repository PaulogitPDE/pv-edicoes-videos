"""Trilha e efeitos sonoros do @crmquevende, 100% sintetizados em numpy (sem direitos autorais, sem ElevenLabs).
trilha(): batida tech/lo-fi com acordes e baixo. efeito(): pop, ding, whoosh, tick, slam, riser, check, risco, glitch."""
import numpy as np

SR = 44100


def _env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-t / d)


def _suave(x, k):
    """Passa-baixa simples (média móvel)."""
    return np.convolve(x, np.ones(k) / k, mode='same') if k > 1 else x


def _ruido(n, seed):
    return np.random.default_rng(seed).standard_normal(n)


def _nota(m):
    return 440 * 2 ** ((m - 69) / 12)


PROGS = [  # acordes (midi) – 4 compassos
    [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 66]],
    [[50, 53, 57, 60], [58, 62, 65, 69], [53, 57, 60, 64], [48, 52, 55, 58]],
    [[52, 55, 59, 62], [48, 52, 55, 59], [55, 59, 62, 66], [50, 54, 57, 60]],
    [[45, 48, 52, 55], [53, 57, 60, 64], [48, 52, 55, 59], [52, 56, 59, 62]],
]


def trilha(dur, semente=1):
    rng = np.random.default_rng(semente)
    bpm = [108, 112, 116, 120][semente % 4]
    b = 60 / bpm
    n = int(dur * SR)
    mix = np.zeros(n)
    prog = PROGS[semente % len(PROGS)]

    def put(sig, t, g=1.0):
        i = int(t * SR)
        if i >= n:
            return
        e = min(n, i + len(sig))
        mix[i:e] += sig[:e - i] * g

    L = int(0.5 * SR)
    t = np.arange(L) / SR
    kick = np.tanh(np.sin(2 * np.pi * np.cumsum(50 + 110 * np.exp(-t * 30)) / SR) * _env(L, 0.001, 0.22) * 2)
    clap = _suave(_ruido(int(0.25 * SR), 1), 3) * _env(int(0.25 * SR), 0.001, 0.06)
    hat_r = _ruido(int(0.06 * SR), 2)
    hat = (hat_r - _suave(hat_r, 6)) * _env(len(hat_r), 0.0005, 0.018)
    beats = int(dur / b) + 1
    for k in range(beats):
        tb = k * b
        put(kick, tb, 0.85)
        if k % 2 == 1:
            put(clap, tb, 0.32)
        put(hat, tb + b / 2, 0.22)
        if rng.random() < 0.5:
            put(hat, tb + b * 0.75, 0.12)
    # pump (sidechain) para pad e baixo
    tt = np.arange(n) / SR
    pump = 1 - 0.65 * np.exp(-((tt % b) / 0.11))
    pad = np.zeros(n)
    baixo = np.zeros(n)
    comp = 4 * b
    for c in range(int(dur / comp) + 1):
        acorde = prog[c % 4]
        i0, i1 = int(c * comp * SR), min(n, int((c + 1) * comp * SR))
        if i0 >= n:
            break
        tl = np.arange(i1 - i0) / SR
        envp = np.minimum(tl / 0.25, 1) * np.minimum((comp - tl) / 0.15, 1)
        for m in acorde:
            for det in (0.997, 1.003):
                fr = _nota(m) * det
                pad[i0:i1] += (np.sin(2 * np.pi * fr * tl) + 0.4 * np.sin(4 * np.pi * fr * tl) + 0.2 * np.sin(6 * np.pi * fr * tl)) * envp
        raiz = _nota(acorde[0] - 24)
        for k in range(8):
            ts = k * b / 2 + b / 4
            j0 = int(ts * SR)
            seg = np.arange(int(b / 2 * SR)) / SR
            nota = np.tanh(np.sin(2 * np.pi * raiz * seg) * 1.6) * _env(len(seg), 0.004, 0.16)
            e = min(i1 - i0, j0 + len(seg))
            if j0 < e:
                baixo[i0 + j0:i0 + e] += nota[:e - j0]
        # arpejo nos compassos ímpares
        if c % 2 == 1:
            for k in range(16):
                m = acorde[rng.integers(4)] + 12
                put(np.sin(2 * np.pi * _nota(m) * np.arange(int(0.2 * SR)) / SR) * _env(int(0.2 * SR), 0.002, 0.07), c * comp + k * b / 4, 0.07)
    mix += _suave(pad, 9) * 0.035 * pump + baixo * 0.28 * pump
    fade = np.minimum(tt / 0.4, 1) * np.minimum((dur - tt) / 0.8, 1)
    mix *= np.clip(fade, 0, 1)
    pico = np.abs(mix).max() or 1
    return mix / pico * 0.55


def efeito(nome, seed=0):
    if nome == 'pop':
        L = int(0.09 * SR); t = np.arange(L) / SR
        return np.sin(2 * np.pi * np.cumsum(500 + 1400 * t / 0.09) / SR) * _env(L, 0.001, 0.03) * 0.6
    if nome == 'ding':
        L = int(0.7 * SR); t = np.arange(L) / SR
        return (np.sin(2 * np.pi * 1318.5 * t) * _env(L, 0.001, 0.25) + 0.7 * np.sin(2 * np.pi * 1975.5 * t) * np.exp(-np.maximum(t - 0.09, 0) / 0.3) * (t > 0.09)) * 0.32
    if nome == 'whoosh':
        L = int(0.38 * SR); t = np.arange(L) / SR
        r = _ruido(L, 10 + seed)
        alto = r - _suave(r, 4)
        env = np.sin(np.pi * np.clip(t / 0.38, 0, 1)) ** 2
        return (_suave(r, 12) * 0.7 + alto * 0.25) * env * 0.5
    if nome == 'tick':
        L = int(0.025 * SR)
        r = _ruido(L, 20 + seed)
        return (r - _suave(r, 3)) * _env(L, 0.0003, 0.004) * 0.5
    if nome == 'slam':
        L = int(0.6 * SR); t = np.arange(L) / SR
        grave = np.sin(2 * np.pi * np.cumsum(40 + 90 * np.exp(-t * 18)) / SR) * _env(L, 0.001, 0.25)
        return np.tanh((grave * 1.4 + _suave(_ruido(L, 30), 2) * _env(L, 0.001, 0.03)) * 1.5) * 0.7
    if nome == 'riser':
        L = int(0.8 * SR); t = np.arange(L) / SR
        return (np.sin(2 * np.pi * np.cumsum(200 + 900 * (t / 0.8) ** 2) / SR) * 0.3 + _suave(_ruido(L, 40), 5) * 0.4) * (t / 0.8) ** 2 * 0.4
    if nome == 'check':
        L = int(0.16 * SR); t = np.arange(L) / SR
        f = np.where(t < 0.07, 880, 1320)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(L, 0.001, 0.06) * 0.35
    if nome == 'risco':
        L = int(0.4 * SR)
        r = _suave(_ruido(L, 50 + seed), 3)
        return r * (0.5 + 0.5 * np.sin(np.arange(L) / SR * 2 * np.pi * 18)) * _env(L, 0.02, 0.2) * 0.12
    if nome == 'glitch':
        L = int(0.3 * SR)
        r = _ruido(L, 60 + seed)
        corte = (np.floor(np.arange(L) / (SR * 0.018)) % 2).astype(float)
        return (r - _suave(r, 2)) * corte * _env(L, 0.001, 0.12) * 0.35
    raise ValueError(nome)
