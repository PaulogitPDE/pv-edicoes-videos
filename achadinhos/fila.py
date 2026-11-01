"""Monta a fila de ofertas do grupo de WhatsApp (formato em whatsapp/README.md).
Uso (na raiz do repo): python3 achadinhos/fila.py AAAA-MM-DD achadinhos/dia/X.json [achadinhos/dia/Y.json ...] [--textos T.json]
Pega até 8 produtos aprovados pelo escolher.py, alternando os temas, fora dos usados nos últimos 14 dias,
e grava achadinhos/fila/AAAA-MM-DD.json. --textos = {id: {emoji, titulo, modelo, specs}} escritos pela rotina (ex.: 🖱️, "Mouse gamer sem fio",
"Logitech G305", "Sem fio - 12.000 DPI - Preto"); sem ele usa o nome do anúncio e marca/modelo.
Também gera a arte de cada oferta em achadinhos/ofertas/DATA/ (commitar e dar push na main antes do envio). Marca os escolhidos em achadinhos/usados.json."""
import datetime as dt
import json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAW = 'https://raw.githubusercontent.com/PaulogitPDE/pv-edicoes-videos/main/'
HORAS = ['09:00', '11:00', '13:00', '15:00', '18:00', '19:30', '20:30', '21:30']
DIAS_SEM_REPETIR = 14


def brl(v):
    return 'R$ ' + f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def curto(nome, n=60):
    return nome if len(nome) <= n else nome[:n].rsplit(' ', 1)[0].rstrip(' -,|')


def texto(p, t):
    """Formato pedido pelo usuário em 01/11 (modelo de grupo de ofertas):
    emoji + TÍTULO em caixa alta, marca e modelo, specs curtas, De riscado / Por, link e aviso."""
    titulo = (t.get('titulo') or curto(p['nome'], 50)).upper()
    emoji = t.get('emoji', '🔥')
    modelo = t.get('modelo') or ' '.join(x for x in (p.get('marca'), p.get('modelo')) if x)
    specs = t.get('specs', '')
    linhas = [f'{emoji} *{titulo}*', '']
    if modelo:
        linhas += [f'*{modelo}*', '']
    if specs:
        linhas += [specs, '']
    if p.get('preco_de') and p['preco_de'] > p['preco']:
        linhas.append(f"~De: {brl(p['preco_de'])}~")
    linhas += [f"*Por: {brl(p['preco'])}*", '', 'Link para compra:', p['link'], '',
               '📌 Anúncio | Preços podem subir rapidamente']
    return '\n'.join(linhas)


def arte(p, data):
    """Foto do produto recortada sobre fundo amarelo, com a marca Achadinhos do PV embaixo (1080x1080).
    Grava em achadinhos/ofertas/DATA/ID.jpg e devolve a URL raw da main (precisa de push antes do envio)."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    import numpy as np, urllib.request
    S = 1080
    cache = os.path.join(AQUI, 'cache', f"{p['id']}-0.jpg")
    if not os.path.exists(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        urllib.request.urlretrieve(p['fotos'][0], cache)
    foto = Image.open(cache).convert('RGB')
    arr = np.asarray(foto).astype(np.int16)
    # fundo = região clara e sem cor (branco e a sombra cinza do anúncio) ligada à borda da foto
    claro = Image.fromarray(((arr.min(-1) > 190) & (arr.max(-1) - arr.min(-1) < 14)).astype(np.uint8) * 255).copy()
    w, h = claro.size
    for xy in [(x, y) for x in range(0, w, 15) for y in (0, h - 1)] + [(x, y) for y in range(0, h, 15) for x in (0, w - 1)]:
        if claro.getpixel(xy) == 255:
            ImageDraw.floodfill(claro, xy, 128)
    alfa = np.where(np.asarray(claro) == 128, 0, 255).astype(np.uint8)
    rec = foto.convert('RGBA')
    rec.putalpha(Image.fromarray(alfa).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1)))
    rec = rec.crop(rec.getbbox() or (0, 0, foto.width, foto.height))
    esc = min(800 / rec.width, 760 / rec.height)
    rec = rec.resize((int(rec.width * esc), int(rec.height * esc)), Image.LANCZOS)
    fundo = Image.new('RGBA', (S, S), (240, 200, 60, 255))
    x, y = (S - rec.width) // 2, (S - 150 - rec.height) // 2 + 30
    sombra = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    sombra.paste((120, 90, 0, 110), (x + 14, y + 24), rec.getchannel('A'))
    fundo = Image.alpha_composite(fundo, sombra.filter(ImageFilter.GaussianBlur(22)))
    fundo.alpha_composite(rec, (x, y))
    d = ImageDraw.Draw(fundo)
    f = ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf', 54)
    d.text((S // 2, S - 80), 'Achadinhos do PV', font=f, fill=(255, 255, 255, 230), anchor='mm')
    destino = os.path.join(AQUI, 'ofertas', data, f"{p['id']}.jpg")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    fundo.convert('RGB').save(destino, quality=90)
    return RAW + f"achadinhos/ofertas/{data}/{p['id']}.jpg"


def main():
    args = sys.argv[1:]
    textos = {}
    if '--textos' in args:
        i = args.index('--textos')
        textos = json.load(open(args[i + 1]))
        del args[i:i + 2]
    data, arquivos = args[0], args[1:]
    usados_path = os.path.join(AQUI, 'usados.json')
    usados = json.load(open(usados_path)) if os.path.exists(usados_path) else {}
    limite = (dt.date.fromisoformat(data) - dt.timedelta(days=DIAS_SEM_REPETIR)).isoformat()
    listas = [json.load(open(a))['produtos'] for a in arquivos]
    escolhidos, vistos = [], set()
    for k in range(max(map(len, listas), default=0)):
        for l in listas:
            if k < len(l) and len(escolhidos) < len(HORAS):
                p = l[k]
                if p['id'] in vistos or usados.get(p['id'], '') >= limite:
                    continue
                vistos.add(p['id'])
                escolhidos.append(p)
    ofertas = [{'id': p['id'], 'hora': h, 'imagem': arte(p, data), 'texto': texto(p, textos.get(p['id'], {}))}
               for p, h in zip(escolhidos, HORAS)]
    for p in escolhidos:
        usados[p['id']] = data
    json.dump(usados, open(usados_path, 'w'), ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(AQUI, 'fila'), exist_ok=True)
    saida = os.path.join(AQUI, 'fila', f'{data}.json')
    json.dump({'data': data, 'ofertas': ofertas}, open(saida, 'w'), ensure_ascii=False, indent=1)
    print(f'{len(ofertas)} ofertas em {saida}')


if __name__ == '__main__':
    main()
