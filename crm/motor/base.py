"""Peças visuais do @crmquevende, compartilhadas pelo reel e pelo post (Pillow/numpy, sem biblioteca de motion).
Cores, fontes, palavras com brilho neon, cartões de vidro, bolinhas neon, traço sendo desenhado e formas à mão."""
import math, re, zlib
from functools import lru_cache
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

BG, BG2 = (11, 15, 20), (17, 24, 39)
LIME, TXT, MUTED = (198, 255, 61), (245, 243, 238), (138, 148, 166)
VERMELHO, CIANO, ROSA, VERDE_WPP = (255, 92, 92), (61, 224, 255), (255, 77, 196), (37, 211, 102)
VIDRO = (24, 32, 46, 238)
CORES = {'lime': LIME, 'vermelho': VERMELHO, 'ciano': CIANO, 'rosa': ROSA, 'branco': TXT, 'cinza': MUTED}
PASTA_F = '/usr/share/fonts/opentype/inter/'
FONTES = {'black': 'InterDisplay-Black.otf', 'xbold': 'Inter-ExtraBold.otf', 'bold': 'Inter-Bold.otf',
          'semi': 'Inter-SemiBold.otf', 'med': 'Inter-Medium.otf'}


def clamp01(x):
    return max(0.0, min(1.0, x))


def lerp(f, a, b, va, vb):
    return va + (vb - va) * clamp01((f - a) / (b - a)) if b != a else vb


def sai(p):
    """ease-out cúbico"""
    p = clamp01(p)
    return 1 - (1 - p) ** 3


def mola(t, damping=11, mass=0.6, stiffness=180, fps=30):
    """Mola amortecida 0→1 (passa um pouco do ponto e volta). t em frames."""
    if t <= 0:
        return 0.0
    ts = t / fps
    w0 = math.sqrt(stiffness / mass)
    z = damping / (2 * math.sqrt(stiffness * mass))
    if z < 1:
        wd = w0 * math.sqrt(1 - z * z)
        return 1 - math.exp(-z * w0 * ts) * (math.cos(wd * ts) + (z * w0 / wd) * math.sin(wd * ts))
    return 1 - math.exp(-w0 * ts) * (1 + w0 * ts)


def rnd(*k):
    """Aleatório determinístico (igual em toda execução)."""
    return (zlib.crc32(repr(k).encode()) % 100003) / 100003.0


def limpa(t):
    """Tira emoji (as fontes não têm) e espaços duplos."""
    t = re.sub(r'[\U00010000-\U0010ffff☀-➿️‍]', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def corpo(peso, tam):
    return _fonte(peso, int(tam))


@lru_cache(maxsize=256)
def _fonte(peso, tam):
    return ImageFont.truetype(PASTA_F + FONTES[peso], tam)


def moeda(v):
    return f'{int(round(v)):,}'.replace(',', '.')


# ---------- colar com recorte ----------
_LUT = {}


def colar(base, sp, cx, cy, esc=1.0, alpha=1.0, rot=0.0, canto=False):
    if esc <= 0.01 or alpha <= 0.01:
        return
    if esc != 1:
        sp = sp.resize((max(1, round(sp.width * esc)), max(1, round(sp.height * esc))), Image.BILINEAR)
    if rot:
        sp = sp.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 0.99:
        k = round(alpha * 50)
        if k not in _LUT:
            _LUT[k] = [int(v * k / 50) for v in range(256)]
        sp = sp.copy()
        sp.putalpha(sp.getchannel('A').point(_LUT[k]))
    x, y = (round(cx), round(cy)) if canto else (round(cx - sp.width / 2), round(cy - sp.height / 2))
    x0, y0 = max(0, -x), max(0, -y)
    x1, y1 = min(sp.width, base.width - x), min(sp.height, base.height - y)
    if x1 <= x0 or y1 <= y0:
        return
    if (x0, y0, x1, y1) != (0, 0, sp.width, sp.height):
        sp = sp.crop((x0, y0, x1, y1))
    base.alpha_composite(sp, (x + x0, y + y0))


# ---------- sprites ----------
@lru_cache(maxsize=4096)
def palavra(w, tam, peso='black', cor=TXT, brilho=False, sombra=True):
    f = corpo(peso, tam)
    asc, desc = f.getmetrics()
    pad = int(tam * 0.3) + (int(tam * 0.3) if brilho else 0)
    larg = max(1, int(f.getlength(w)))
    im = Image.new('RGBA', (larg + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).text((pad, pad), w, font=f, fill=255)
    if brilho:
        g = m.filter(ImageFilter.GaussianBlur(tam * 0.22))
        im.paste(cor + (255,), (0, 0), g.point(lambda v: min(255, int(v * 1.3))))
    if sombra:
        s = ImageChops.offset(m, 0, max(2, tam // 18)).filter(ImageFilter.GaussianBlur(max(2, tam * 0.07)))
        im.paste((0, 0, 0, 255), (0, 0), s.point(lambda v: int(v * 0.85)))
    im.paste(cor + (255,), (0, 0), m)
    return im


@lru_cache(maxsize=512)
def cartao(w, h, r=28, fill=VIDRO, borda=(255, 255, 255, 34), sombra=40, lb=2, brilho=None):
    """Cartão de vidro escuro com sombra (e borda neon opcional)."""
    w, h = int(w), int(h)
    pad = sombra if sombra else 4
    if brilho:
        pad = max(pad, 40)
    im = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if sombra:
        m = Image.new('L', im.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([pad, pad + 16, pad + w, pad + h + 16], r, fill=170)
        im.paste((0, 0, 0, 255), (0, 0), m.filter(ImageFilter.GaussianBlur(sombra / 2.2)))
    if brilho:
        m = Image.new('L', im.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([pad, pad, pad + w, pad + h], r, outline=255, width=6)
        im.paste(brilho + (255,), (0, 0), m.filter(ImageFilter.GaussianBlur(12)))
    over = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(over).rounded_rectangle([pad, pad, pad + w, pad + h], r, fill=fill, outline=borda, width=lb)
    im.alpha_composite(over)
    return im


@lru_cache(maxsize=64)
def neon(cor, r):
    """Bolinha neon: miolo claro + halo borrado."""
    s = int(r * 9)
    m = Image.new('L', (s, s), 0)
    ImageDraw.Draw(m).ellipse([s / 2 - r * 2.4, s / 2 - r * 2.4, s / 2 + r * 2.4, s / 2 + r * 2.4], fill=150)
    halo = m.filter(ImageFilter.GaussianBlur(r * 1.4))
    im = Image.new('RGBA', (s, s), cor + (0,))
    im.putalpha(halo)
    d = ImageDraw.Draw(im)
    d.ellipse([s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r], fill=tuple(min(255, c + 60) for c in cor) + (255,))
    return im


@lru_cache(maxsize=64)
def anel(cor, r, larg=6):
    s = int(r * 2 + 60)
    m = Image.new('L', (s, s), 0)
    ImageDraw.Draw(m).ellipse([30, 30, 30 + 2 * r, 30 + 2 * r], outline=255, width=larg)
    im = Image.new('RGBA', (s, s), cor + (0,))
    im.putalpha(ImageChops.lighter(m, m.filter(ImageFilter.GaussianBlur(8)).point(lambda v: min(255, v * 2))))
    return im


def runs(txt):
    """'Texto com <destaque>' → [(palavra, destacada?)]"""
    out, dest = [], False
    for parte in re.split(r'([<>])', txt):
        if parte == '<':
            dest = True
        elif parte == '>':
            dest = False
        else:
            for w in parte.split():
                if out and re.fullmatch(r'[.,!?:;…]+', w):
                    out.append((w, False, True))  # pontuação colada na palavra anterior
                else:
                    out.append((w, dest, False))
    return out


class Texto:
    """Bloco de texto quebrado em linhas, com palavras <destacadas> em lime e brilho neon, animado palavra a palavra."""

    def __init__(self, txt, tam, peso='black', cor=TXT, dest=LIME, max_w=920, upper=True, entre=1.08, brilho=True, sombra=True):
        txt = limpa(txt)
        if upper:
            txt = txt.upper()
        itens = runs(txt)
        f = corpo(peso, tam)
        esp = f.getlength(' ')
        self.tam, self.n = tam, len(itens)
        self.dest = [d for _, d, _ in itens]
        self.sp = [palavra(w, tam, peso, dest if d else cor, brilho and d, sombra) for w, d, _ in itens]
        larg = [f.getlength(w) for w, _, _ in itens]
        cola = [k for _, _, k in itens]
        linhas, atual, l = [], [], 0
        for i, lw in enumerate(larg):
            if atual and l + lw > max_w and not cola[i]:
                linhas.append((atual, l - esp)); atual, l = [], 0
            if cola[i] and atual:
                l -= esp
            atual.append(i); l += lw + esp
        linhas.append((atual, l - esp))
        alt = tam * entre
        self.alt = alt * len(linhas)
        self.larg = max(l for _, l in linhas)
        self.pos, self.caixa, self.linhas = {}, {}, []
        for li, (idx, l) in enumerate(linhas):
            x = -l / 2
            y = -self.alt / 2 + li * alt + alt / 2
            for i in idx:
                if cola[i] and i != idx[0]:
                    x -= esp
                self.pos[i] = (x + larg[i] / 2, y)
                self.caixa[i] = (larg[i], tam)
                x += larg[i] + esp
            self.linhas.append((idx, l, y))

    def caixa_dest(self, cx, cy):
        """Retângulo que cobre as palavras destacadas (para circular/sublinhar)."""
        ids = [i for i in range(self.n) if self.dest[i]] or list(range(self.n))
        xs = [cx + self.pos[i][0] - self.caixa[i][0] / 2 for i in ids] + [cx + self.pos[i][0] + self.caixa[i][0] / 2 for i in ids]
        ys = [cy + self.pos[i][1] - self.tam * 0.55 for i in ids] + [cy + self.pos[i][1] + self.tam * 0.55 for i in ids]
        return min(xs), min(ys), max(xs), max(ys)

    def fim(self, passo):
        return (self.n - 1) * passo

    def draw(self, base, cx, cy, f, ini=0, modo='pop', passo=4, alpha=1.0, fundo=False):
        if fundo:
            for idx, l, y in self.linhas:
                d = f - ini - idx[0] * passo
                if d >= 0:
                    p = sai(d / 6)
                    colar(base, pilula(int(l + self.tam * 0.7), int(self.tam * 1.25)), cx, cy + y + self.tam * 0.06, 0.9 + 0.1 * p, alpha * p * 0.92)
        for i, sp in enumerate(self.sp):
            d = f - ini - i * passo
            if d < 0:
                continue
            x, y = cx + self.pos[i][0], cy + self.pos[i][1]
            if modo == 'slam':
                s = mola(d, 9, 0.5, 230)
                esc = 2.6 + (1 - 2.6) * s
                a = alpha * clamp01(d / 3)
                trem = (rnd('ts', i, f) - 0.5) * 22 if d < 7 else 0
                colar(base, sp, x + trem, y + trem * 0.5, esc, a)
            elif modo == 'sobe':
                p = sai(d / 9)
                colar(base, sp, x, y + (1 - p) * 50, 1, alpha * p)
            elif modo == 'fixo':
                colar(base, sp, x, y, 1, alpha)
            else:  # pop
                s = mola(d, 10, 0.5, 200)
                colar(base, sp, x, y + (1 - s) * 30, 0.35 + 0.65 * s, alpha * clamp01(d / 3))


@lru_cache(maxsize=256)
def pilula(w, h, cor=(0, 0, 0, 215)):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], int(h * 0.28), fill=cor)
    return im


def rotulo(txt, tam=26, cor=MUTED, esp=5, peso='xbold'):
    """Texto pequeno em caixa alta com letras espaçadas."""
    txt = limpa(txt).upper()
    f = corpo(peso, tam)
    larg = sum(f.getlength(c) + esp for c in txt) - esp
    asc, desc = f.getmetrics()
    im = Image.new('RGBA', (int(larg) + 8, asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 4
    for c in txt:
        d.text((x, 4), c, font=f, fill=cor + (255,))
        x += f.getlength(c) + esp
    return im


def texto_simples(txt, tam, peso='semi', cor=TXT, max_w=None, centro=False):
    """Sprite de texto corrido (quebra de linha) sem animação."""
    txt = limpa(txt)
    f = corpo(peso, tam)
    linhas = []
    for par in txt.split('\n'):
        atual = ''
        for w in par.split():
            if max_w and atual and f.getlength(atual + ' ' + w) > max_w:
                linhas.append(atual); atual = w
            else:
                atual = (atual + ' ' + w).strip()
        linhas.append(atual)
    alt = int(tam * 1.28)
    larg = int(max(f.getlength(l) for l in linhas)) + 4
    im = Image.new('RGBA', (larg, alt * len(linhas) + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(linhas):
        d.text(((larg - f.getlength(l)) / 2 if centro else 0, i * alt), l, font=f, fill=cor + (255,))
    return im


# ---------- traço sendo desenhado ----------
def parcial(pts, p):
    """Primeiros p (0..1) do caminho, pelo comprimento."""
    if p >= 1:
        return pts
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    alvo = sum(seg) * clamp01(p)
    out = [pts[0]]
    for i, s in enumerate(seg):
        if alvo <= s:
            if s > 0:
                t = alvo / s
                out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t))
            return out
        out.append(pts[i + 1]); alvo -= s
    return out


def traco(base, pts, p=1.0, cor=LIME, larg=9, ponta=True, glow=True):
    """Desenha o caminho até a fração p com brilho neon e uma ponta de caneta acesa."""
    if p <= 0 or len(pts) < 2:
        return
    seg = parcial(pts, p)
    if len(seg) < 2:
        return
    xs, ys = [q[0] for q in seg], [q[1] for q in seg]
    pad = 40
    x0, y0 = int(min(xs)) - pad, int(min(ys)) - pad
    w, h = int(max(xs)) - x0 + pad, int(max(ys)) - y0 + pad
    m = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(m)
    loc = [(x - x0, y - y0) for x, y in seg]
    d.line(loc, fill=255, width=larg, joint='curve')
    for q in (loc[0], loc[-1]):
        d.ellipse([q[0] - larg / 2, q[1] - larg / 2, q[0] + larg / 2, q[1] + larg / 2], fill=255)
    if glow:
        g = m.resize((max(1, w // 3), max(1, h // 3)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)).resize((w, h), Image.BILINEAR)
        a = ImageChops.lighter(m, g.point(lambda v: min(255, v * 2)))
    else:
        a = m
    im = Image.new('RGBA', (w, h), cor + (0,))
    im.putalpha(a)
    colar(base, im, x0, y0, canto=True)
    if ponta and p < 1:
        colar(base, neon((255, 255, 255), 6), seg[-1][0], seg[-1][1])


def forma(nome, x0, y0, x1, y1, semente=1):
    """Caminhos desenhados à mão (pontos absolutos)."""
    cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    j = lambda i: (rnd('j', semente, i) - 0.5)
    if nome == 'circulo':
        pts = []
        for i in range(73):
            a = -math.pi * 0.62 + i / 72 * math.pi * 2.18
            rx, ry = w / 2 + 34 + j(i // 6) * 14, h / 2 + 26 + j(i // 5 + 50) * 10
            pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
        return pts
    if nome == 'sublinha':
        return [(x0 - 10 + w * 1.04 * i / 30, y1 + 10 + math.sin(i / 30 * math.pi * 2.2) * 7 + j(i) * 3) for i in range(31)]
    if nome == 'check':
        return [(x0, cy), (x0 + w * 0.36, y1), (x1, y0)]
    if nome == 'x':
        return [(x0, y0), (x1, y1), (cx, cy), (x1, y0), (x0, y1)]
    if nome == 'seta':
        # de (x0,y0) até (x1,y1), curvada, com ponta
        pts = []
        mx, my = cx + h * 0.25, cy - w * 0.25
        for i in range(25):
            t = i / 24
            pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1))
        ang = math.atan2(y1 - pts[-3][1], x1 - pts[-3][0])
        for da in (2.6, -2.6):
            pts += [(x1 + math.cos(ang + da) * 44, y1 + math.sin(ang + da) * 44), (x1, y1)]
        return pts
    if nome == 'funil':
        bx = w * 0.1
        return [(x0, y0), (x1, y0), (cx + bx, y0 + h * 0.72), (cx + bx, y1), (cx - bx, y1), (cx - bx, y0 + h * 0.72), (x0, y0)]
    raise ValueError(nome)
