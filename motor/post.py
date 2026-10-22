"""Motor próprio dos posts de imagem do PV Edições (sem Remotion): headline editada direto na foto, 1080x1350.
Uso (na raiz do repo): python3 motor/post.py modelo/posts/AAAA-MM-DD.json postados-img/AAAA-MM-DD.jpg
JSON: imagem, headline, destaque (palavras da headline que viram tarja vermelha), sub (linha aesthetic),
pb (true = preto e branco), posicao ("baixo" padrão | "topo"), foco ("top"/"bottom" para enquadrar).
Carrossel (estratégia 22/10): JSON com "serie" (ex.: "VAGABOND · MUSASHI") e "slides": [ {mesmos campos}, ... ].
Saída vira ARQUIVO-1.jpg, ARQUIVO-2.jpg... (passe postados-img/AAAA-MM-DD.jpg). Slide 1 ganha "ARRASTA →", todos ganham n/total."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1350
VERMELHO, CREME = (229, 25, 46), (244, 241, 234)
PUBLIC = os.path.join(os.path.dirname(__file__), '..', 'modelo', 'public')
F_BLACK = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
F_BOLD = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
F_SERIFA = '/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf'


def render(p, saida, idx=0, total=1, serie=None):
    topo = p.get('posicao') == 'topo'
    im = Image.open(os.path.join(PUBLIC, p['imagem'])).convert('RGB')
    centro = {'top': (0.5, 0.15), 'bottom': (0.5, 0.85)}.get(p.get('foco'), (0.5, 0.5))
    im = ImageOps.fit(im, (W, H), Image.LANCZOS, centering=centro)
    arr = np.asarray(im).astype(np.float32)
    if p.get('pb'):
        g = arr @ np.array([0.299, 0.587, 0.114], np.float32)
        g = np.clip((g - 128) * 1.25 + 128, 0, 255) * 0.9
        arr = np.repeat(g[..., None], 3, 2)
    else:
        arr = np.clip((arr - 128) * 1.08 + 128, 0, 255)
    # degradê escuro onde fica o texto + vinheta
    y = np.linspace(0, 1, H)[:, None]
    t = (1 - y) if not topo else y
    grad = np.interp(t, [0, 0.4, 0.66, 1], [0.94, 0.62, 0, 0])
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    vin = np.clip((d - 0.55) / 0.5, 0, 1) * 0.6
    escuro = 1 - np.clip(grad + vin - grad * vin, 0, 1)
    arr = arr * escuro[..., None]
    arr = arr + np.random.default_rng(3).random((H, W))[..., None] * 255 * 0.06  # grão
    base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
    dr = ImageDraw.Draw(base)
    dr.rectangle([28, 28, W - 29, H - 29], outline=CREME + (90,), width=2)

    headline = p.get('headline', '').upper()
    destaque = [x.upper() for x in p.get('destaque', [])]
    tam = 112 if len(headline) <= 22 else 92 if len(headline) <= 40 else 76
    fonte = ImageFont.truetype(F_BLACK, tam)
    esp = fonte.getlength(' ') + 10
    # quebra de linha
    linhas, atual, larg = [], [], 0
    for w in headline.split():
        lw = fonte.getlength(w) + (28 if w in destaque else 0)
        if atual and larg + lw > W - 168:
            linhas.append(atual); atual, larg = [], 0
        atual.append(w); larg += lw + esp
    linhas.append(atual)
    alt = tam * 1.04
    sub = p.get('sub')
    fs = ImageFont.truetype(F_SERIFA, 46)
    sub_linhas = []
    if sub:
        atual = ''
        for w in sub.split():
            if atual and fs.getlength(atual + ' ' + w) > W - 168:
                sub_linhas.append(atual); atual = w
            else:
                atual = (atual + ' ' + w).strip()
        sub_linhas.append(atual)
    bloco = 8 + 30 + alt * len(linhas) + (30 + 60 * len(sub_linhas) if sub else 0)
    y0 = 110 if topo else H - 110 - bloco
    x0 = 84
    dr.rectangle([x0, y0, x0 + 90, y0 + 8], fill=VERMELHO)
    yl = y0 + 38
    camada = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sombra = Image.new('L', (W, H), 0)
    dc, ds = ImageDraw.Draw(camada), ImageDraw.Draw(sombra)
    for li, linha in enumerate(linhas):
        x = x0
        yt = yl + li * alt
        for w in linha:
            lw = fonte.getlength(w)
            if w in destaque:
                tarja = Image.new('RGBA', (int(lw + 28), int(tam * 1.08)), VERMELHO + (255,))
                tarja = tarja.rotate(1.5, expand=True, resample=Image.BICUBIC)
                camada.alpha_composite(tarja, (int(x - 4), int(yt + tam * 0.03 - 6)))
                dc.text((x + 14, yt), w, font=fonte, fill=CREME)
                x += lw + 28 + esp
            else:
                ds.text((x, yt + 6), w, font=fonte, fill=150)
                dc.text((x, yt), w, font=fonte, fill=CREME)
                x += lw + esp
    base.paste((0, 0, 0, 255), (0, 0), sombra.filter(ImageFilter.GaussianBlur(18)))
    base.alpha_composite(camada)
    if sub:
        ys = yl + alt * len(linhas) + 30
        for i, l in enumerate(sub_linhas):
            dr = ImageDraw.Draw(base)
            dr.text((x0, ys + i * 60), l, font=fs, fill=CREME + (225,))
    fa = ImageFont.truetype(F_BOLD, 30)
    marca = '@PVEDICOES'
    mx = W - 72 - (fa.getlength(marca) + 4 * len(marca))
    my = (H - 64 - 30) if topo else 64
    for ch in marca:
        ImageDraw.Draw(base).text((mx, my), ch, font=fa, fill=CREME + (205,))
        mx += fa.getlength(ch) + 4
    if total > 1 or serie:
        dr = ImageDraw.Draw(base)
        fr = ImageFont.truetype(F_BOLD, 28)
        y = (H - 64 - 30) if topo else 64
        if serie:
            t = serie.upper()
            dr.rectangle([72, y - 8, 72 + fr.getlength(t) + 28, y + 40], fill=VERMELHO + (255,))
            dr.text((86, y - 2), t, font=fr, fill=CREME)
        if total > 1:
            t = ('ARRASTA  →  ' if idx == 0 else '') + f'{idx + 1}/{total}'
            yb = 64 if topo else H - 64 - 30
            dr.text((W - 72 - fr.getlength(t), yb), t, font=fr, fill=CREME + (220,))
    base.convert('RGB').save(saida, quality=92)
    print('ok', saida)


def main():
    p = json.load(open(sys.argv[1], encoding='utf-8'))
    if 'slides' not in p:
        return render(p, sys.argv[2])
    raiz, ext = os.path.splitext(sys.argv[2])
    for i, sl in enumerate(p['slides']):
        render(sl, f'{raiz}-{i + 1}{ext}', i, len(p['slides']), p.get('serie'))


if __name__ == '__main__':
    main()
