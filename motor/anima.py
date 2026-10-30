"""Cenas 100% animadas do PV Edições (sem imagem do banco): o "Ronin", um personagem de tinta com cachecol vermelho,
desenhado frame a frame com Pillow. Fundo claro de papel (primeiro frame claro, como pediu a análise de 29/10).
Cada cena é uma função (f, dur) -> Image RGB 1080x1920. O texto continua sendo desenhado pelo reel.py.
Cenas: sombra, chuva, levanta, escada, corrida, multidao, sol, espada, poste."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
PAPEL = (236, 232, 222)
TINTA = (18, 16, 16)
VERMELHO = (229, 25, 46)
CHAO = 1560

_rng = np.random.default_rng(3)
_textura = (_rng.random((H // 4, W // 4)) * 18 - 9)
_PAPEL_IMG = Image.fromarray(np.clip(np.array(PAPEL, np.float32)[None, None, :] + np.kron(_textura, np.ones((4, 4)))[:, :, None], 0, 255).astype(np.uint8))


def r(*k):
    return (hash(k) % 10007) / 10007.0


def suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    return {k: a[k] + (b[k] - a[k]) * t for k in a}


# ---------- o boneco ----------
# ângulos absolutos em graus: 0 = para baixo, 180 = para cima, positivo gira para a direita
EM_PE = dict(tronco=180, cabeca=180, braco_e=8, ante_e=4, braco_d=-8, ante_d=-4, coxa_e=5, canela_e=0, coxa_d=-5, canela_d=0)
AJOELHADO = dict(tronco=150, cabeca=120, braco_e=25, ante_e=10, braco_d=15, ante_d=5, coxa_e=85, canela_e=2, coxa_d=-15, canela_d=-92)
SENTADO = dict(tronco=165, cabeca=140, braco_e=40, ante_e=95, braco_d=30, ante_d=90, coxa_e=95, canela_e=10, coxa_d=88, canela_d=4)
ESPADA_ALTO = dict(tronco=176, cabeca=178, braco_e=150, ante_e=165, braco_d=140, ante_d=160, coxa_e=25, canela_e=5, coxa_d=-20, canela_d=-5)
ESPADA_CORTE = dict(tronco=150, cabeca=160, braco_e=55, ante_e=70, braco_d=50, ante_d=65, coxa_e=55, canela_e=0, coxa_d=-35, canela_d=-15)


def andar(fase, corrida=False):
    a = 38 if corrida else 24
    s = math.sin(fase)
    p = dict(EM_PE)
    p['tronco'] = 168 if corrida else 177
    p['coxa_e'], p['coxa_d'] = a * s, -a * s
    p['canela_e'] = p['coxa_e'] - (55 if corrida else 25) * max(0, -math.cos(fase))
    p['canela_d'] = p['coxa_d'] - (55 if corrida else 25) * max(0, math.cos(fase))
    p['braco_e'], p['braco_d'] = -a * s * 0.9, a * s * 0.9
    p['ante_e'] = p['braco_e'] + (70 if corrida else 20)
    p['ante_d'] = p['braco_d'] + (70 if corrida else 20)
    return p


def _v(ang, comp):
    a = math.radians(ang)
    return math.sin(a) * comp, math.cos(a) * comp


def juntas(p, s):
    q = (0.0, 0.0)  # quadril
    def soma(a, ang, comp):
        dx, dy = _v(ang, comp * s)
        return a[0] + dx, a[1] + dy
    pesc = soma(q, p['tronco'], 1.0)
    cab = soma(pesc, p['cabeca'], 0.32)
    j = dict(quadril=q, pescoco=pesc, cabeca=cab)
    j['cot_e'] = soma(pesc, p['braco_e'], 0.52); j['mao_e'] = soma(j['cot_e'], p['ante_e'], 0.48)
    j['cot_d'] = soma(pesc, p['braco_d'], 0.52); j['mao_d'] = soma(j['cot_d'], p['ante_d'], 0.48)
    j['joe_e'] = soma(q, p['coxa_e'], 0.66); j['pe_e'] = soma(j['joe_e'], p['canela_e'], 0.62)
    j['joe_d'] = soma(q, p['coxa_d'], 0.66); j['pe_d'] = soma(j['joe_d'], p['canela_d'], 0.62)
    return j


def boneco(d, p, x, chao, s, cor=TINTA, cachecol=0.0, espada=None, olhos=None, espelho=False):
    """Desenha o Ronin com os pés no chão. cachecol = fase do vento (None = sem cachecol)."""
    j = juntas(p, s)
    if espelho:
        j = {k: (-v[0], v[1]) for k, v in j.items()}
    base = max(v[1] for k, v in j.items() if k != 'cabeca')
    pt = lambda k: (x + j[k][0], chao - base + j[k][1])
    g = max(4, int(s * 0.17))
    seg = [('pescoco', 'quadril'), ('pescoco', 'cot_e'), ('cot_e', 'mao_e'), ('pescoco', 'cot_d'), ('cot_d', 'mao_d'),
           ('quadril', 'joe_e'), ('joe_e', 'pe_e'), ('quadril', 'joe_d'), ('joe_d', 'pe_d')]
    for a, b in seg:
        larg = int(g * (1.5 if (a, b) == ('pescoco', 'quadril') else 1))
        d.line([pt(a), pt(b)], fill=cor, width=larg)
        for k in (a, b):
            cx, cy = pt(k); rr = larg / 2
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=cor)
    cx, cy = pt('cabeca')
    rr = s * 0.2
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=cor)
    # chapéu de palha (ronin)
    d.polygon([(cx - rr * 1.9, cy - rr * 0.35), (cx + rr * 1.9, cy - rr * 0.35), (cx, cy - rr * 1.5)], fill=cor)
    if olhos:
        lado = -1 if espelho else 1
        for o in (-0.35, 0.35):
            ox = cx + lado * 0.25 * rr + o * rr
            d.ellipse([ox - rr * 0.14, cy - rr * 0.05, ox + rr * 0.14, cy + rr * 0.12], fill=olhos)
    if cachecol is not None:
        px, py = pt('pescoco')
        lado = 1 if espelho else -1
        pts = [(px, py + g * 0.3)]
        for i in range(1, 9):
            pts.append((px + lado * i * s * 0.11, py + g * 0.3 + math.sin(cachecol + i * 0.8) * s * 0.035 * i ** 0.6 + i * s * 0.015))
        d.line(pts, fill=VERMELHO, width=max(4, int(g * 0.9)), joint='curve')
        d.line([(px - g * 0.6, py), (px + g * 0.6, py)], fill=VERMELHO, width=max(4, int(g * 0.9)))
    if espada:
        mx, my = pt('mao_e') if not espelho else pt('mao_e')
        ang = math.radians(espada)
        d.line([(mx, my), (mx + math.sin(ang) * s * 1.4, my + math.cos(ang) * s * 1.4)], fill=cor, width=max(3, g // 2))
        d.line([(mx - math.cos(ang) * g, my + math.sin(ang) * g), (mx + math.cos(ang) * g, my - math.sin(ang) * g)], fill=cor, width=g // 2 + 2)
    return pt


def papel():
    return _PAPEL_IMG.copy()


def tinta_chao(d, y=CHAO, f=0):
    d.line([(0, y), (W, y)], fill=TINTA, width=8)
    for i in range(14):
        x = r('c', i) * W
        d.line([(x, y + 18 + r('cy', i) * 40), (x + 40 + r('cl', i) * 120, y + 18 + r('cy', i) * 40)], fill=TINTA, width=3)


# ---------- cenas ----------
def sombra(f, dur):
    im = papel(); d = ImageDraw.Draw(im)
    t = suave(f / max(1, dur * 0.8))
    # a sombra gigante na parede, crescendo
    s_g = 250 + 90 * t
    camada = Image.new('L', (W, H), 0)
    pt = boneco(ImageDraw.Draw(camada), EM_PE, 420, CHAO + 10, s_g, cor=255, cachecol=None)
    camada = camada.filter(ImageFilter.GaussianBlur(6))
    cinza = Image.new('RGB', (W, H), (70, 64, 60))
    im.paste(cinza, (0, 0), camada.point(lambda v: int(v * (0.55 + 0.35 * t))))
    d = ImageDraw.Draw(im)
    if f > dur * 0.45:
        cx, cy = pt('cabeca')
        a = suave((f - dur * 0.45) / 8)
        for o in (-0.35, 0.35):
            ox = cx + o * s_g * 0.2
            d.ellipse([ox - 22 * a, cy - 8 * a, ox + 22 * a, cy + 10 * a], fill=VERMELHO)
    tinta_chao(d)
    boneco(d, EM_PE, 700, CHAO, 210, cachecol=f * 0.25)
    return im


def chuva(f, dur):
    im = papel(); d = ImageDraw.Draw(im)
    tinta_chao(d)
    boneco(d, AJOELHADO, 560, CHAO, 210, cachecol=f * 0.12)
    for i in range(140):
        x = (r('x', i) * (W + 400) + f * 9) % (W + 400) - 200
        y = (r('y', i) * H + f * (55 + r('v', i) * 25)) % H
        d.line([(x, y), (x - 14, y + 70)], fill=(60, 58, 60), width=3)
    if int(dur * 0.55) <= f < int(dur * 0.55) + 3:
        im = Image.eval(im, lambda v: 255 - v)
    return im


def levanta(f, dur):
    im = papel(); d = ImageDraw.Draw(im)
    t = suave(f / max(1, dur * 0.65))
    tinta_chao(d)
    boneco(d, mix(AJOELHADO, EM_PE, t), 560, CHAO, 215, cachecol=f * 0.3)
    if t > 0.3:
        for i in range(18):
            k = (f - dur * 0.2) * (0.6 + r('p', i))
            x = 560 + (r('px', i) - 0.5) * 2 * k * 6
            y = CHAO - abs(math.sin(i)) * k * 2.5
            rr = 3 + r('pr', i) * 6
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(90, 86, 80))
    return im


def escada(f, dur):
    im = papel(); d = ImageDraw.Draw(im)
    passo_x, passo_y = 170, 110
    desl = (f / 24) % 1  # um degrau a cada 24 frames
    for k in range(-6, 10):
        x = 540 + (k - desl) * passo_x - 80
        y = CHAO - 200 - (k - desl) * passo_y
        d.polygon([(x, y), (x + passo_x, y), (x + passo_x, y + 40), (x, y + 40)], fill=TINTA)
        d.line([(x + passo_x, y), (x + passo_x, H)], fill=(120, 116, 110), width=3)
    fase = f / 24 * math.pi * 2
    p = andar(fase)
    p['tronco'] = 170
    boneco(d, p, 560, CHAO - 200 - (0.5 - desl) * passo_y * 0.3 + 4, 200, cachecol=f * 0.3)
    return im


def corrida(f, dur):
    im = papel(); d = ImageDraw.Draw(im)
    for i in range(10):
        x = (r('poste', i) * W * 2 - f * 38) % (W * 1.6) - 200
        d.rectangle([x, CHAO - 700, x + 26, CHAO], fill=(170, 164, 156))
    tinta_chao(d)
    for i in range(30):
        x = (r('vel', i) * W * 2 - f * 70) % (W * 1.5) - 200
        y = 700 + r('vy', i) * 800
        d.line([(x, y), (x + 120 + r('vl', i) * 200, y)], fill=(110, 106, 100), width=3)
    boneco(d, andar(f / 9 * math.pi, corrida=True), 520, CHAO - abs(math.sin(f / 9 * math.pi)) * 18, 210, cachecol=f * 0.6)
    return im


def multidao(f, dur):
    im = papel(); d = ImageDraw.Draw(im)
    tinta_chao(d)
    for i in range(16):
        prof = 0.55 + r('pf', i) * 0.35
        x = (r('mx', i) * W * 1.6 - f * (5 + 4 * prof)) % (W * 1.6) - 300
        cor = tuple(int(150 - 60 * prof) for _ in range(3))
        boneco(d, andar(f / 14 * math.pi + i, False), x, CHAO - (1 - prof) * 160, 150 * prof, cor=cor, cachecol=None, espelho=True)
    boneco(d, andar(f / 14 * math.pi), 540, CHAO, 210, cachecol=f * 0.3)
    return im


def sol(f, dur):
    im = papel(); d = ImageDraw.Draw(im)
    t = suave(f / max(1, dur))
    cy = CHAO + 120 - t * 520
    for i in range(24):
        a = i / 24 * math.pi * 2 + f * 0.004
        d.line([(540 + math.cos(a) * 340, cy + math.sin(a) * 340), (540 + math.cos(a) * 1400, cy + math.sin(a) * 1400)], fill=(214, 200, 190), width=10)
    d.ellipse([540 - 300, cy - 300, 540 + 300, cy + 300], fill=VERMELHO)
    d.polygon([(0, CHAO), (700, CHAO), (760, CHAO + 30), (760, H), (0, H)], fill=TINTA)
    d.rectangle([0, CHAO + 30, W, H], fill=TINTA)
    boneco(d, EM_PE, 600, CHAO, 205, cachecol=f * 0.2)
    return im


def espada(f, dur):
    im = papel(); d = ImageDraw.Draw(im)
    tinta_chao(d)
    corte = int(dur * 0.55)
    if f < corte:
        t = suave(f / max(1, corte - 4))
        p = mix(EM_PE, ESPADA_ALTO, t); ang = 180 + 15 * t
    else:
        p = ESPADA_CORTE; ang = 60
    boneco(d, p, 540, CHAO, 220, cachecol=f * 0.4, espada=ang)
    if f >= corte:
        a = suave((f - corte) / 4)
        x0, y0, x1, y1 = -100, 520, W + 100, 1350
        xm, ym = x0 + (x1 - x0) * a, y0 + (y1 - y0) * a
        d.polygon([(x0, y0 - 6), (xm, ym - 26), (xm, ym + 26), (x0, y0 + 6)], fill=TINTA)
        d.line([(x0, y0), (xm, ym)], fill=VERMELHO, width=8)
    return im


def poste(f, dur):
    im = papel(); d = ImageDraw.Draw(im)
    luz = Image.new('L', (W, H), 0)
    ImageDraw.Draw(luz).polygon([(770, 520), (300, CHAO), (1080, CHAO), (1080, 1300)], fill=255)
    luz = luz.filter(ImageFilter.GaussianBlur(30))
    escuro = Image.new('RGB', (W, H), (52, 48, 46))
    im = Image.composite(im, escuro, luz.point(lambda v: int(80 + v * 0.69)))
    d = ImageDraw.Draw(im)
    d.rectangle([800, 480, 828, CHAO], fill=TINTA)
    d.polygon([(700, 470), (828, 470), (828, 500), (720, 520)], fill=TINTA)
    tinta_chao(d)
    pisca = 1 if r('pisca', f // 3) > 0.12 else 0
    if pisca:
        d.ellipse([705, 505, 745, 530], fill=(255, 246, 210))
    boneco(d, SENTADO, 600, CHAO, 200, cachecol=f * 0.1)
    return im


CENAS = dict(sombra=sombra, chuva=chuva, levanta=levanta, escada=escada, corrida=corrida, multidao=multidao, sol=sol, espada=espada, poste=poste)


def cena(nome, f, dur):
    return CENAS[nome](f, dur)
