"""Carrossel de achadinhos, 1080x1350 (estratégia 30/10): capa com gancho, 1 produto por slide, slide final com CTA QUERO.
Uso (na raiz do repo): python3 achadinhos/carrossel.py achadinhos/roteiros/AAAA-MM-DD-tema.json SAIDA/pasta
Roteiro JSON: dia (arquivo de achadinhos/dia), capa {linha1, linha2, sub}, produtos [{id, nome, beneficio, foto}],
cta {titulo, sub}. "foto" = índice da foto do anúncio (0-3). As fotos são baixadas para achadinhos/cache/ (fora do git).
Saída: SAIDA/1.jpg, 2.jpg..."""
import json, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1350
AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(AQUI, 'cache')
F_BLACK = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
F_BOLD = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
F_MED = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
TINTA = (24, 22, 28)
AMARELO = (255, 214, 10)
# fundos quentes que se alternam entre os slides de produto
FUNDOS = [(255, 236, 214), (226, 240, 230), (232, 228, 250), (255, 226, 226), (222, 236, 250), (250, 240, 205)]
ASSINATURA = 'Achadinhos do PV'


def fonte(caminho, tam):
    return ImageFont.truetype(caminho, tam)


def foto(produto, idx):
    os.makedirs(CACHE, exist_ok=True)
    idx = min(idx, len(produto['fotos']) - 1)
    destino = os.path.join(CACHE, f"{produto['id']}-{idx}.jpg")
    if not os.path.exists(destino):
        urllib.request.urlretrieve(produto['fotos'][idx], destino)
    return Image.open(destino).convert('RGB')


def quebra(texto, f, largura):
    linhas, atual = [], ''
    for w in texto.split():
        if atual and f.getlength(atual + ' ' + w) > largura:
            linhas.append(atual)
            atual = w
        else:
            atual = (atual + ' ' + w).strip()
    return linhas + [atual]


def cartao(im, lado, raio=44):
    """Foto do anúncio num cartão branco arredondado, com sombra suave."""
    im = ImageOps.fit(im, (lado, lado), Image.LANCZOS)
    mask = Image.new('L', (lado, lado), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, lado - 1, lado - 1], raio, fill=255)
    pad = 60
    out = Image.new('RGBA', (lado + pad * 2, lado + pad * 2), (0, 0, 0, 0))
    sombra = Image.new('L', out.size, 0)
    ImageDraw.Draw(sombra).rounded_rectangle([pad, pad + 18, pad + lado, pad + lado + 18], raio, fill=90)
    out.putalpha(sombra.filter(ImageFilter.GaussianBlur(26)))
    out = Image.composite(Image.new('RGBA', out.size, (40, 30, 30, 255)), Image.new('RGBA', out.size, (0, 0, 0, 0)), out.getchannel('A'))
    out.paste(im, (pad, pad), mask)
    return out, pad


def topo(dr, rotulo, n=None):
    f = fonte(F_BOLD, 30)
    dr.text((70, 74), rotulo.upper(), font=f, fill=TINTA, anchor='lm')
    if n:
        dr.text((W - 70, 74), n, font=f, fill=TINTA, anchor='rm')


def slide_capa(r, produtos):
    base = Image.new('RGB', (W, H), AMARELO)
    dr = ImageDraw.Draw(base, 'RGBA')
    f1 = fonte(F_BLACK, 100)
    y = 120
    for linha in (r['capa']['linha1'], r['capa']['linha2']):
        for l in quebra(linha.upper(), f1, W - 140):
            dr.text((70, y), l, font=f1, fill=TINTA)
            y += 100
    if r['capa'].get('sub'):
        dr.text((72, y + 24), r['capa']['sub'], font=fonte(F_MED, 40), fill=TINTA)
        y += 80
    # três fotos inclinadas abaixo do texto
    y0 = max(y + 60, 560)
    for k, (ang, x, dy) in enumerate([(-9, -40, 40), (7, 600, 0), (-3, 270, 170)]):
        if k >= len(produtos):
            break
        p, cfg = produtos[k]
        c, pad = cartao(foto(p, cfg.get('foto', 0)), 500, 36)
        c = c.rotate(ang, Image.BICUBIC, expand=True)
        base.paste(c, (x - pad, y0 + dy - pad), c)
    dr = ImageDraw.Draw(base, 'RGBA')
    # selo "arrasta"
    fa = fonte(F_BOLD, 34)
    dr.rounded_rectangle([W - 330, H - 130, W - 60, H - 60], 35, fill=TINTA)
    dr.text((W - 195, H - 95), 'ARRASTA  →', font=fa, fill=AMARELO, anchor='mm')
    return base


def slide_produto(p, cfg, i, total, rotulo):
    base = Image.new('RGB', (W, H), FUNDOS[(i - 1) % len(FUNDOS)])
    dr = ImageDraw.Draw(base, 'RGBA')
    topo(dr, rotulo, f'{i}/{total}')
    c, pad = cartao(foto(p, cfg.get('foto', 0)), 800)
    base.paste(c, ((W - 800) // 2 - pad, 120 - pad), c)
    dr = ImageDraw.Draw(base, 'RGBA')
    # número grande sobre o cartão
    fn = fonte(F_BLACK, 70)
    dr.ellipse([70, 960, 190, 1080], fill=TINTA)
    dr.text((130, 1020), str(i), font=fn, fill=AMARELO, anchor='mm')
    fnome = fonte(F_BLACK, 62)
    y = 1044
    for l in quebra(cfg['nome'], fnome, W - 260)[:2]:
        dr.text((215, y), l, font=fnome, fill=TINTA, anchor='ls')
        y += 66
    y += 20
    fb = fonte(F_MED, 36)
    y += 4
    for l in quebra(cfg['beneficio'], fb, W - 140)[:3]:
        dr.text((70, y), l, font=fb, fill=(60, 56, 66))
        y += 46
    return base


def slide_cta(r):
    base = Image.new('RGB', (W, H), TINTA)
    dr = ImageDraw.Draw(base, 'RGBA')
    topo(dr, '', None)
    f = fonte(F_BLACK, 100)
    y = 300
    for l in quebra(r['cta']['titulo'].upper(), f, W - 140):
        dr.text((70, y), l, font=f, fill=(255, 255, 255))
        y += 104
    # balão de comentário com QUERO
    y += 70
    dr.rounded_rectangle([70, y, W - 70, y + 190], 50, fill=(255, 255, 255))
    dr.polygon([(150, y + 185), (130, y + 250), (230, y + 185)], fill=(255, 255, 255))
    dr.ellipse([110, y + 45, 210, y + 145], fill=AMARELO)
    dr.text((160, y + 95), 'V', font=fonte(F_BLACK, 40), fill=TINTA, anchor='mm')
    dr.text((245, y + 72), 'você', font=fonte(F_BOLD, 30), fill=(120, 116, 126), anchor='lm')
    dr.text((245, y + 122), 'QUERO', font=fonte(F_BLACK, 62), fill=TINTA, anchor='lm')
    dr.text((W - 120, y + 95), '♥', font=fonte('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 48), fill=(230, 40, 70), anchor='mm')
    fs = fonte(F_MED, 40)
    y += 320
    for l in quebra(r['cta']['sub'], fs, W - 140):
        dr.text((70, y), l, font=fs, fill=(220, 216, 226))
        y += 54
    dr.text((70, H - 90), ASSINATURA, font=fonte(F_BOLD, 34), fill=AMARELO, anchor='lm')
    return base


def main():
    roteiro, pasta = sys.argv[1], sys.argv[2]
    r = json.load(open(roteiro))
    dia = json.load(open(os.path.join(AQUI, 'dia', r['dia'])))
    por_id = {p['id']: p for p in dia['produtos']}
    produtos = [(por_id[c['id']], c) for c in r['produtos']]
    os.makedirs(pasta, exist_ok=True)
    slides = [slide_capa(r, produtos)]
    slides += [slide_produto(p, c, i + 1, len(produtos), r.get('rotulo', 'achadinhos')) for i, (p, c) in enumerate(produtos)]
    slides.append(slide_cta(r))
    for k, s in enumerate(slides, 1):
        s.save(os.path.join(pasta, f'{k}.jpg'), quality=92)
    print(f'{len(slides)} slides em {pasta}')


if __name__ == '__main__':
    main()
