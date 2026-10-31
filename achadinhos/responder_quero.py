"""Responde quem comentou QUERO nos posts de achadinhos do @pvedicoes: manda no Direct (resposta privada) os links
do post e o link do grupo, e responde o comentário em público ("Te mandei no Direct!").
Uso (na raiz do repo): python3 achadinhos/responder_quero.py [--teste]   (--teste só lista, não envia)
achadinhos/postados.json: {media_id: {roteiro, dia}} gravado quando o carrossel é publicado.
achadinhos/respondidos.json: ids de comentários já respondidos (commitar depois de rodar, para não repetir).
A resposta privada só funciona até 7 dias depois do comentário e uma vez por comentário."""
import json, os, sys, urllib.parse, urllib.request

IG = '17841429538755844'
PAGINA = '1296775513530226'
API = 'https://graph.facebook.com/v21.0'
AQUI = os.path.dirname(os.path.abspath(__file__))
GRUPO = os.environ.get('ACHADINHOS_GRUPO_LINK', '')  # link de convite do grupo de WhatsApp


def req(metodo, caminho, dados=None, token=None):
    url = f'{API}/{caminho}'
    corpo = None
    if token:
        url += ('&' if '?' in url else '?') + 'access_token=' + token
    if dados is not None:
        corpo = json.dumps(dados).encode()
    r = urllib.request.Request(url, corpo, method=metodo, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        return {'error': e.read().decode()}


def ler(nome, padrao):
    try:
        return json.load(open(os.path.join(AQUI, nome)))
    except (FileNotFoundError, ValueError):
        return padrao


def mensagem(info):
    r = json.load(open(os.path.join(AQUI, 'roteiros', info['roteiro'])))
    dia = {p['id']: p for p in json.load(open(os.path.join(AQUI, 'dia', r['dia'])))['produtos']}
    linhas = ['Oi! Aqui estão os links dos achadinhos 👇', '']
    for i, c in enumerate(r['produtos'], 1):
        linhas += [f"{i}. {c['nome']}", dia[c['id']]['link'], '']
    if GRUPO:
        linhas += ['Promoções todo dia no nosso grupo de WhatsApp:', GRUPO]
    return '\n'.join(linhas).strip()


def main():
    teste = '--teste' in sys.argv
    postados = ler('postados.json', {})
    respondidos = set(ler('respondidos.json', []))
    contas = req('GET', 'me/accounts?fields=id,access_token')
    token_pagina = next(a['access_token'] for a in contas['data'] if a['id'] == PAGINA)
    novos = 0
    for media_id, info in postados.items():
        coments = req('GET', f'{media_id}/comments?fields=id,text,username,timestamp&limit=100')
        for c in coments.get('data', []):
            if c['id'] in respondidos or 'quero' not in c.get('text', '').lower():
                continue
            print(f"QUERO de @{c.get('username')} ({c['id']})")
            if teste:
                continue
            r = req('POST', f'{PAGINA}/messages', {'recipient': {'comment_id': c['id']}, 'message': {'text': mensagem(info)}},
                    token_pagina)
            if 'error' in r:
                print('  erro no Direct:', r['error'][:300])
                continue
            req('POST', f"{c['id']}/replies?message=" + urllib.parse.quote('Te mandei no Direct! 📩'))
            respondidos.add(c['id'])
            novos += 1
    if not teste:
        json.dump(sorted(respondidos), open(os.path.join(AQUI, 'respondidos.json'), 'w'), indent=1)
    print(f'{novos} respondidos')


if __name__ == '__main__':
    main()
