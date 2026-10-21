"""Posts de imagem do @crmquevende (1080x1350), no mesmo visual dos reels: fundo escuro com grade, bolinhas neon,
destaque lime com brilho, cartões de vidro e um rodapé com CTA.
Uso (na raiz do repo): python3 crm/motor/post.py crm/posts/AAAA-MM-DD-p1.json crm/postados-img/AAAA-MM-DD-p1.jpg

JSON: {"layout": "frase|data|chat|numero|lista|antes_depois", "rotulo": "...", "headline": "Texto com <destaque>",
"sub": "...", "cta": "direct|bio|comenta", "palavra": "FUNIL", "rabisco": "sublinha|circulo", ...campos do layout}"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from base import *  # noqa: E402,F403
from reel import balao, avatar, notificacao, _calendario, cartao_lead  # noqa: E402

W, H = 1080, 1350


def fundo(semente):
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.9)) ** 2 + ((y - H * 0.45) / (H * 0.6)) ** 2)
    t = np.clip(d / 0.8, 0, 1)[..., None]
    arr = np.array(BG2, np.float32) * (1 - t) + np.array(BG, np.float32) * t
    g = np.clip(1 - d / 0.5, 0, 1)[..., None] * 0.07
    arr = arr * (1 - g) + np.array(LIME, np.float32) * g
    grade = ((x % 90) < 2) | ((y % 90) < 2)
    arr[grade] = arr[grade] * 0.86 + 255 * 0.035
    base = Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
    for i in range(16):
        cor = [LIME, LIME, CIANO, ROSA][i % 4]
        colar(base, neon(cor, 3 + int(rnd('r', semente, i) * 4)), rnd('x', semente, i) * W, rnd('y', semente, i) * H,
              alpha=0.3 + 0.7 * rnd('a', semente, i))
    return base


def rodape(base, p):
    colar(base, rotulo('@crmquevende', 24, MUTED, 4), 70, H - 92, canto=True)
    cta = p.get('cta', 'direct')
    pal = limpa(p.get('palavra', 'FUNIL')).upper()
    txt = {'direct': f'Manda {pal} no Direct', 'bio': 'Link na bio', 'comenta': f'Comenta {pal}'}.get(cta, cta)
    f = corpo('black', 30)
    t = limpa(txt).upper()
    w = int(f.getlength(t)) + 64
    pil = cartao(w, 66, 33, LIME + (255,), None, 18, 0, LIME).copy()
    pad = (pil.width - w) // 2
    ImageDraw.Draw(pil).text((pad + 32, pad + 14), t, font=f, fill=BG + (255,))
    colar(base, pil, W - 70 - w / 2, H - 80)


def headline(base, p, cy, tam=None, max_w=930):
    txt = p['headline']
    n = len(runs(limpa(txt)))
    tam = tam or p.get('tam') or (118 if n <= 4 else 96 if n <= 8 else 80 if n <= 13 else 68)
    t = Texto(txt, tam, max_w=max_w)
    t.draw(base, W / 2, cy, 99, 0, 'fixo')
    if p.get('rabisco'):
        cor = VERMELHO if p['rabisco'] == 'x' else LIME
        traco(base, forma(p['rabisco'], *t.caixa_dest(W / 2, cy), semente=len(txt)), 1, cor, 9, ponta=False)
    return t


def topo(base, p, y=150):
    if p.get('rotulo'):
        colar(base, rotulo(p['rotulo'], 28, CORES.get(p.get('cor_rotulo', 'lime'), LIME), 5), W / 2, y)


def sub(base, p, y, cor=MUTED):
    if p.get('sub'):
        sp = texto_simples(p['sub'], 38, 'semi', cor, 860, centro=True)
        colar(base, sp, W / 2, y + sp.height / 2)
        return sp.height
    return 0


def l_frase(base, p):
    topo(base, p, 260)
    t = headline(base, p, 560)
    sub(base, p, 560 + t.alt / 2 + 70)


def l_data(base, p):
    cal = _calendario(str(p['dia']), limpa(p['mes']).upper())
    colar(base, cal, W / 2, 330, 0.75, rot=-4)
    for k in range(18):
        ang = k / 18 * math.pi * 2
        colar(base, neon([LIME, CIANO, ROSA][k % 3], 4), W / 2 + math.cos(ang) * (260 + rnd('d', k) * 90), 330 + math.sin(ang) * (230 + rnd('e', k) * 60))
    t = headline(base, p, 780, max_w=960)
    sub(base, p, 780 + t.alt / 2 + 50, TXT)


def l_chat(base, p):
    t = headline(base, p, 250)
    X0, Y0, X1, Y1 = 110, 250 + t.alt / 2 + 60, 970, 1160
    colar(base, cartao(X1 - X0, int(Y1 - Y0), 34, (17, 23, 33, 245)), W / 2, (Y0 + Y1) / 2)
    nome = p.get('nome', 'Paciente')
    colar(base, avatar(nome[0].upper(), CORES.get(p.get('cor', 'rosa'), ROSA), 32), X0 + 60, Y0 + 56)
    colar(base, palavra(nome, 34, 'bold', TXT, False, False), X0 + 104, Y0 + 20, canto=True)
    colar(base, palavra(limpa(p.get('status', 'online')), 22, 'med', MUTED, False, False), X0 + 104, Y0 + 58, canto=True)
    y = Y0 + 130
    for m in p['mensagens']:
        ela = m.get('de', 'ela') != 'eu'
        sp = balao(m['texto'], 'ela' if ela else 'eu', m.get('meta', ''))
        colar(base, sp, X0 + 30 if ela else X1 - 30 - sp.width, y, canto=True)
        y += sp.height + 18
    if p.get('carimbo'):
        from reel import carimbo
        colar(base, carimbo(p['carimbo'], CORES.get(p.get('cor_carimbo', 'vermelho'), VERMELHO)), W / 2, min(Y1 - 120, y + 90), 0.85)


def l_numero(base, p):
    topo(base, p, 250)
    cor = CORES.get(p.get('cor', 'lime'), LIME)
    txt = limpa(p['numero'])
    sp = palavra(txt, 250 if len(txt) <= 5 else 180, 'black', cor, True)
    cy = 520
    colar(base, sp, W / 2, cy)
    pts = [(W / 2 + math.cos(-math.pi / 2 + a / 60 * math.pi * 2) * 400, cy + math.sin(-math.pi / 2 + a / 60 * math.pi * 2) * 200) for a in range(61)]
    traco(base, pts, 0.92, cor, 6, ponta=True)
    t = headline(base, p, 870, max_w=940)
    sub(base, p, 870 + t.alt / 2 + 50)


def l_lista(base, p):
    t = headline(base, p, 230)
    y = 230 + t.alt / 2 + 70
    for it in p['itens']:
        ok = it.get('ok', True)
        sp = texto_simples(it['t'], 38, 'semi', TXT, 720)
        h = max(118, sp.height + 50)
        colar(base, cartao(920, h, 24, (24, 32, 46, 240), (255, 255, 255, 30), 20), W / 2, y + h / 2)
        bx = 140
        colar(base, cartao(56, 56, 14, (12, 16, 24, 255), ((198, 255, 61, 200) if ok else (255, 92, 92, 200)), 0, 3), bx, y + h / 2)
        traco(base, forma('check' if ok else 'x', bx - 15, y + h / 2 - 13, bx + 15, y + h / 2 + 13), 1, LIME if ok else VERMELHO, 7, ponta=False)
        colar(base, sp, bx + 52, y + h / 2 - sp.height / 2, canto=True)
        y += h + 22


def l_antes_depois(base, p):
    t = headline(base, p, 220)
    y0 = 220 + t.alt / 2 + 70
    for k, (lado, cor, titulo) in enumerate([('antes', VERMELHO, p.get('titulo_antes', 'Sem follow-up')), ('depois', LIME, p.get('titulo_depois', 'Com follow-up'))]):
        cx = 300 + k * 480
        itens = p[lado]
        h = 140 + len(itens) * 120
        colar(base, cartao(440, h, 28, (20, 28, 40, 245), cor + (140,), 26, 2, cor), cx, y0 + h / 2)
        colar(base, rotulo(titulo, 26, cor, 4), cx, y0 + 60)
        for i, it in enumerate(itens):
            yy = y0 + 140 + i * 120
            traco(base, forma('check' if lado == 'depois' else 'x', cx - 190, yy - 12, cx - 162, yy + 12), 1, cor, 6, ponta=False)
            colar(base, texto_simples(it, 32, 'semi', TXT, 330), cx - 140, yy - 20, canto=True)


def main():
    p = json.load(open(sys.argv[1], encoding='utf-8'))
    base = fundo(len(p.get('headline', '')))
    globals()['l_' + p.get('layout', 'frase')](base, p)
    rodape(base, p)
    ImageDraw.Draw(base).rectangle([0, 0, W, 7], fill=LIME + (255,))
    base.convert('RGB').save(sys.argv[2], quality=93)
    print('ok', sys.argv[2])


if __name__ == '__main__':
    main()
