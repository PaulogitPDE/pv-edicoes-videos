"""Motor próprio de reels do PV Edições (sem Remotion): desenha cada frame com Pillow/numpy e codifica com ffmpeg.
Uso (na raiz do repo): python3 motor/reel.py modelo/roteiros/AAAA-MM-DD.json postados/AAAA-MM-DD.mp4
Lê o mesmo JSON de roteiro (cenas, destaque, impacto, imagem, tempos, duracao, audio, musica, inicioMusica, assinatura).
Estratégia 22/10: "serie" + "gancho" ficam fixos no topo desde o frame 0 (o espectador sabe na hora de quem é a história);
"pergunta" fecha o vídeo no cartão final (puxa comentário). Sem flash branco no frame 0.
Toda a animação (zoom, tremida, pop das palavras, frase de impacto, linhas de velocidade) é calculada aqui, à mão."""
import json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
POR_PALAVRA, SEGURA, FINAL = 8, 26, 45
VERMELHO, BRANCO = (229, 25, 46), (244, 241, 234)
PUBLIC = os.path.join(os.path.dirname(__file__), '..', 'modelo', 'public')
F_BOLD = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
F_BLACK = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
F_MED = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'


def dur_cena(c):
    if c.get('duracao'):
        return c['duracao']
    n = len(c['texto'].split())
    return round(n * POR_PALAVRA * (1.6 if c.get('impacto') else 1)) + SEGURA + (22 if c.get('impacto') else 0)


def clamp01(x):
    return max(0.0, min(1.0, x))


def lerp(f, a, b, va, vb):
    return va + (vb - va) * clamp01((f - a) / (b - a)) if b != a else vb


def mola(t, damping, mass, stiffness):
    """Mola amortecida (oscilador harmônico), 0→1. t em frames."""
    if t <= 0:
        return 0.0
    ts = t / FPS
    w0 = math.sqrt(stiffness / mass)
    z = damping / (2 * math.sqrt(stiffness * mass))
    if z < 1:
        wd = w0 * math.sqrt(1 - z * z)
        return 1 - math.exp(-z * w0 * ts) * (math.cos(wd * ts) + (z * w0 / wd) * math.sin(wd * ts))
    return 1 - math.exp(-w0 * ts) * (1 + w0 * ts)


def rnd(*k):
    return (hash(k) % 10007) / 10007.0


# ---------- camadas fixas ----------
def vinheta():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.8)) ** 2 + ((y - H / 2) / (H * 0.6)) ** 2)
    a = np.clip((d - 0.4) / 0.6, 0, 1) * 0.92
    return Image.fromarray((a * 255).astype(np.uint8))


def sobreposicao_texto():
    """Escurece a faixa central onde fica o texto (elipse 85% x 35%)."""
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.85)) ** 2 + ((y - H / 2) / (H * 0.35)) ** 2)
    a = np.where(d < 0.7, 0.85 - (0.45 * d / 0.7), np.clip(0.4 + (d - 0.7) / 0.3 * 0.25, 0, 0.65))
    return Image.fromarray((a * 255).astype(np.uint8))


rng = np.random.default_rng(7)
GRAOS = [Image.fromarray((rng.random((H // 2, W // 2)) * 255 * 0.12).astype(np.uint8)).resize((W, H)) for _ in range(6)]
VIN, ESC = vinheta(), sobreposicao_texto()
PRETO = Image.new('RGB', (W, H), (0, 0, 0))
CACHE_IMG = {}


def imagem_pb(src):
    if src not in CACHE_IMG:
        im = Image.open(os.path.join(PUBLIC, src)).convert('L')
        # cobrir 1080x1920 com folga de zoom 1.22
        s = max(W * 1.25 / im.width, H * 1.25 / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        arr = np.asarray(im).astype(np.float32)
        arr = np.clip((arr - 128) * 1.6 + 128, 0, 255) * 0.55  # contraste 1.6, brilho 0.55
        CACHE_IMG[src] = Image.fromarray(arr.astype(np.uint8)).convert('RGB')
    return CACHE_IMG[src]


def linhas(seed, f, forca, cx=540, cy=960):
    lay = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(lay)
    for i in range(120):
        ang = rnd('a', seed, i) * math.pi * 2
        larg = 0.004 + rnd('w', seed, i) * 0.012
        r0 = 520 + rnd('r', seed, i, f // 2) * 260
        p = lambda a, r: (cx + math.cos(a) * r, cy + math.sin(a) * r)
        d.polygon([p(ang - larg, 2000), p(ang + larg, 2000), p(ang, r0)], fill=255)
    return lay.point(lambda v: int(v * min(1, 0.16 + forca * 0.5)))


# ---------- texto ----------
def sprite_palavra(t, tam, cor, impacto=False):
    fonte = ImageFont.truetype(F_BLACK if impacto else F_BOLD, tam)
    t = t.upper()
    bb = fonte.getbbox(t)
    # altura fixa pela métrica da fonte: todas as palavras ficam na mesma linha de base (acentos não descem a palavra)
    asc, desc = fonte.getmetrics()
    bb = (bb[0], 0, bb[2], asc + desc)
    w, h = bb[2] - bb[0] + 60, bb[3] - bb[1] + 60
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sombra = Image.new('L', (w, h), 0)
    ImageDraw.Draw(sombra).text((30 - bb[0] + 5, 30 - bb[1] + 5), t, font=fonte, fill=255)
    brilho = sombra.filter(ImageFilter.GaussianBlur(14))
    im.paste((0, 0, 0, 255), (0, 0), brilho.point(lambda v: int(v * 0.8)))
    if cor == VERMELHO:
        im.paste(VERMELHO + (255,), (0, 0), brilho.point(lambda v: int(v * 0.6)))
    im.paste((0, 0, 0, 255), (0, 0), sombra)
    ImageDraw.Draw(im).text((30 - bb[0], 30 - bb[1]), t, font=fonte, fill=cor + (255,))
    return im, fonte.getlength(t + ' ')


def layout(c):
    palavras = c['texto'].split()
    tam = 150 if len(palavras) <= 2 else 118 if len(palavras) <= 4 else 100
    sprites = [sprite_palavra(p, tam, VERMELHO if p in (c.get('destaque') or []) else BRANCO, c.get('impacto')) for p in palavras]
    sprites = [(sp, adv + tam * 0.1) for sp, adv in sprites]
    linhas_, atual, larg = [], [], 0
    for i, (sp, adv) in enumerate(sprites):
        if atual and larg + adv > W - 180:
            linhas_.append((atual, larg)); atual, larg = [], 0
        atual.append(i); larg += adv
    linhas_.append((atual, larg))
    alt = tam * 1.12
    y0 = H / 2 - alt * len(linhas_) / 2
    pos = {}
    espaco = ImageFont.truetype(F_BLACK if c.get('impacto') else F_BOLD, tam).getlength(' ') + tam * 0.1
    for li, (idx, larg) in enumerate(linhas_):
        x = W / 2 - (larg - espaco) / 2
        for i in idx:
            pos[i] = (x + (sprites[i][0].width - 60) / 2, y0 + li * alt + alt / 2)
            x += sprites[i][1]
    return palavras, sprites, pos, y0 + alt * len(linhas_)


def faixa_topo(serie, gancho):
    """Título fixo no topo: rótulo vermelho (anime · personagem) + gancho em caixa preta. Fica fora da área da UI do IG."""
    fs, fg = ImageFont.truetype(F_MED, 34), ImageFont.truetype(F_BLACK, 60)
    linhas_g, atual = [], ''
    for w in (gancho or '').upper().split():
        if atual and fg.getlength(atual + ' ' + w) > W - 200:
            linhas_g.append(atual); atual = w
        else:
            atual = (atual + ' ' + w).strip()
    if atual:
        linhas_g.append(atual)
    im = Image.new('RGBA', (W, 120 + 72 * len(linhas_g)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 0
    if serie:
        t = serie.upper()
        larg = sum(fs.getlength(ch) + 5 for ch in t)
        x = W / 2 - larg / 2
        d.rectangle([x - 18, 0, x + larg + 12, 52], fill=VERMELHO + (255,))
        for ch in t:
            d.text((x, 6), ch, font=fs, fill=BRANCO + (255,)); x += fs.getlength(ch) + 5
        y = 70
    if linhas_g:
        larg = max(fg.getlength(l) for l in linhas_g)
        d.rectangle([W / 2 - larg / 2 - 28, y, W / 2 + larg / 2 + 28, y + 30 + 72 * len(linhas_g)], fill=(0, 0, 0, 215))
        for i, l in enumerate(linhas_g):
            d.text((W / 2 - fg.getlength(l) / 2, y + 12 + i * 72), l, font=fg, fill=BRANCO + (255,))
    return im


def colar_escala(base, sp, cx, cy, esc, alpha=1.0):
    if esc <= 0.01 or alpha <= 0:
        return
    w, h = max(1, round(sp.width * esc)), max(1, round(sp.height * esc))
    s = sp.resize((w, h), Image.BILINEAR)
    if alpha < 1:
        s.putalpha(s.getchannel('A').point(lambda v: int(v * alpha)))
    base.alpha_composite(s, (round(cx - w / 2), round(cy - h / 2)))


def frame_cena(c, n, f, dur, lay, topo=None):
    palavras, sprites, pos, base_y = lay
    imp = c.get('impacto')
    tempos = c.get('tempos') or [round(i * POR_PALAVRA * (1.6 if imp else 1)) for i in range(len(palavras))]
    ultima = tempos[-1]
    zoom_c = lerp(f, 0, dur, 1.08, 1.0)
    sac = (rnd('s', n, f) - 0.5) * 30 if imp and ultima <= f < ultima + 10 else 0
    # fundo + imagem
    if c.get('imagem'):
        im = imagem_pb(c['imagem'])
        z = lerp(f, 0, dur, 1.22, 1.06)
        pulso = 1 if (f % POR_PALAVRA < 3 and f < len(palavras) * POR_PALAVRA) else 0
        z = z + pulso * 0.02
        tx = (rnd('x', f) - 0.5) * 22 * pulso
        ty = (rnd('y', f) - 0.5) * 22 * pulso
        cw, ch = W / z, H / z
        cx = im.width / 2 - tx / z
        cy = im.height / 2 - ty / z
        if c.get('foco') == 'top':
            cy = ch / 2 + 10
        quadro = im.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
        quadro = Image.composite(PRETO, quadro, ESC)
    else:
        quadro = Image.new('RGB', (W, H), (5, 5, 5))
    quadro = Image.composite(PRETO, quadro, VIN)
    forca = lerp(f, 0, 10, 1, 0) + (lerp(f, len(palavras) * POR_PALAVRA, len(palavras) * POR_PALAVRA + 12, 1, 0.3) if imp else 0)
    quadro.paste(BRANCO, (0, 0), linhas(n, f, min(forca, 1) * (0.6 if c.get('imagem') else 1)))
    quadro.paste((255, 255, 255), (0, 0), GRAOS[f % 6])
    base = quadro.convert('RGBA')
    # palavras
    for i, (sp, _) in enumerate(sprites):
        ini = tempos[i] if i < len(tempos) else i * POR_PALAVRA
        d = f - ini
        if d < 0:
            continue
        cx, cy = pos[i]
        cx += sp.width / 2 - sp.width / 2
        if imp:
            s = mola(d, 9, 0.5, 220)
            esc = 2.8 + (1 - 2.8) * s
            trem = (rnd('ti', i, f) - 0.5) * 26 if d < 8 else 0
            rgb = lerp(d, 0, 10, 18, 0)
            spi = sp if d >= 6 else sp.filter(ImageFilter.GaussianBlur(lerp(d, 0, 6, 10, 0)))
            if rgb > 0.5:
                r, g, b, a = spi.split()
                verm = Image.merge('RGBA', (a, a.point(lambda v: v * 43 // 255), a.point(lambda v: v * 58 // 255), a.point(lambda v: v * 0.7)))
                cia = Image.merge('RGBA', (a.point(lambda v: v * 34 // 255), a.point(lambda v: v * 229 // 255), a, a.point(lambda v: v * 0.5)))
                colar_escala(base, verm, cx - rgb + trem, cy + trem * 0.5, esc)
                colar_escala(base, cia, cx + rgb + trem, cy + trem * 0.5, esc)
            colar_escala(base, spi, cx + trem, cy + trem * 0.5, esc)
        else:
            s = mola(d, 11, 0.6, 180)
            trem = (rnd('t', i, f) - 0.5) * 18 if d < 6 else 0
            colar_escala(base, sp, cx + trem, cy + trem * 0.6, 0.4 + s * 0.6)
    dr = ImageDraw.Draw(base)
    if imp:
        p = clamp01((f - ultima - 4) / 10)
        larg = (1 - (1 - p) ** 3) * 0.7 * (W - 180)
        if larg > 2:
            y = base_y + 30
            x0 = W / 2 - larg / 2
            dr.polygon([(x0 + 5, y), (x0 + larg + 5, y), (x0 + larg - 5, y + 14), (x0 - 5, y + 14)], fill=VERMELHO + (255,))
    if topo is not None:
        base.alpha_composite(topo, (0, 210))
    # moldura de painel
    dr.rectangle([22, 22, W - 23, H - 23], outline=(0, 0, 0, 255), width=14)
    dr.rectangle([36, 36, W - 37, H - 37], outline=BRANCO + (217,), width=5)
    out = base.convert('RGB')
    if imp:
        fl = lerp(f, ultima, ultima + 3, 0, 0.55) if f < ultima + 3 else lerp(f, ultima + 3, ultima + 12, 0.55, 0)
        if fl > 0:
            arr = np.asarray(out).astype(np.float32)
            mult = np.array(VERMELHO, np.float32) / 255
            arr = arr * (1 - fl) + arr * mult * fl
            out = Image.fromarray(arr.astype(np.uint8))
    if zoom_c != 1 or sac:
        cw, ch = W / zoom_c, H / zoom_c
        out = out.resize((W, H), Image.BILINEAR, box=(W / 2 - cw / 2 - sac, H / 2 - ch / 2 - sac * 0.6, W / 2 + cw / 2 - sac, H / 2 + ch / 2 - sac * 0.6))
    flash = lerp(f, 0, 4, 0.85, 0) if n > 0 else 0
    if flash > 0:
        out = Image.blend(out, Image.new('RGB', (W, H), (255, 255, 255)), flash)
    sai = lerp(f, dur - 5, dur, 1, 0)
    if sai < 1:
        out = Image.blend(PRETO, out, sai)
    return out


def frame_final(f, assinatura, sprites):
    quadro = Image.new('RGB', (W, H), (5, 5, 5))
    quadro.paste(BRANCO, (0, 0), linhas(99, f, 0.2))
    quadro.paste((255, 255, 255), (0, 0), GRAOS[f % 6])
    base = quadro.convert('RGBA')
    s = mola(f, 14, 1, 100)
    colar_escala(base, sprites[0], W / 2, H / 2 - 30, 0.6 + s * 0.4, clamp01(s))
    for i, sp in enumerate(sprites[1:]):
        colar_escala(base, sp, W / 2, H / 2 + 80 + i * 66, 1, lerp(f, 6 + i * 3, 14 + i * 3, 0, 1))
    return base.convert('RGB')


def audio(r, total, janelas, saida):
    """Mistura música (com fade e abaixando sob a voz) + narrações por cena. Tudo em numpy."""
    sr = 44100
    n = int(total / FPS * sr)

    def decod(path, inicio=0.0):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(inicio), '-i', path, '-f', 's16le', '-ac', '2', '-ar', str(sr), '-'], capture_output=True).stdout
        return np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768

    mix = np.zeros((n, 2), np.float32)
    if r.get('musica'):
        m = decod(os.path.join(PUBLIC, r['musica']), r.get('inicioMusica') or 0)[:n]
        t = np.arange(len(m)) / sr * FPS  # em frames
        env = np.clip(t / 8, 0, 1) * np.clip((total - t) / 15, 0, 1)
        duck = np.ones_like(t)
        for a, b in janelas:
            dentro = np.interp(t, [a - 6, a, b - 4, b + 2], [1, 0.32, 0.32, 1], left=1, right=1)
            duck = np.minimum(duck, dentro)
        mix[:len(m)] += m * (env * duck * 0.9)[:, None]
    for ini, path in r['_narr']:
        v = decod(os.path.join(PUBLIC, path))
        k = int(ini / FPS * sr)
        v = v[:max(0, n - k)]
        mix[k:k + len(v)] += v
    pico = np.abs(mix).max()
    if pico > 0.98:
        mix *= 0.98 / pico
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ac', '2', '-ar', str(sr), '-i', '-', saida], input=(mix * 32767).astype(np.int16).tobytes(), check=True)


def main():
    rot, saida = sys.argv[1], sys.argv[2]
    r = json.load(open(rot, encoding='utf-8'))
    cenas = r['cenas']
    durs = [dur_cena(c) for c in cenas]
    total = sum(durs) + FINAL
    janelas, narr, ini = [], [], 0
    for c, d in zip(cenas, durs):
        if c.get('audio'):
            janelas.append((ini, ini + d)); narr.append((ini, c['audio']))
        ini += d
    r['_narr'] = narr
    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, 'a.wav')
    audio(r, total, janelas, wav)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                            '-movflags', '+faststart', '-shortest', saida], stdin=subprocess.PIPE)
    topo = faixa_topo(r.get('serie'), r.get('gancho')) if (r.get('serie') or r.get('gancho')) else None
    for n, (c, d) in enumerate(zip(cenas, durs)):
        lay = layout(c)
        for f in range(d):
            enc.stdin.write(frame_cena(c, n, f, d, lay, topo).tobytes())
        print(f'cena {n + 1}/{len(cenas)} ok', flush=True)
    ass = sprite_palavra(r.get('assinatura', '@pvedicoes'), 96, BRANCO)[0]
    linhas_p, atual = [], ''
    for w in (r.get('pergunta') or 'SALVA E MANDA PRA QUEM PRECISA').split():
        if atual and len(atual) + len(w) > 24:
            linhas_p.append(atual); atual = w
        else:
            atual = (atual + ' ' + w).strip()
    linhas_p.append(atual)
    cta = [sprite_palavra(l, 44, VERMELHO)[0] for l in linhas_p]
    for f in range(FINAL):
        enc.stdin.write(frame_final(f, None, [ass] + cta).tobytes())
    enc.stdin.close()
    enc.wait()
    print('ok', saida, f'{total / FPS:.1f} s')


if __name__ == '__main__':
    main()
