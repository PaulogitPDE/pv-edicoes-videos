"""Motor de reels do @crmquevende (sem Remotion, sem biblioteca de motion): cada frame é desenhado com Pillow/numpy
e o ffmpeg só codifica. Uso (na raiz do repo): python3 crm/motor/reel.py crm/roteiros/AAAA-MM-DD-r1.json crm/postados/AAAA-MM-DD-r1.mp4

Roteiro JSON: {"tarja": "...", "semente": 3, "cenas": [{"tipo": ..., "legenda": "...", "dur": 3.0, ...}]}
Tipos de cena: gancho, chat, leads, timeline, numero, desenho (funil|grafico), lista, cta (direct|bio|comenta), data, virada.
Cada cena tem um humor (dor = halo e fundo vermelhos, solucao = lime), forçável com 'humor'. Padrão criativo: crm/DIRETOR.md.
Texto entre <sinais> vira destaque lime com brilho. Tudo é animado aqui, à mão: câmera (push, pan, giro, tremida),
transições (whip com motion blur, zoom com flash, glitch RGB), bolinhas neon piscando, traços sendo desenhados,
pop-ups de lead pulando na tela, contadores, digitação, ondas de toque e explosões de partículas."""
import json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from base import *  # noqa: E402,F403
from base import _fonte  # noqa: E402
import som  # noqa: E402

W, H, FPS = 1080, 1920, 30
TR = 6  # frames de transição


# ---------- camadas globais ----------
def _fundo():
    y, x = np.mgrid[0:H + 90, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.9)) ** 2 + ((y - H / 2) / (H * 0.55)) ** 2)
    t = np.clip(d / 0.75, 0, 1)[..., None]
    arr = np.array(BG2, np.float32) * (1 - t) + np.array(BG, np.float32) * t
    g = np.clip(1 - d / 0.45, 0, 1)[..., None] * 0.06
    arr = arr * (1 - g) + np.array(LIME, np.float32) * g
    grade = ((x % 90) < 2) | ((y % 90) < 2)
    arr[grade] = arr[grade] * 0.86 + 255 * 0.035
    return Image.fromarray(arr.astype(np.uint8)).convert('RGBA')


def _vinheta():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.75)) ** 2 + ((y - H / 2) / (H * 0.62)) ** 2)
    return Image.fromarray((np.clip((d - 0.55) / 0.55, 0, 1) * 0.75 * 255).astype(np.uint8))


FUNDO, VIN = _fundo(), _vinheta()
PRETO = Image.new('RGB', (W, H), BG)
PONTOS = [(rnd('px', i) * W, rnd('py', i) * H, [LIME, LIME, CIANO, ROSA, LIME][i % 5], rnd('pf', i), 40 + rnd('pp', i) * 70, 3 + int(rnd('pr', i) * 4))
          for i in range(18)]


def fundo(F):
    off = int(90 - (F * 1.5) % 90)
    base = FUNDO.crop((0, off, W, off + H))
    for x, y, cor, fase, per, r in PONTOS:
        b = math.sin(2 * math.pi * (F / per + fase))
        a = 0.12 + 0.88 * clamp01(b * 3)
        if rnd('fl', x, F // 2) < 0.06:
            a *= 0.2  # piscada rápida
        yy = (y - F * (0.6 + r * 0.15)) % (H + 100) - 50
        colar(base, neon(cor, r), x + math.sin(F / 30 + fase * 6) * 12, yy, alpha=a)
    return base


def explosao(base, x, y, d, semente, cor=LIME, n=18, raio=280, dur=22):
    """Partículas neon saindo de um ponto."""
    if not 0 <= d < dur:
        return
    p = sai(d / dur)
    for k in range(n):
        ang = rnd('ea', semente, k) * math.pi * 2
        v = 0.4 + rnd('ev', semente, k) * 0.6
        c = [cor, TXT, CIANO][k % 3] if cor == LIME else cor
        colar(base, neon(c, 4 + k % 3), x + math.cos(ang) * raio * v * p, y + math.sin(ang) * raio * v * p + d * d * 0.15, alpha=1 - d / dur)


def onda(base, x, y, d, cor=LIME, dur=18):
    """Onda de toque (ripple)."""
    if 0 <= d < dur:
        for k in (0, 6):
            q = (d - k) / dur
            if 0 < q < 1:
                colar(base, anel(cor, int(30 + 90 * sai(q))), x, y, alpha=1 - q)


def contador_sprite(n, cor):
    return _contador(int(n), cor)


@lru_cache(maxsize=256)
def _contador(n, cor):
    s = 46
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=cor + (255,))
    f = _fonte('xbold', 24)
    t = str(n)
    d.text((s / 2 - f.getlength(t) / 2, 9), t, font=f, fill=BG + (255,))
    return im


@lru_cache(maxsize=256)
def balao(texto, lado, meta=''):
    texto = limpa(texto)
    f, fm = _fonte('semi', 36), _fonte('med', 22)
    linhas, atual = [], ''
    for w in texto.split():
        if atual and f.getlength(atual + ' ' + w) > 540:
            linhas.append(atual); atual = w
        else:
            atual = (atual + ' ' + w).strip()
    linhas.append(atual)
    eu = lado == 'eu'
    tw = max(f.getlength(l) for l in linhas)
    mw = fm.getlength(meta) + (46 if eu else 0) if meta else 0
    w = int(max(tw, mw) + 52)
    h = len(linhas) * 46 + 34 + (28 if meta else 0)
    cor = LIME if eu else (44, 54, 72)
    tc = BG if eu else TXT
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 28, fill=cor + (255,))
    d.rectangle([w - 26, h - 26, w - 1, h - 1] if eu else [0, h - 26, 25, h - 1], fill=cor + (255,))
    for i, l in enumerate(linhas):
        d.text((26, 16 + i * 46), l, font=f, fill=tc + (255,))
    if meta:
        mc = (40, 60, 20) if eu else MUTED
        d.text((w - 26 - mw, h - 38), meta, font=fm, fill=mc + (255,))
        if eu:  # dois tiques de lido
            x0, y0 = w - 62, h - 26
            for dx in (0, 12):
                d.line([(x0 + dx, y0), (x0 + dx + 7, y0 + 7), (x0 + dx + 19, y0 - 7)], fill=(30, 120, 200, 255), width=3)
    return im


def digitando(f, lado='ela'):
    im = Image.new('RGBA', (130, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 129, 69], 28, fill=(44, 54, 72, 255))
    for k in range(3):
        y = 35 + math.sin(f * 0.5 - k * 0.9) * 7
        d.ellipse([30 + k * 28 - 8, y - 8, 30 + k * 28 + 8, y + 8], fill=(200, 205, 215, 255))
    return im


@lru_cache(maxsize=32)
def avatar(letra, cor, r=38):
    im = Image.new('RGBA', (2 * r, 2 * r), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=cor + (255,))
    f = _fonte('black', int(r * 0.95))
    asc, desc = f.getmetrics()
    d.text((r - f.getlength(letra) / 2, r - (asc + desc) / 2), letra, font=f, fill=BG + (255,))
    return im


@lru_cache(maxsize=32)
def carimbo(txt, cor=VERMELHO):
    txt = limpa(txt).upper()
    f = _fonte('black', 78)
    w = int(f.getlength(txt)) + 90
    h = 150
    pad = 30
    im = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    m = Image.new('L', im.size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], 18, outline=255, width=10)
    d.text((pad + 45, pad + 28), txt, font=f, fill=255)
    im.paste(cor + (255,), (0, 0), m.filter(ImageFilter.GaussianBlur(14)).point(lambda v: v // 2))
    fundo_ = Image.new('L', im.size, 0)
    ImageDraw.Draw(fundo_).rounded_rectangle([pad, pad, pad + w, pad + h], 18, fill=200)
    im.paste((20, 6, 8, 255), (0, 0), fundo_)
    im.paste(cor + (255,), (0, 0), m)
    return im.rotate(8, expand=True, resample=Image.BICUBIC)


def valor_num(v):
    dig = ''.join(ch for ch in str(v) if ch.isdigit())
    return int(dig) if dig else 0


# ---------- cenas ----------
class Cena:
    dur_padrao = 3.0

    def __init__(self, c, t0, ev, idx):
        self.c, self.t0, self.ev, self.idx = c, t0, ev, idx
        self.trem = []
        self.dur = round(c.get('dur', self.dur_padrao) * FPS)

    def som(self, f, nome, g=1.0):
        self.ev.append((self.t0 + f, nome, g))

    def tremer(self, f, forca=1.0):
        self.trem.append((f, forca))

    def texto_topo(self, base, f, ini=2, y=470):
        if getattr(self, 'tt', None):
            self.tt.draw(base, W / 2, y + self.tt.alt / 2 - 40, f, ini, 'pop', 3)

    def prep_texto_topo(self, ini=2):
        self.tt = Texto(self.c['texto'], self.c.get('tam', 74), max_w=940) if self.c.get('texto') else None
        if self.tt:
            for i in range(0, self.tt.n, 2):
                self.som(ini + i * 3, 'pop', 0.35)


class Gancho(Cena):
    dur_padrao = 2.8

    def __init__(self, *a):
        super().__init__(*a)
        c = self.c
        nw = len(runs(limpa(c['texto'])))
        self.t = Texto(c['texto'], c.get('tam') or (150 if nw <= 3 else 124 if nw <= 6 else 102), max_w=950)
        self.rot = rotulo(c['rotulo'], 30, CORES.get(c.get('cor_rotulo', 'vermelho'), VERMELHO)) if c.get('rotulo') else None
        for i in range(self.t.n):
            self.som(6 + i * 5, 'slam' if i == 0 else 'pop', 1 if i == 0 else 0.6)
            self.tremer(6 + i * 5, 1 if i == 0 else 0.35)
        self.fim = 6 + self.t.fim(5) + 8
        self.rab = c.get('rabisco', 'sublinha')
        if self.rab:
            self.som(self.fim, 'risco')

    def draw(self, base, f):
        cy = 900
        if self.rot:
            p = sai(f / 9)
            colar(base, self.rot, W / 2, cy - self.t.alt / 2 - 70 + (1 - p) * 30, alpha=p)
        explosao(base, W / 2, cy, f - 6, self.idx)
        self.t.draw(base, W / 2, cy, f, 6, 'slam', 5)
        if self.rab and f >= self.fim:
            cor = VERMELHO if self.rab == 'x' else LIME
            traco(base, forma(self.rab, *self.t.caixa_dest(W / 2, cy), semente=self.idx), sai((f - self.fim) / 14), cor, 10)


class Chat(Cena):
    dur_padrao = 4.4
    X0, Y0, X1, Y1 = 80, 400, 1000, 1250

    def __init__(self, *a):
        super().__init__(*a)
        c = self.c
        nome = c.get('nome', 'Paciente')
        self.av = avatar(nome[0].upper(), CORES.get(c.get('cor', 'rosa'), ROSA))
        self.nome = palavra(nome, 38, 'bold', TXT, False, False)
        self.status = palavra(limpa(c.get('status', 'online')), 24, 'med', MUTED, False, False)
        self.msgs, t = [], 10
        for m in c['mensagens']:
            ela = m.get('de', 'ela') != 'eu'
            if ela:
                t += 16
            self.msgs.append((t, balao(m['texto'], 'ela' if ela else 'eu', m.get('meta', '')), ela))
            self.som(t, 'ding' if ela else 'pop', 0.45 if ela else 0.6)
            t += 15
        self.tc = None
        if c.get('carimbo'):
            self.tc = t + 6
            self.stamp = carimbo(c['carimbo'], CORES.get(c.get('cor_carimbo', 'vermelho'), VERMELHO))
            self.som(self.tc, 'slam')
            self.tremer(self.tc, 1.2)

    def draw(self, base, f):
        p = sai(f / 10)
        X0, Y0, X1, Y1 = self.X0, self.Y0 + (1 - p) * 120, self.X1, self.Y1 + (1 - p) * 120
        colar(base, cartao(X1 - X0, Y1 - Y0, 36, (17, 23, 33, 245)), (X0 + X1) / 2, (Y0 + Y1) / 2, alpha=p)
        colar(base, self.av, X0 + 70, Y0 + 66, alpha=p)
        colar(base, self.nome, X0 + 120, Y0 + 26, alpha=p, canto=True)
        colar(base, self.status, X0 + 120, Y0 + 68, alpha=p, canto=True)
        # bolinha "online" piscando
        colar(base, neon(LIME if 'online' in self.c.get('status', 'online') else MUTED, 5), X1 - 50, Y0 + 66, alpha=0.4 + 0.6 * (math.sin(f / 4) > 0))
        ImageDraw.Draw(base).line([(X0 + 20, Y0 + 130), (X1 - 20, Y0 + 130)], fill=(255, 255, 255, 30), width=2)
        corpo_h = int(Y1 - Y0 - 160)
        lay = Image.new('RGBA', (X1 - X0 - 40, corpo_h), (0, 0, 0, 0))
        itens = []
        for t, sp, ela in self.msgs:
            if f >= t:
                itens.append((sp, ela, mola(f - t, 11, 0.5, 200)))
            elif ela and f >= t - 16:
                itens.append((digitando(f), True, 1.0))
                break
            else:
                break
        alt = sum((sp.height + 20) * min(1, s) for sp, _, s in itens)
        y = 10 - max(0, alt - corpo_h + 20)
        for sp, ela, s in itens:
            x = 10 + sp.width / 2 if ela else lay.width - 10 - sp.width / 2
            h = (sp.height + 20) * min(1, s)
            colar(lay, sp, x + (1 - s) * (-60 if ela else 60), y + sp.height / 2 + (1 - s) * 30, 0.6 + 0.4 * s, clamp01(s * 2))
            y += h
        colar(base, lay, X0 + 20, Y0 + 145, canto=True)
        if self.tc is not None and f >= self.tc:
            s = mola(f - self.tc, 9, 0.5, 240)
            colar(base, self.stamp, W / 2, 1000, 2.4 + (1 - 2.4) * s, clamp01((f - self.tc) / 3))


class Leads(Cena):
    dur_padrao = 6.0

    def __init__(self, *a):
        super().__init__(*a)
        c = self.c
        self.cols = c.get('colunas', ['Novo', 'Orçamento', 'Follow-up', 'Agendado'])
        n = len(self.cols)
        self.cw = (960 - 14 * (n - 1)) / n
        self.cx = [60 + self.cw / 2 + k * (self.cw + 14) for k in range(n)]
        self.titulo = rotulo(c.get('titulo', 'Funil de orçamentos'), 28, TXT)
        self.hdr = [rotulo(x, 20 if n > 3 else 24, LIME if k == n - 1 else MUTED, 3) for k, x in enumerate(self.cols)]
        self.leads = []
        t = 8
        for i, L in enumerate(c['leads']):
            pop = notificacao(L['nome'], L.get('proc', ''), c.get('aviso', 'Novo lead'))
            card = cartao_lead(L['nome'], L.get('proc', ''), L.get('valor', ''), int(self.cw - 16), False)
            card_ok = cartao_lead(L['nome'], L.get('proc', ''), L.get('valor', ''), int(self.cw - 16), True)
            self.leads.append(dict(L, pop=pop, card=card, ok=card_ok, a=t, col=L.get('col', 0), num=valor_num(L.get('valor', 0)), x=None, y=None,
                                   pos=(rnd('lx', i) * 300 + 390, 640 + (i % 3) * 190)))
            self.som(t, 'ding', 0.5)
            self.som(t + 16, 'whoosh', 0.4)
            self.som(t + 26, 'pop', 0.5)
            self.tremer(t + 2, 0.25)
            t += 11
        # movimentos depois que todos pousaram
        self.movs = []
        t += 22
        for i, L in enumerate(self.leads):
            alvo = L.get('vai')
            while alvo is not None and L['col'] + len([m for m in self.movs if m[0] == i]) < alvo:
                c0 = L['col'] + len([m for m in self.movs if m[0] == i])
                self.movs.append((i, t, c0, c0 + 1))
                self.som(t, 'whoosh', 0.35)
                if c0 + 1 == n - 1:
                    self.som(t + 12, 'check', 0.8)
                    self.tremer(t + 12, 0.3)
                t += 12
        self.t_total = t
        self.total = c.get('total')

    def coluna(self, i, f):
        L, col = self.leads[i], self.leads[i]['col']
        mov = None
        for j, t, c0, c1 in self.movs:
            if j == i and f >= t:
                col = c1 if f >= t + 12 else c0
                if f < t + 12:
                    mov = (t, c0, c1)
        return col, mov

    def draw(self, base, f):
        n = len(self.cols)
        p = sai(f / 10)
        colar(base, self.titulo, 60, 400, alpha=p, canto=True)
        colar(base, neon(VERMELHO, 6), 60 + self.titulo.width + 26, 418, alpha=0.3 + 0.7 * (math.sin(f / 3) > 0))
        for k in range(n):
            pk = sai((f - k * 3) / 10)
            colar(base, cartao(int(self.cw), 800, 22, (18, 25, 37, 225), sombra=24), self.cx[k], 470 + 400 + (1 - pk) * 80, alpha=pk)
            colar(base, self.hdr[k], self.cx[k] - self.cw / 2 + 16, 490, alpha=pk, canto=True)
        # quem está em cada coluna agora
        em = {k: [] for k in range(n)}
        for i, L in enumerate(self.leads):
            if f >= L['a'] + 26:
                col, mov = self.coluna(i, f)
                if not mov:
                    chegada = max([t + 12 for j, t, c0, c1 in self.movs if j == i and f >= t + 12] + [L['a'] + 26])
                    em[col].append((chegada, i))
        alvo = {}
        for k in range(n):
            for slot, (_, i) in enumerate(sorted(em[k])):
                alvo[i] = (self.cx[k], 580 + slot * 104)
            if em[k]:
                cs = contador_sprite(len(em[k]), LIME if k == n - 1 else MUTED)
                colar(base, cs, self.cx[k] + self.cw / 2 - 30, 506, mola(f - max(t for t, _ in em[k]), 9, 0.5, 220) * 0.4 + 0.6)
        voando = []
        for i, L in enumerate(self.leads):
            d = f - L['a']
            if d < 0:
                continue
            col, mov = self.coluna(i, f)
            final = col == n - 1 and not mov
            if d < 16:  # pop-up pulando na tela
                s = mola(d, 8, 0.5, 220)
                voando.append((L['pop'], L['pos'][0], L['pos'][1], 0.3 + 0.7 * s, clamp01(d / 3), (1 - s) * 10 * (1 if i % 2 else -1), d, L))
                continue
            if d < 26:  # voando até a coluna
                q = sai((d - 16) / 10)
                tx, ty = self.cx[L['col']], 580 + len([1 for j in range(i) if self.leads[j]['col'] == L['col'] and self.coluna(j, f)[0] == L['col']]) * 104
                x = L['pos'][0] + (tx - L['pos'][0]) * q
                y = L['pos'][1] + (ty - L['pos'][1]) * q - math.sin(q * math.pi) * 120
                esc = 1 + ((self.cw - 16) / L['pop'].width - 1) * q
                voando.append((L['pop'] if q < 0.6 else L['card'], x, y, esc if q < 0.6 else 1, 1, 0, None, L))
                L['x'], L['y'] = tx, ty
                continue
            if mov:
                t, c0, c1 = mov
                q = sai((f - t) / 12)
                x0, y0 = L['x'], L['y']
                x1 = self.cx[c1]
                y1 = 580 + len(em[c1]) * 104
                x, y = x0 + (x1 - x0) * q, y0 + (y1 - y0) * q - math.sin(q * math.pi) * 90
                for k in (3, 2, 1):  # rastro
                    qq = sai((f - t - k) / 12)
                    colar(base, neon(LIME, 7), x0 + (x1 - x0) * qq, y0 + (y1 - y0) * qq - math.sin(qq * math.pi) * 90, alpha=0.25 * k)
                voando.append((L['card'], x, y, 1.08, 1, (1 - q) * 4, None, L))
                continue
            tx, ty = alvo.get(i, (L['x'], L['y']))
            L['x'] = tx if L['x'] is None else L['x'] + (tx - L['x']) * 0.35
            L['y'] = ty if L['y'] is None else L['y'] + (ty - L['y']) * 0.35
            colar(base, L['ok'] if final else L['card'], L['x'], L['y'])
            if final:
                ch = max(t + 12 for j, t, c0, c1 in self.movs if j == i) if any(j == i for j, *_ in self.movs) else L['a'] + 26
                explosao(base, L['x'], L['y'], f - ch, i, LIME, 12, 160, 18)
        for sp, x, y, esc, a, rot, d, L in voando:
            colar(base, sp, x, y, esc, a, rot)
            if d is not None:
                onda(base, x - sp.width * esc / 2 + 90, y, d, LIME)
        if self.total:
            ganho = 0
            for i, L in enumerate(self.leads):
                col, mov = self.coluna(i, f)
                if col == n - 1 and not mov:
                    ganho += L['num']
            if ganho:
                self._ganho = getattr(self, '_ganho', 0)
                self._ganho += (ganho - self._ganho) * 0.3
                if abs(ganho - self._ganho) < 8:
                    self._ganho = ganho
                txt = limpa(self.total).replace('{valor}', 'R$ ' + moeda(self._ganho))
                colar(base, _linha_total(txt), W / 2, 1310)


@lru_cache(maxsize=256)
def _linha_total(txt):
    t = Texto(txt, 50, 'black', max_w=980)
    im = Image.new('RGBA', (1060, int(t.alt + 60)), (0, 0, 0, 0))
    t.draw(im, 530, im.height / 2, 99, 0, 'fixo')
    return im


@lru_cache(maxsize=128)
def notificacao(nome, proc, titulo):
    w, h = 720, 132
    im = cartao(w, h, 30, (30, 40, 58, 252), (198, 255, 61, 90), 30, 2, LIME).copy()
    pad = (im.width - w) // 2
    colar(im, neon(LIME, 9), pad + 56, pad + h / 2)
    colar(im, rotulo(titulo, 20, LIME, 4), pad + 100, pad + 20, canto=True)
    colar(im, palavra(limpa(nome), 40, 'bold', TXT, False, False), pad + 92, pad + 38, canto=True)
    if proc:
        x = pad + 100 + _fonte('bold', 40).getlength(limpa(nome)) + 20
        colar(im, palavra('· ' + limpa(proc), 30, 'med', MUTED, False, False), x - 8, pad + 48, canto=True)
    colar(im, palavra('agora', 22, 'med', MUTED, False, False), pad + w - 100, pad + 14, canto=True)
    return im


@lru_cache(maxsize=128)
def cartao_lead(nome, proc, valor, w, ok):
    h = 92
    im = cartao(w, h, 18, (34, 44, 62, 250) if not ok else (30, 48, 26, 250), (198, 255, 61, 160) if ok else (255, 255, 255, 30), 16, 2, LIME if ok else None).copy()
    pad = (im.width - w) // 2
    tam = 26 if w > 200 else 22
    colar(im, palavra(limpa(nome), tam, 'bold', TXT, False, False), pad + 10, pad + 4, canto=True)
    if proc:
        colar(im, palavra(limpa(proc), tam - 6, 'med', MUTED, False, False), pad + 10, pad + 38, canto=True)
    if valor:
        sv = palavra(limpa(valor), tam - 6, 'xbold', LIME, False, False)
        colar(im, sv, pad + w - sv.width + 4, pad + 38, canto=True)
    if ok:
        d = ImageDraw.Draw(im)
        cx, cy = pad + w - 22, pad + 22
        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=LIME + (255,))
        d.line([(cx - 6, cy), (cx - 1, cy + 5), (cx + 7, cy - 5)], fill=BG + (255,), width=3)
    return im


class Timeline(Cena):
    dur_padrao = 5.4

    def __init__(self, *a):
        super().__init__(*a)
        c = self.c
        self.passos = c['passos']
        n = len(self.passos)
        self.y0 = 450
        self.step = min(210, 640 / max(1, n - 1)) if n > 1 else 200
        self.t = [10 + i * 20 for i in range(n)]
        self.rots = [rotulo(f"{p['quando']} · {p.get('rotulo', 'envio automático')}", 22, LIME, 4) for p in self.passos]
        self.cards = [balao_card(p['texto']) for p in self.passos]
        for t in self.t:
            self.som(t, 'pop', 0.7)
            self.som(t + 4, 'whoosh', 0.25)
        self.tr = None
        if c.get('resposta'):
            self.tr = self.t[-1] + 26
            self.resp = balao(c['resposta'], 'ela', c.get('meta_resposta', 'agora'))
            self.notif = notificacao(c.get('nome', 'Paciente'), 'respondeu', 'Nova mensagem')
            self.som(self.tr, 'ding', 0.8)
            self.tremer(self.tr, 0.5)

    def draw(self, base, f):
        x = 150
        ys = [self.y0 + i * self.step for i in range(len(self.passos))]
        fim = ys[-1] + 60
        # linha desenhada
        prog = 0
        for i, t in enumerate(self.t):
            if f >= t - 10:
                prog = ys[i] if f >= t else ys[i - 1] + (ys[i] - ys[i - 1]) * sai((f - t + 10) / 10) if i else self.y0 - 40 + 40 * sai((f - t + 10) / 10)
        if self.tr and f >= self.tr - 10:
            prog = ys[-1] + (fim + 40 - ys[-1]) * sai((f - self.tr + 10) / 10)
        if prog > self.y0 - 40:
            traco(base, [(x, self.y0 - 40), (x, prog)], 1, LIME, 6, ponta=True)
        for i, (y, t) in enumerate(zip(ys, self.t)):
            d = f - t
            if d < 0:
                continue
            s = mola(d, 9, 0.5, 220)
            colar(base, neon(LIME, 22), x, y, 0.4 + 0.6 * s)
            if d > 4:
                traco(base, forma('check', x - 12, y - 10, x + 12, y + 10), sai((d - 4) / 6), BG, 5, ponta=False, glow=False)
            q = sai((d - 2) / 10)
            colar(base, self.rots[i], 210 + (1 - q) * 200, y - 52, alpha=q, canto=True)
            colar(base, self.cards[i], 210 + (1 - q) * 300, y - 18, alpha=q, canto=True)
            onda(base, x, y, d, LIME)
        if self.tr and f >= self.tr:
            d = f - self.tr
            s = mola(d, 9, 0.5, 220)
            yb = fim + 50
            colar(base, self.resp, 120 + self.resp.width / 2, yb + self.resp.height / 2, 0.5 + 0.5 * s, clamp01(d / 3))
            explosao(base, 120 + self.resp.width, yb, d, 77, LIME)
            # notificação que cai do topo e volta
            q = sai(d / 8) if d < 34 else 1 - sai((d - 34) / 8)
            colar(base, self.notif, W / 2, 300 + (q - 1) * 260, 0.9, q)


@lru_cache(maxsize=64)
def balao_card(texto):
    sp = texto_simples('"' + limpa(texto) + '"', 32, 'semi', TXT, 700)
    w, h = sp.width + 44, sp.height + 30
    im = cartao(w, h, 22, (28, 38, 54, 248), (198, 255, 61, 70), 16).copy()
    pad = (im.width - w) // 2
    colar(im, sp, pad + 22, pad + 16, canto=True)
    out = im.crop((pad - 6, pad - 6, im.width - pad + 6, im.height - pad + 22))
    return out


class Numero(Cena):
    dur_padrao = 3.2

    def __init__(self, *a):
        super().__init__(*a)
        c = self.c
        self.cor = CORES.get(c.get('cor', 'lime'), LIME)
        self.rot = rotulo(c['rotulo'], 30, self.cor) if c.get('rotulo') else None
        self.sub = Texto(c['sub'], 52, max_w=900) if c.get('sub') else None
        self.de, self.ate = c.get('de', 0), c['ate']
        for k in range(0, 30, 3):
            self.som(6 + k, 'tick', 0.6)
        self.som(36, 'slam', 0.7)
        self.tremer(36, 0.6)
        if c.get('riscar'):
            self.som(52, 'risco')

    def draw(self, base, f):
        cy = 880
        if self.rot:
            p = sai(f / 8)
            colar(base, self.rot, W / 2, cy - 260 - (1 - p) * 30, alpha=p)
        q = sai((f - 6) / 30)
        v = self.de + (self.ate - self.de) * q
        txt = self.c.get('prefixo', '') + (moeda(v) if self.ate >= 1000 else str(int(round(v)))) + self.c.get('sufixo', '')
        tam = 260 if len(txt) <= 4 else 200 if len(txt) <= 7 else 150
        sp = palavra(txt, tam, 'black', self.cor if self.c.get('numero_colorido') else TXT, self.c.get('numero_colorido', False))
        bate = mola(f - 36, 8, 0.5, 260) if f >= 36 else 1
        colar(base, sp, W / 2, cy, 1 + (1 - bate) * 0.25 if f >= 36 else 0.9 + 0.1 * q, clamp01(f / 4))
        # anel sendo desenhado em volta
        r = 360
        pts = [(W / 2 + math.cos(-math.pi / 2 + a / 60 * math.pi * 2) * r, cy + math.sin(-math.pi / 2 + a / 60 * math.pi * 2) * r * 0.62) for a in range(61)]
        traco(base, pts, q, self.cor, 6)
        explosao(base, W / 2, cy, f - 36, 31, self.cor)
        if self.c.get('riscar') and f >= 52:
            traco(base, [(W / 2 - sp.width / 2 + 40, cy + 10), (W / 2 + sp.width / 2 - 40, cy - 20)], sai((f - 52) / 8), VERMELHO, 14)
        if self.sub:
            self.sub.draw(base, W / 2, cy + 300, f, 40, 'pop', 3)


class Desenho(Cena):
    dur_padrao = 4.2

    def __init__(self, *a):
        super().__init__(*a)
        self.prep_texto_topo()
        c = self.c
        self.forma = c.get('forma', 'funil')
        self.som(10, 'risco')
        if self.forma == 'funil':
            self.n = c.get('bolinhas', 12)
            self.vaza = c.get('vazando', 0)
            self.bolas = [(30 + i * 4, 230 + rnd('bx', i) * 620, rnd('bv', i) < self.vaza) for i in range(self.n)]
            for s, x, v in self.bolas:
                if not v:
                    self.som(s + 26, 'pop', 0.3)
            self.pilula_txt = c.get('rotulo_saida', 'agendados')
        else:
            self.vals = c.get('pontos', [10, 14, 12, 20, 26, 24, 38])
            for k in range(len(self.vals)):
                self.som(18 + k * 5, 'tick', 0.7)
            self.t_fim = 18 + len(self.vals) * 5
            self.som(self.t_fim, 'slam', 0.6)
            self.tremer(self.t_fim, 0.5)
            self.valor = Texto(c.get('valor', '+38%'), 120, max_w=600, dest=LIME, cor=LIME)

    def draw(self, base, f):
        self.texto_topo(base, f)
        if self.forma == 'funil':
            x0, y0, x1, y1 = 180, 640, 900, 1140
            cx = (x0 + x1) / 2
            traco(base, forma('funil', x0, y0, x1, y1), sai((f - 6) / 22), LIME, 9)
            cont = 0
            for i, (s, bx, vaza) in enumerate(self.bolas):
                t = f - s
                if t < 0:
                    continue
                y = y0 - 70 + 0.5 * 2.1 * t * t
                hw0 = (x1 - x0) / 2
                ymid = y0 + (y1 - y0) * 0.72
                hw = hw0 - (hw0 - 72) * clamp01((y - y0) / (ymid - y0))
                x = cx + (bx - cx) * min(1, hw / hw0) * 0.85
                cor = [LIME, CIANO, ROSA][i % 3]
                if vaza and y > y0 + 170:
                    tv = (y - y0 - 170) / 9
                    lado = -1 if bx < cx else 1
                    x = cx + lado * (hw0 * 0.75 + tv * 8)
                    cor = VERMELHO
                    if y > H + 40:
                        continue
                elif y > y1 + 50:
                    cont += 1
                    continue
                colar(base, neon(cor, 9), x, y)
            if any(v for _, _, v in self.bolas):
                pisca = 0.3 + 0.7 * (math.sin(f / 3) > 0)
                colar(base, rotulo(self.c.get('rotulo_vazamento', 'vazando'), 26, VERMELHO), 120, 860, alpha=pisca, canto=True)
                colar(base, rotulo(self.c.get('rotulo_vazamento', 'vazando'), 26, VERMELHO), 800, 860, alpha=pisca, canto=True)
            sp = _pilula_saida(cont, self.pilula_txt)
            colar(base, sp, cx, y1 + 110, mola(f - 30, 9, 0.5, 220) if f >= 30 else 0)
        else:
            x0, y0, x1, y1 = 150, 660, 930, 1160
            traco(base, [(x0, y0), (x0, y1), (x1, y1)], sai((f - 4) / 12), (90, 100, 120), 5, ponta=False)
            mn, mx = min(self.vals), max(self.vals)
            pts = [(x0 + 40 + (x1 - x0 - 80) * k / (len(self.vals) - 1), y1 - 40 - (y1 - y0 - 120) * (v - mn) / max(1, mx - mn)) for k, v in enumerate(self.vals)]
            q = clamp01((f - 18) / (len(self.vals) * 5))
            traco(base, pts, q, LIME, 9)
            for k, (x, y) in enumerate(pts):
                d = f - 18 - k * 5 - 4
                if d >= 0:
                    colar(base, neon(LIME, 9), x, y, 0.5 + 0.5 * mola(d, 9, 0.5, 220))
            d = f - self.t_fim
            explosao(base, pts[-1][0], pts[-1][1], d, 9)
            if d >= 0:
                self.valor.draw(base, pts[-1][0] - 170, pts[-1][1] + 130, f, self.t_fim, 'slam', 3)


@lru_cache(maxsize=64)
def _pilula_saida(n, txt):
    t = f'{n} {limpa(txt).upper()}'
    f = _fonte('black', 44)
    w = int(f.getlength(t)) + 70
    im = cartao(w, 90, 45, (198, 255, 61, 255), None, 20, 0, LIME).copy()
    pad = (im.width - w) // 2
    ImageDraw.Draw(im).text((pad + 35, pad + 18), t, font=f, fill=BG + (255,))
    return im


class Lista(Cena):
    dur_padrao = 4.6

    def __init__(self, *a):
        super().__init__(*a)
        self.prep_texto_topo()
        self.itens = self.c['itens']
        self.sps = [texto_simples(i['t'], 40, 'semi', TXT, 700) for i in self.itens]
        for k, it in enumerate(self.itens):
            self.som(14 + k * 12, 'whoosh', 0.25)
            self.som(22 + k * 12, 'check' if it.get('ok', True) else 'pop', 0.7)
            if not it.get('ok', True):
                self.tremer(22 + k * 12, 0.25)

    def draw(self, base, f):
        self.texto_topo(base, f)
        top = 470 + (self.tt.alt if self.tt else 0) + 70
        alts = [max(130, sp.height + 54) for sp in self.sps]
        folga = max(24, min(60, (1340 - top - sum(alts)) / max(1, len(alts))))
        for k, (it, sp) in enumerate(zip(self.itens, self.sps)):
            d = f - 14 - k * 12
            if d < 0:
                continue
            q = sai(d / 9)
            h = alts[k]
            y = top + sum(alts[:k]) + folga * k + h / 2
            x = W / 2 - (1 - q) * 500
            ok = it.get('ok', True)
            colar(base, cartao(920, h, 24, (24, 32, 46, 240), (255, 255, 255, 30), 20), x, y, alpha=q)
            bx = x - 460 + 60
            colar(base, cartao(56, 56, 14, (12, 16, 24, 255), ((198, 255, 61, 200) if ok else (255, 92, 92, 200)), 0, 3), bx, y, alpha=q)
            colar(base, sp, bx + 52, y - sp.height / 2, alpha=q, canto=True)
            if d >= 8:
                cor = LIME if ok else VERMELHO
                traco(base, forma('check' if ok else 'x', bx - 15, y - 13, bx + 15, y + 13), sai((d - 8) / 6), cor, 7, ponta=False)


class Cta(Cena):
    dur_padrao = 4.6

    def __init__(self, *a):
        super().__init__(*a)
        self.prep_texto_topo()
        c = self.c
        self.modo = c.get('modo', 'direct')
        self.pal = limpa(c.get('palavra', 'FUNIL')).upper()
        self.t_dig = 24
        if self.modo in ('direct', 'comenta'):
            for k in range(len(self.pal)):
                self.som(self.t_dig + k * 4, 'tick', 0.8)
            self.t_env = self.t_dig + len(self.pal) * 4 + 8
            self.som(self.t_env, 'whoosh', 0.5)
            self.som(self.t_env + 3, 'pop', 0.7)
            self.som(self.t_env + 26, 'ding', 0.7)
            self.resp = balao(c.get('resposta', 'Opa! Te mandei o kit aqui. Você tem clínica?'), 'ela', 'agora')
            self.minha = balao(self.pal, 'eu', 'agora')
        else:
            self.t_toque = 34
            self.som(self.t_toque, 'pop', 0.8)
            self.som(self.t_toque + 8, 'ding', 0.8)
            self.tremer(self.t_toque + 8, 0.4)
        self.som(8, 'risco')

    def draw(self, base, f):
        self.texto_topo(base, f)
        getattr(self, 'd_' + self.modo)(base, f)

    def d_direct(self, base, f):
        X0, Y0, X1, Y1 = 90, 660, 990, 1290
        p = sai(f / 10)
        colar(base, cartao(X1 - X0, Y1 - Y0, 36, (17, 23, 33, 245)), W / 2, (Y0 + Y1) / 2 + (1 - p) * 120, alpha=p)
        colar(base, avatar('C', LIME, 34), X0 + 64, Y0 + 60, alpha=p)
        colar(base, palavra('crmquevende', 34, 'bold', TXT, False, False), X0 + 112, Y0 + 24, alpha=p, canto=True)
        colar(base, palavra('responde em minutos', 22, 'med', MUTED, False, False), X0 + 112, Y0 + 64, alpha=p, canto=True)
        # campo de mensagem
        iy = Y1 - 70
        colar(base, cartao(700, 76, 38, (34, 44, 62, 255), (255, 255, 255, 40), 0), X0 + 30 + 350, iy, alpha=p)
        k = int(clamp01((f - self.t_dig) / (len(self.pal) * 4)) * len(self.pal)) if f < self.t_env else 0
        txt = self.pal[:k] if f >= self.t_dig else ''
        cursor = '|' if (f // 8) % 2 == 0 and f < self.t_env else ''
        if txt or cursor:
            colar(base, palavra(txt + cursor, 36, 'bold', TXT, False, False), X0 + 60, iy - 32, canto=True)
        elif f < self.t_dig or f >= self.t_env:
            colar(base, palavra('Mensagem...', 32, 'med', MUTED, False, False), X0 + 60, iy - 28, alpha=p, canto=True)
        bx = X1 - 80
        pulso = 1 + 0.08 * math.sin(f / 3)
        colar(base, neon(LIME, 30), bx, iy, pulso, p)
        traco(base, [(bx - 12, iy + 10), (bx + 12, iy), (bx - 12, iy - 10)], 1, BG, 5, ponta=False, glow=False)
        onda(base, bx, iy, f - self.t_env, LIME)
        traco(base, forma('seta', 1000, 560, X0 + 400, iy - 60), sai((f - 8) / 14), LIME, 8)
        if f >= self.t_env:
            d = f - self.t_env
            s = mola(d, 10, 0.5, 220)
            yb = Y0 + 200 + (1 - s) * 300
            colar(base, self.minha, X1 - 40 - self.minha.width / 2, yb, 0.5 + 0.5 * s, clamp01(d / 3))
            if 10 <= d < 26:
                sp = digitando(f)
                colar(base, sp, X0 + 40 + sp.width / 2, Y0 + 330)
            if d >= 26:
                s2 = mola(d - 26, 10, 0.5, 220)
                colar(base, self.resp, X0 + 40 + self.resp.width / 2, Y0 + 340, 0.5 + 0.5 * s2, clamp01((d - 26) / 3))
                explosao(base, X0 + 40 + self.resp.width, Y0 + 300, d - 26, 5)

    def d_comenta(self, base, f):
        X0, Y0, X1, Y1 = 120, 650, 960, 1300
        p = sai(f / 10)
        colar(base, cartao(X1 - X0, Y1 - Y0, 32, (17, 23, 33, 245)), W / 2, (Y0 + Y1) / 2 + (1 - p) * 120, alpha=p)
        colar(base, _post_mini(), W / 2, Y0 + 210, alpha=p)
        # coração pulsando
        hx, hy = X0 + 60, Y0 + 450
        bat = 1 + 0.15 * max(0, math.sin(f / 4)) if f < self.t_env else 1 + 0.35 * (1 - sai((f - self.t_env) / 10))
        colar(base, _coracao(ROSA if f >= self.t_env else TXT), hx, hy, bat, p)
        colar(base, palavra('comentários', 28, 'bold', TXT, False, False), hx + 50, hy - 20, alpha=p, canto=True)
        iy = Y1 - 64
        colar(base, cartao(740, 70, 35, (34, 44, 62, 255), (255, 255, 255, 40), 0), W / 2, iy, alpha=p)
        k = int(clamp01((f - self.t_dig) / (len(self.pal) * 4)) * len(self.pal)) if f < self.t_env else 0
        cursor = '|' if (f // 8) % 2 == 0 and f < self.t_env else ''
        txt = (self.pal[:k] if f >= self.t_dig else '') + cursor
        if txt.strip('|') or cursor:
            colar(base, palavra(txt, 34, 'bold', TXT, False, False), X0 + 70, iy - 30, canto=True)
        traco(base, forma('seta', 1010, 560, X0 + 360, iy - 50), sai((f - 8) / 14), LIME, 8)
        if f >= self.t_env:
            d = f - self.t_env
            s = mola(d, 10, 0.5, 220)
            y = Y0 + 530
            colar(base, avatar('V', CIANO, 26), X0 + 70, y, 0.5 + 0.5 * s, clamp01(d / 3))
            colar(base, palavra('você  ' + self.pal, 32, 'bold', TXT, False, False), X0 + 110, y - 22, alpha=clamp01(d / 3), canto=True)
            explosao(base, hx, hy, d, 41, ROSA, 16, 200)
            if d >= 26:
                q = sai((d - 26) / 8)
                colar(base, rotulo(self.c.get('resposta_curta', 'te chamei no direct'), 22, LIME, 4), X0 + 112, y + 26, alpha=q, canto=True)

    def d_bio(self, base, f):
        X0, Y0, X1, Y1 = 90, 640, 990, 1270
        p = sai(f / 10)
        colar(base, cartao(X1 - X0, Y1 - Y0, 36, (17, 23, 33, 245)), W / 2, (Y0 + Y1) / 2 + (1 - p) * 120, alpha=p)
        ax, ay = X0 + 110, Y0 + 120
        for k in range(24):  # anel girando em volta da foto
            a = k / 24 * math.pi * 2 + f / 10
            cor = [LIME, CIANO, ROSA][k % 3]
            colar(base, neon(cor, 4), ax + math.cos(a) * 82, ay + math.sin(a) * 82, alpha=p * (0.4 + 0.6 * ((k + f // 2) % 3 == 0)))
        colar(base, avatar('C', LIME, 66), ax, ay, alpha=p)
        colar(base, palavra('@crmquevende', 40, 'bold', TXT, False, False), X0 + 220, Y0 + 70, alpha=p, canto=True)
        colar(base, palavra('CRM que vende | Follow-up para clínicas', 24, 'med', MUTED, False, False), X0 + 220, Y0 + 124, alpha=p, canto=True)
        colar(base, texto_simples('Nenhum orçamento esquecido.\nSeu WhatsApp chama de volta toda paciente que disse "vou pensar".', 30, 'semi', TXT, 800),
              X0 + 50, Y0 + 240, alpha=p, canto=True)
        ly = Y0 + 430
        link = palavra('wa.me/5581985704921', 34, 'bold', CIANO, False, False)
        colar(base, link, X0 + 50, ly - 26, alpha=p, canto=True)
        traco(base, forma('seta', 1010, 560, X0 + 260, ly - 40), sai((f - 8) / 14), LIME, 8)
        if f >= 18 and f < self.t_toque + 4:
            traco(base, forma('sublinha', X0 + 50, ly - 26, X0 + 50 + link.width, ly + 10), sai((f - 18) / 10), LIME, 6, ponta=False)
        onda(base, X0 + 250, ly, f - self.t_toque, CIANO)
        d = f - self.t_toque - 8
        if d >= 0:
            s = mola(d, 9, 0.5, 220)
            colar(base, _cartao_wpp(self.c.get('mensagem_wpp', 'Quero o raio-x dos meus orçamentos parados')), W / 2, 1180 + (1 - s) * 200, 0.6 + 0.4 * s, clamp01(d / 3))
            explosao(base, W / 2, 1150, d, 13, VERDE_WPP)


@lru_cache(maxsize=8)
def _cartao_wpp(msg):
    w, h = 860, 150
    im = cartao(w, h, 30, (18, 38, 28, 252), (37, 211, 102, 160), 30, 2, VERDE_WPP).copy()
    pad = (im.width - w) // 2
    d = ImageDraw.Draw(im)
    d.ellipse([pad + 26, pad + 35, pad + 106, pad + 115], fill=VERDE_WPP + (255,))
    d.rounded_rectangle([pad + 48, pad + 56, pad + 84, pad + 92], 8, outline=(255, 255, 255, 255), width=5)
    colar(im, rotulo('WhatsApp · agora', 20, VERDE_WPP, 3), pad + 130, pad + 28, canto=True)
    colar(im, texto_simples(msg, 32, 'bold', TXT, 680), pad + 130, pad + 62, canto=True)
    return im


@lru_cache(maxsize=4)
def _post_mini():
    w, h = 760, 360
    y, x = np.mgrid[0:h, 0:w]
    t = (x / w * 0.6 + y / h * 0.4)[..., None]
    arr = np.array([30, 50, 20], np.float32) * (1 - t) + np.array([12, 60, 72], np.float32) * t
    im = Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 24, fill=255)
    im.putalpha(m)
    t_ = Texto('Seu orçamento <volta>?', 64, max_w=640)
    t_.draw(im, w / 2, h / 2, 99, 0, 'fixo')
    return im


@lru_cache(maxsize=8)
def _coracao(cor):
    s = 64
    m = Image.new('L', (s, s), 0)
    pts = [(s / 2 + 16 * math.sin(t) ** 3 * 1.7, s / 2 - (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) * 1.7)
           for t in np.linspace(0, 2 * math.pi, 60)]
    ImageDraw.Draw(m).polygon(pts, fill=255)
    im = Image.new('RGBA', (s, s), cor + (0,))
    im.putalpha(m)
    return im


class Data(Cena):
    dur_padrao = 3.4

    def __init__(self, *a):
        super().__init__(*a)
        c = self.c
        self.cal = _calendario(str(c['dia']), limpa(c['mes']).upper())
        self.titulo = Texto(c['titulo'], c.get('tam', 96), max_w=960)
        self.sub = Texto(c['sub'], 46, 'bold', max_w=900, upper=False) if c.get('sub') else None
        self.som(4, 'whoosh', 0.6)
        self.som(14, 'slam')
        self.tremer(14, 1)
        for i in range(self.titulo.n):
            self.som(22 + i * 4, 'pop', 0.5)

    def draw(self, base, f):
        cy = 760
        s = mola(f - 4, 9, 0.6, 200) if f >= 4 else 0
        if s > 0.02:
            cal = self.cal.resize((self.cal.width, max(1, int(self.cal.height * min(1.2, s)))), Image.BILINEAR)
            colar(base, cal, W / 2, cy - self.cal.height / 2 + cal.height / 2, 1, clamp01(s * 2), (1 - min(1, s)) * -12)
        explosao(base, W / 2, cy, f - 14, 3, LIME, 26, 420, 26)
        for k in range(10):  # confete neon caindo
            d = f - 14 - k * 2
            if d > 0:
                colar(base, neon([LIME, CIANO, ROSA][k % 3], 5), 100 + rnd('cf', k) * 880, 380 + d * (7 + k % 4) + math.sin(d / 4 + k) * 20, alpha=clamp01(1 - d / 70))
        self.titulo.draw(base, W / 2, cy + 330 + self.titulo.alt / 2, f, 22, 'slam', 4)
        if self.sub:
            self.sub.draw(base, W / 2, cy + 400 + self.titulo.alt + self.sub.alt / 2, f, 34 + self.titulo.n * 4, 'pop', 2)


@lru_cache(maxsize=8)
def _calendario(dia, mes):
    w, h = 470, 500
    im = cartao(w, h, 34, (236, 236, 228, 255), None, 40, 0, LIME).copy()
    pad = (im.width - w) // 2
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([pad, pad, pad + w, pad + 120], 34, fill=LIME + (255,))
    d.rectangle([pad, pad + 80, pad + w, pad + 120], fill=LIME + (255,))
    fm = _fonte('black', 64)
    d.text((pad + w / 2 - fm.getlength(mes) / 2, pad + 22), mes, font=fm, fill=BG + (255,))
    fd = _fonte('black', 250)
    asc, desc = fd.getmetrics()
    d.text((pad + w / 2 - fd.getlength(dia) / 2, pad + 120 + (h - 120) / 2 - (asc + desc) / 2 + 8), dia, font=fd, fill=BG + (255,))
    for x in (pad + 110, pad + w - 110):
        d.ellipse([x - 16, pad - 16, x + 16, pad + 16], fill=(60, 70, 80, 255))
    return im


class Virada(Cena):
    """Virada da dor para a solução: riser, flash branco, halo e fundo passando de vermelho para lime, pergunta batendo."""
    dur_padrao = 2.2

    def __init__(self, *a):
        super().__init__(*a)
        self.t = Texto(self.c['texto'], self.c.get('tam', 104), max_w=940)
        self.som(-24, 'riser', 0.9)
        self.som(2, 'slam', 1)
        self.tremer(2, 0.8)
        for i in range(self.t.n):
            self.som(8 + i * 3, 'pop', 0.4)

    def draw(self, base, f):
        q = sai(f / 10)
        colar(base, anel(LIME, int(260 + 140 * q), 10), W / 2, 900, 1 + 0.03 * math.sin(f / 3), 0.5 + 0.5 * q)
        explosao(base, W / 2, 900, f - 2, 61, LIME, 28, 480, 26)
        self.t.draw(base, W / 2, 900, f, 8, 'slam', 3)


TIPOS = {'gancho': Gancho, 'chat': Chat, 'leads': Leads, 'timeline': Timeline, 'numero': Numero,
         'desenho': Desenho, 'lista': Lista, 'cta': Cta, 'data': Data, 'virada': Virada}
MOVS = ['push', 'esq', 'pull', 'gira', 'dir', 'push2']
HUMOR = {'gancho': 'dor', 'chat': 'dor', 'numero': 'dor', 'data': 'solucao', 'leads': 'solucao', 'timeline': 'solucao',
         'lista': 'solucao', 'cta': 'solucao', 'desenho': 'solucao', 'virada': 'solucao'}


def _tinta(cor):
    y, x = np.mgrid[0:H // 4, 0:W // 4]
    d = np.sqrt(((x - W / 8) / (W / 4 * 0.7)) ** 2 + ((y - H / 8) / (H / 4 * 0.45)) ** 2)
    a = Image.fromarray((np.clip(1 - d, 0, 1) * 70).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    im = Image.new('RGBA', (W, H), cor + (0,))
    im.putalpha(a)
    return im


TINTA = {'dor': _tinta(VERMELHO), 'solucao': _tinta(LIME)}
TRANS = ['whip', 'zoom', 'glitch']


# ---------- câmera e transições ----------
def camera(img, z, rot, px, py):
    th = math.radians(rot)
    co, si = math.cos(th), math.sin(th)
    cx, cy = W / 2, H / 2
    a, b = co / z, si / z
    d, e = -si / z, co / z
    c = cx - (a * cx + b * cy) - px
    f = cy - (d * cx + e * cy) - py
    return img.transform((W, H), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BILINEAR, fillcolor=BG)


def mov_cena(nome, p):
    e = p * p * (3 - 2 * p)
    return {'push': (1 + 0.10 * e, 0, 0, 0), 'pull': (1.13 - 0.11 * e, 0, 0, 0), 'esq': (1.07, 0, 45 - 90 * e, 0),
            'dir': (1.07, 0, -45 + 90 * e, 0), 'gira': (1.08, -1.8 + 3.6 * e, 0, 0), 'push2': (1.02 + 0.13 * e, 0, 0, 25 - 50 * e)}[nome]


def glitch(img, forca, semente):
    arr = np.asarray(img).copy()
    s = int(28 * forca)
    arr[..., 0] = np.roll(arr[..., 0], s, 1)
    arr[..., 2] = np.roll(arr[..., 2], -s, 1)
    for k in range(7):
        y0 = int(rnd('gy', semente, k) * H)
        h = int(20 + rnd('gh', semente, k) * 120)
        arr[y0:y0 + h] = np.roll(arr[y0:y0 + h], int((rnd('gx', semente, k) - 0.5) * 160 * forca), 1)
    return Image.fromarray(arr)


@lru_cache(maxsize=4)
def tarja_sprite(txt):
    t = Texto(txt, 44, 'black', max_w=860, brilho=False)
    w, h = 960, int(t.alt + 50)
    im = cartao(w, h, 26, (14, 26, 43, 248), (255, 255, 255, 30), 30).copy()
    t.draw(im, im.width / 2, im.height / 2 - 6, 99, 0, 'fixo')
    return im


def main():
    rot_, saida = sys.argv[1], sys.argv[2]
    r = json.load(open(rot_, encoding='utf-8'))
    ev, cenas, t0 = [], [], 0
    for i, c in enumerate(r['cenas']):
        cena = TIPOS[c['tipo']](c, t0, ev, i)
        cena.mov = c.get('camera', MOVS[i % len(MOVS)])
        cena.trans = c.get('transicao', TRANS[i % len(TRANS)])
        cena.leg = Texto(c['legenda'], 56, max_w=900) if c.get('legenda') else None
        cena.humor = c.get('humor') or ('dor' if c['tipo'] == 'desenho' and c.get('vazando') else HUMOR[c['tipo']])
        if c['tipo'] == 'virada':
            cena.trans = 'zoom'
        if i:
            ev.append((t0 - 3, 'whoosh', 0.6))
            if cena.trans == 'glitch':
                ev.append((t0 - 4, 'glitch', 0.8))
        cenas.append(cena)
        t0 += cena.dur
    total = t0
    semente = r.get('semente', 1)
    tarja = tarja_sprite(r['tarja']) if r.get('tarja') else None
    marca = rotulo('@crmquevende', 24, MUTED, 4)
    # áudio
    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, 'a.wav')
    mix = som.trilha(total / FPS + 0.5, semente)
    mix = np.stack([mix, mix], 1)
    for F, nome, g in ev:
        sfx = som.efeito(nome, F)
        k = int(F / FPS * som.SR)
        if 0 <= k < len(mix):
            sfx = sfx[:len(mix) - k]
            mix[k:k + len(sfx)] += (sfx * g)[:, None]
    mix = np.tanh(mix * 1.1) * 0.9
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ac', '2', '-ar', str(som.SR), '-i', '-', wav],
                   input=(mix * 32767).astype(np.int16).tobytes(), check=True)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                            '-movflags', '+faststart', '-shortest', saida], stdin=subprocess.PIPE)
    for i, cena in enumerate(cenas):
        prox = cenas[i + 1].trans if i + 1 < len(cenas) else None
        for f in range(cena.dur):
            F = cena.t0 + f
            base = fundo(F)
            base.alpha_composite(TINTA[cena.humor])
            # halo: anel de luz recorrente, vermelho na dor e lime na solução
            if cena.c['tipo'] != 'virada':
                colar(base, anel(VERMELHO if cena.humor == 'dor' else LIME, 430, 8), W / 2, 900, 1 + 0.02 * math.sin(F / 9), 0.16 + 0.06 * math.sin(F / 7))
            cena.draw(base, f)
            img = base.convert('RGB')
            z, rot, px, py = mov_cena(cena.mov, f / max(1, cena.dur - 1))
            px += math.sin(F / 23) * 6
            py += math.cos(F / 31) * 6
            for ft, forca in cena.trem:
                d = f - ft
                if 0 <= d < 12:
                    amp = forca * 28 * math.exp(-d / 3.5)
                    px += (rnd('cx', F) - 0.5) * 2 * amp
                    py += (rnd('cy', F) - 0.5) * 2 * amp
                    rot += (rnd('cr', F) - 0.5) * amp * 0.06
            flash, gl, borrao = 0, 0, 0
            if f < TR and i > 0:
                q = f / TR
                if cena.trans == 'whip':
                    px += (1 - q) ** 2 * 900; borrao = 2 * (1 - q) * 900 / TR
                elif cena.trans == 'zoom':
                    z *= 1 + (1 - q) ** 2 * 0.6; flash = (1 - q) * 0.9 if cena.c['tipo'] == 'virada' else (1 - q) ** 2 * 0.35
                else:
                    gl = 1 - q
            if prox and f >= cena.dur - TR:
                q = (f - (cena.dur - TR) + 1) / TR
                if prox == 'whip':
                    px -= q * q * 900; borrao = 2 * q * 900 / TR
                elif prox == 'zoom':
                    z *= 1 + q * q * 0.9; flash = max(flash, q ** 4 * 0.55)
                else:
                    gl = max(gl, q)
            if borrao > 20:
                amostras = [camera(img, z, rot, px + k * borrao / 3, py) for k in (-1, 0, 1)]
                img = Image.blend(Image.blend(amostras[0], amostras[2], 0.5), amostras[1], 0.4)
            else:
                img = camera(img, z, rot, px, py)
            if gl > 0.05:
                img = glitch(img, gl, F)
            img = Image.composite(PRETO, img, VIN)
            top = img.convert('RGBA')
            if tarja:
                s = mola(F, 12, 0.6, 160)
                colar(top, tarja, W / 2, 230 - (1 - s) * 300)
            if cena.leg:
                cena.leg.draw(top, W / 2, 1400 + cena.leg.alt / 2 - 30, f, 4, 'pop', 3, fundo=True)  # área segura: acima dos ~420 px de baixo
            colar(top, marca, 80, 1530, alpha=0.75, canto=True)
            ImageDraw.Draw(top).rectangle([0, 0, int(W * (F + 1) / total), 7], fill=LIME + (255,))
            img = top.convert('RGB')
            if flash > 0:
                img = Image.blend(img, Image.new('RGB', (W, H), (255, 255, 255)), min(0.9, flash))
            enc.stdin.write(img.tobytes())
        print(f'cena {i + 1}/{len(cenas)} ({cena.c["tipo"]}) ok', flush=True)
    enc.stdin.close()
    enc.wait()
    print('ok', saida, f'{total / FPS:.1f} s')


if __name__ == '__main__':
    main()
