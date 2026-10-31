"""Carrossel de achadinhos no estilo das referências (BRIEFING-visual.md, 31/10), 1080x1350.
Foto POV sangrando a tela toda, texto branco por cima (nome bold + frase light), seta desenhada à mão.
Uso (na raiz do repo): python3 achadinhos/carrossel.py achadinhos/roteiros/AAAA-MM-DD-tema.json SAIDA/pasta
Roteiro JSON:
  dia: arquivo de achadinhos/dia (produtos, fotos do anúncio)
  capa: {titulo, versao, fotos: [4 caminhos]}  (colagem 2x2; sem foto usa a dos produtos)
  produtos: [{id, nome, texto, foto, pos, seta}]
    foto = caminho de uma foto POV (gerada por IA etc.); sem ela, monta uma provisória com a foto limpa do anúncio
    pos = "sup_dir" | "sup_esq" | "inf" (onde a foto tem respiro); seta = [x, y] para onde a seta aponta
  cta: {titulo, sub, foto}
  pilula: false (pílula "link | Nome" desligada a pedido do usuário em 31/10)
Saída: SAIDA/1.jpg, 2.jpg..."""
import json, math, os, sys, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1350
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
CACHE = os.path.join(AQUI, 'cache')
F_BOLD = '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
F_LIGHT = '/usr/share/fonts/opentype/inter/InterDisplay-Light.otf'
F_REG = '/usr/share/fonts/opentype/inter/Inter-Regular.otf'
BRANCO = (255, 255, 255)
ASSINATURA = 'Achadinhos do PV'


def fonte(caminho, tam):
    return ImageFont.truetype(caminho, tam)


def foto_anuncio(produto, idx=0):
    os.makedirs(CACHE, exist_ok=True)
    idx = min(idx, len(produto['fotos']) - 1)
    destino = os.path.join(CACHE, f"{produto['id']}-{idx}.jpg")
    if not os.path.exists(destino):
        urllib.request.urlretrieve(produto['fotos'][idx], destino)
    return Image.open(destino).convert('RGB')


def mesa(seed=0):
    """Fundo provisório: mesa de madeira quente desfocada com bokeh (só até as fotos POV chegarem)."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    veio = np.sin(x / 9 + np.sin(y / 140) * 3) * 0.5 + 0.5
    base = np.stack([120 + 40 * veio, 78 + 25 * veio, 48 + 14 * veio], -1)
    luz = np.exp(-(((x - W * 0.8) / 700) ** 2 + ((y - 0) / 600) ** 2))[..., None]
    arr = base * (0.55 + 0.7 * luz)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im, 'RGBA')
    for _ in range(14):
        cx, cy, r = rng.uniform(0, W), rng.uniform(0, H * 0.4), rng.uniform(30, 90)
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 220, 170, int(rng.uniform(25, 60))))
    return im.filter(ImageFilter.GaussianBlur(18))


def provisoria(produto, seed):
    """Produto recortado do fundo branco do anúncio, grande e levemente inclinado, sobre a mesa."""
    fundo = mesa(seed)
    p = foto_anuncio(produto, 0)
    arr = np.asarray(p).astype(np.int16)
    alfa = (255 - np.clip((arr.min(-1) - 225) * 9, 0, 255)).astype(np.uint8)
    rec = p.convert('RGBA')
    rec.putalpha(Image.fromarray(alfa).filter(ImageFilter.GaussianBlur(1.2)))
    rec = rec.crop(rec.getbbox())
    esc = min(760 / rec.width, 680 / rec.height)
    rec = rec.resize((int(rec.width * esc), int(rec.height * esc)), Image.LANCZOS).rotate(-8, Image.BICUBIC, expand=True)
    x, y = (W - rec.width) // 2 - 40, H - rec.height - 90
    sombra = Image.new('RGBA', fundo.size, (0, 0, 0, 0))
    sombra.paste((0, 0, 0, 150), (x + 30, y + 40), rec.getchannel('A'))
    fundo = Image.alpha_composite(fundo.convert('RGBA'), sombra.filter(ImageFilter.GaussianBlur(30)))
    fundo.alpha_composite(rec, (x, y))
    return fundo.convert('RGB')


def abrir(caminho):
    return ImageOps.fit(Image.open(os.path.join(RAIZ, caminho)).convert('RGB'), (W, H), Image.LANCZOS)


def escurecer(im, caixa, forca=0.5):
    """Escurecimento local e suave atrás do texto (sem caixa visível)."""
    x0, y0, x1, y1 = caixa
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse([x0 - 160, y0 - 140, x1 + 160, y1 + 140], fill=int(255 * forca))
    m = m.filter(ImageFilter.GaussianBlur(110))
    return Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), im, m)


def quebra(texto, f, largura):
    linhas, atual = [], ''
    for w in texto.split():
        if atual and f.getlength(atual + ' ' + w) > largura:
            linhas.append(atual)
            atual = w
        else:
            atual = (atual + ' ' + w).strip()
    return linhas + [atual]


def texto_centro(dr, cx, y, linhas, f, entre, sombra=None):
    for l in linhas:
        if sombra is not None:
            sombra.text((cx, y), l, font=f, fill=150, anchor='ma')
        dr.text((cx, y), l, font=f, fill=BRANCO, anchor='ma')
        y += entre
    return y


def seta(dr, de, para):
    """Seta fina desenhada à mão: curva quadrática + ponta aberta."""
    (x0, y0), (x1, y1) = de, para
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    n = math.hypot(nx, ny) or 1
    cx, cy = mx + nx / n * 70, my + ny / n * 70
    pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1)
           for t in np.linspace(0, 1, 40)]
    dr.line(pts, fill=BRANCO, width=5, joint='curve')
    ang = math.atan2(y1 - pts[-4][1], x1 - pts[-4][0])
    for d in (2.5, -2.5):
        dr.line([(x1, y1), (x1 - 34 * math.cos(ang + d / 6), y1 - 34 * math.sin(ang + d / 6))], fill=BRANCO, width=5)


def cantos(dr, esq=ASSINATURA, dir_baixo=None):
    f = fonte(F_LIGHT, 30)
    dr.text((60, 60), esq, font=f, fill=BRANCO, anchor='lm')
    if dir_baixo:
        dr.text((W - 60, H - 64), dir_baixo, font=f, fill=BRANCO, anchor='rm')


def pilula(dr, cx, y, texto):
    f = fonte(F_REG, 30)
    larg = f.getlength(texto) + 96
    x = cx - larg / 2
    dr.rounded_rectangle([x, y, x + larg, y + 60], 30, fill=(237, 232, 226))
    for dx in (-7, 7):
        dr.rounded_rectangle([x + 38 + dx - 10, y + 25, x + 38 + dx + 10, y + 35], 5, outline=(60, 60, 60), width=3)
    dr.text((x + 66, y + 30), texto, font=f, fill=(60, 60, 60), anchor='lm')


def com_sombra(base, desenhar):
    """Desenha o texto com uma sombra bem suave por baixo."""
    sombra = Image.new('L', (W, H), 0)
    camada = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    desenhar(ImageDraw.Draw(camada), ImageDraw.Draw(sombra))
    s = sombra.filter(ImageFilter.GaussianBlur(10))
    base = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), base, s.point(lambda v: v * 0.6))
    base.paste(camada, (0, 0), camada)
    return base


def slide_capa(r, produtos):
    fotos = r['capa'].get('fotos') or []
    meio = Image.new('RGB', (W, H))
    for k in range(4):
        if k < len(fotos):
            im = Image.open(os.path.join(RAIZ, fotos[k])).convert('RGB')
        else:
            p, c = produtos[k % len(produtos)]
            im = abrir(c['foto']) if c.get('foto') else provisoria(p, k)
        meio.paste(ImageOps.fit(im, (W // 2, H // 2), Image.LANCZOS), ((k % 2) * W // 2, (k // 2) * H // 2))
    base = escurecer(meio, (100, 380, W - 100, 900), 0.55)
    fb, fl = fonte(F_BOLD, 118), fonte(F_LIGHT, 74)

    def desenha(dr, ds):
        linhas = quebra(r['capa']['titulo'], fb, W - 120)
        y = 640 - len(linhas) * 112 // 2 - 40
        y = texto_centro(dr, W // 2, y, linhas, fb, 112, ds)
        texto_centro(dr, W // 2, y + 6, [f"({r['capa']['versao']})"], fl, 80, ds)
        cantos(dr, ASSINATURA, 'arrasta pro lado  →')
    return com_sombra(base, desenha)


POS = {'sup_dir': (W * 0.7, 200), 'sup_esq': (W * 0.3, 200), 'inf': (W * 0.5, 900)}


def slide_produto(p, c, i, usar_pilula):
    base = abrir(c['foto']) if c.get('foto') else provisoria(p, i)
    cx, y0 = POS[c.get('pos', 'sup_dir')]
    cx = int(cx)
    fb, fl = fonte(F_BOLD, 66), fonte(F_LIGHT, 44)
    larg = 560 if c.get('pos', 'sup_dir') != 'inf' else 820
    nome, txt = quebra(c['nome'], fb, larg)[:2], quebra(c['texto'], fl, larg)[:4]
    alt = len(nome) * 64 + 16 + len(txt) * 48 + (80 if usar_pilula else 0)
    base = escurecer(base, (cx - larg // 2, y0, cx + larg // 2, y0 + alt), 0.45)

    def desenha(dr, ds):
        y = texto_centro(dr, cx, y0, nome, fb, 64, ds) + 16
        y = texto_centro(dr, cx, y, txt, fl, 48, ds)
        if usar_pilula:
            pilula(dr, cx, y + 18, 'link | ' + c['nome'])
        if c.get('seta'):
            alvo = tuple(c['seta'])
            de = (cx - larg // 2 + 20, y0 + 30) if alvo[0] < cx else (cx + larg // 2 - 20, y0 + 30)
            if alvo[1] > y:
                de = (cx + (-80 if alvo[0] < cx else 80), y + 30)
            seta(dr, de, alvo)
        cantos(dr)
    return com_sombra(base, desenha)


def slide_cta(r):
    c = r['cta']
    base = abrir(c['foto']) if c.get('foto') else mesa(99)
    base = escurecer(base, (140, 880, W - 140, 1160), 0.55)
    fb, fl = fonte(F_BOLD, 80), fonte(F_LIGHT, 60)

    def desenha(dr, ds):
        y = texto_centro(dr, W // 2, 880, quebra(c['titulo'], fb, W - 200), fb, 80, ds) + 40
        texto_centro(dr, W // 2, y, quebra(c['sub'], fl, W - 260), fl, 64, ds)
        cantos(dr)
    return com_sombra(base, desenha)


def main():
    roteiro, pasta = sys.argv[1], sys.argv[2]
    r = json.load(open(roteiro))
    dia = json.load(open(os.path.join(AQUI, 'dia', r['dia'])))
    por_id = {p['id']: p for p in dia['produtos']}
    produtos = [(por_id[c['id']], c) for c in r['produtos']]
    os.makedirs(pasta, exist_ok=True)
    slides = [slide_capa(r, produtos)]
    slides += [slide_produto(p, c, i + 1, r.get('pilula', False)) for i, (p, c) in enumerate(produtos)]
    slides.append(slide_cta(r))
    for k, s in enumerate(slides, 1):
        s.save(os.path.join(pasta, f'{k}.jpg'), quality=92)
    print(f'{len(slides)} slides em {pasta}')


if __name__ == '__main__':
    main()
