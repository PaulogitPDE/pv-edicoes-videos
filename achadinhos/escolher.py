"""Seletor de achadinhos do Mercado Livre (estratégia 30/10).
Uso (na raiz do repo): python3 achadinhos/escolher.py [tema] [quantos]   -> achadinhos/dia/AAAA-MM-DD-tema.json
Precisa de ML_CLIENT_ID e ML_CLIENT_SECRET no ambiente (token de app, client_credentials).

O que a API libera com token de app (teste 31/10): /highlights (mais vendidos por categoria), /products/{id}
(nome, fotos, destaques, marca), /products/{id}/items (ofertas: preço, preço "de", frete, vendedor) e /users/{id}
(reputação). Avaliações (/reviews) e /items dão 403, então nota e nº de avaliações NÃO são checados aqui:
o "mais vendido da categoria" entra como prova de volume de vendas, e o vendedor precisa ser forte.

Filtros anti-golpe (todos obrigatórios):
- produto de catálogo com marca de verdade (nada de "genérica"/"sem marca") e fora das categorias de risco;
- eletrônico (temas tech/setup) só de marca conhecida e loja oficial;
- oferta nova, com vendedor termômetro verde (5_green) E (loja oficial OU MercadoLíder com 1.000+ vendas);
- frete grátis ou Full;
- desconto só aparece se o preço "de" não subiu nos últimos 14 dias (histórico em achadinhos/precos.json);
- produto não repetido nos últimos 14 dias (achadinhos/usados.json).
"""
import datetime as dt
import json, os, sys, urllib.parse, urllib.request

API = 'https://api.mercadolibre.com'
AQUI = os.path.dirname(os.path.abspath(__file__))
AFILIADO = {'matt_word': 'paulovitorlemes', 'matt_tool': '37931087'}

# tema -> categorias (mais vendidos de cada uma)
TEMAS = {
    'casa': ['MLB1618', 'MLB436414', 'MLB264051', 'MLB1613', 'MLB1631'],
    'cozinha': ['MLB1618', 'MLB438284'],
    'tech': ['MLB3813', 'MLB454379', 'MLB430918', 'MLB417704'],
    'setup': ['MLB447778', 'MLB454379', 'MLB14370', 'MLB1582'],
    'beleza': ['MLB1263', 'MLB199407', 'MLB1248', 'MLB439347'],
    'carro': ['MLB5672'],
}
# domínios e palavras de risco (suplemento, remédio, réplica, arma, adulto, eletrônico de procedência duvidosa)
RISCO = ['SUPPLEMENT', 'MEDICINE', 'DRUG', 'VITAMIN', 'PROTEIN', 'CREATINE', 'WEAPON', 'KNIFE', 'SEXUAL',
         'CIGARET', 'VAPE', 'TV_BOX', 'STREAMING_MEDIA', 'REPLICA', 'CELLPHONES', 'NOTEBOOKS', 'GIFT_CARD']
PALAVRAS_RISCO = ['réplica', 'replica', 'primeira linha', 'inspired', 'similar', 'tv box', 'desbloqueado',
                  'emagrec', 'remédio', 'suplemento', 'cbd']
MARCA_RUIM = {'', 'genérica', 'generica', 'genérico', 'generico', 'sem marca', 'outros', 'outra', 'nenhuma', 'n/a'}
ELETRONICOS = set(TEMAS['tech'] + TEMAS['setup']) - {'MLB1582'}
# eletrônico só de marca conhecida (evita clone de smartwatch/fone de marca própria de importador)
MARCAS_ELETRONICOS = {'logitech', 'huawei', 'xiaomi', 'redmi', 'samsung', 'jbl', 'philips', 'multilaser', 'baseus',
                      'anker', 'ugreen', 'redragon', 'havit', 'intelbras', 'positivo', 'amazfit', 'edifier', 'qcy',
                      'lenovo', 'tp-link', 'kingston', 'sandisk', 'apple', 'motorola', 'sony', 'elgin', 'geonav',
                      'i2go', 'haylou', 'rapoo', 'hp', 'dell', 'asus', 'acer', 'lg', 'aoc', 'hyperx', 'razer',
                      'corsair', 'mondial', 'c3tech', 'soundcore', 'kwg', 'goldentec', 'mi', 'oneplus', 'realme'}
MIN_VENDAS_VENDEDOR = 1000
DIAS_SEM_REPETIR = 14

_tok = None
_vendedores = {}


def token():
    global _tok
    if not _tok:
        dados = urllib.parse.urlencode({'grant_type': 'client_credentials', 'client_id': os.environ['ML_CLIENT_ID'],
                                        'client_secret': os.environ['ML_CLIENT_SECRET']}).encode()
        with urllib.request.urlopen(urllib.request.Request(API + '/oauth/token', dados), timeout=30) as r:
            _tok = json.load(r)['access_token']
    return _tok


def get(caminho):
    req = urllib.request.Request(API + caminho, headers={'Authorization': 'Bearer ' + token()})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError:
        return None


def vendedor(uid):
    if uid not in _vendedores:
        _vendedores[uid] = get(f'/users/{uid}') or {}
    return _vendedores[uid]


def ler(nome, padrao):
    try:
        with open(os.path.join(AQUI, nome)) as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return padrao


def salvar(nome, dados):
    with open(os.path.join(AQUI, nome), 'w') as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)


def link_afiliado(pid):
    return f'https://www.mercadolivre.com.br/p/{pid}?' + urllib.parse.urlencode(AFILIADO)


def oferta_segura(o, exige_loja_oficial=False):
    """Devolve o motivo da recusa, ou None se a oferta passa."""
    if o.get('condition') != 'new':
        return 'não é novo'
    sh = o.get('shipping') or {}
    if not (sh.get('free_shipping') or sh.get('logistic_type') == 'fulfillment'):
        return 'sem frete grátis/Full'
    v = vendedor(o['seller_id'])
    rep = v.get('seller_reputation') or {}
    if rep.get('level_id') != '5_green':
        return 'vendedor sem termômetro verde'
    if o.get('official_store_id'):
        return None
    if exige_loja_oficial:
        return 'eletrônico fora de loja oficial'
    if not rep.get('power_seller_status'):
        return 'vendedor não é MercadoLíder nem loja oficial'
    if (rep.get('transactions') or {}).get('total', 0) < MIN_VENDAS_VENDEDOR:
        return f'vendedor com menos de {MIN_VENDAS_VENDEDOR} vendas'
    return None


def avaliar(pid, posicao, categoria, precos, hoje):
    p = get(f'/products/{pid}')
    if not p or p.get('status') != 'active':
        return None, 'produto inativo'
    texto = (p.get('name', '') + ' ' + p.get('family_name', '')).lower()
    if any(r in (p.get('domain_id') or '') for r in RISCO) or any(w in texto for w in PALAVRAS_RISCO):
        return None, 'categoria de risco'
    attrs = {a['id']: a.get('value_name') or '' for a in p.get('attributes', [])}
    if attrs.get('BRAND', '').strip().lower() in MARCA_RUIM:
        return None, 'sem marca'
    eletronico = categoria in ELETRONICOS
    if eletronico and attrs.get('BRAND', '').strip().lower() not in MARCAS_ELETRONICOS:
        return None, 'eletrônico de marca desconhecida'
    if not p.get('pictures'):
        return None, 'sem foto'
    ofertas = (get(f'/products/{pid}/items') or {}).get('results', [])
    boas = []
    for o in sorted(ofertas, key=lambda o: o['price']):
        motivo = oferta_segura(o, eletronico)
        if not motivo:
            boas.append(o)
            if len(boas) == 1 and o.get('official_store_id'):
                break
    if not boas:
        return None, 'nenhum vendedor confiável'
    o = boas[0]
    v = vendedor(o['seller_id'])
    rep = v['seller_reputation']
    # histórico de preço: registra hoje e checa se o preço "de" é inflado
    hist = precos.setdefault(pid, {})
    hist[hoje] = o['price']
    antes = [pr for d, pr in hist.items() if d != hoje and d >= (dt.date.fromisoformat(hoje) - dt.timedelta(days=14)).isoformat()]
    de = o.get('original_price')
    desconto = None
    if de and de > o['price']:
        # desconto real: o "de" não pode estar acima do que o produto custou nos últimos 14 dias
        if not antes or de <= max(antes) * 1.02:
            desconto = round(100 * (1 - o['price'] / de))
    return {
        'id': pid,
        'posicao_mais_vendidos': posicao,
        'categoria': categoria,
        'nome': p['name'],
        'marca': attrs.get('BRAND'),
        'destaques': [f['text'] for f in p.get('main_features', [])][:4],
        'fotos': [f['url'] for f in p['pictures'][:4]],
        'preco': o['price'],
        'preco_de': de if desconto else None,
        'desconto_pct': desconto,
        'desconto_verificado': bool(desconto and antes),
        'frete': 'Full' if o['shipping'].get('logistic_type') == 'fulfillment' else 'grátis',
        'vendedor': v.get('nickname'),
        'loja_oficial': bool(o.get('official_store_id')),
        'mercadolider': rep.get('power_seller_status'),
        'vendas_vendedor': rep.get('transactions', {}).get('total'),
        'ofertas_no_catalogo': len(ofertas),
        'link': link_afiliado(pid),
    }, None


def main():
    tema = sys.argv[1] if len(sys.argv) > 1 else 'casa'
    quantos = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    hoje = dt.date.today().isoformat()
    precos = ler('precos.json', {})
    usados = ler('usados.json', {})
    limite = (dt.date.today() - dt.timedelta(days=DIAS_SEM_REPETIR)).isoformat()
    recentes = {pid for pid, d in usados.items() if d >= limite}

    candidatos = []  # intercala as categorias para variar o carrossel
    listas = []
    for cat in TEMAS[tema]:
        h = get(f'/highlights/MLB/category/{cat}') or {}
        listas.append([(c['id'], c['position'], cat) for c in h.get('content', []) if c.get('type') == 'PRODUCT'][:15])
    for i in range(max(map(len, listas), default=0)):
        candidatos += [l[i] for l in listas if i < len(l)]

    aprovados, recusas = [], []
    for pid, pos, cat in candidatos:
        if len(aprovados) >= quantos:
            break
        if pid in recentes or any(a['id'] == pid for a in aprovados):
            continue
        item, motivo = avaliar(pid, pos, cat, precos, hoje)
        if item:
            aprovados.append(item)
        else:
            recusas.append({'id': pid, 'motivo': motivo})
        print(('OK  ' if item else '--  ') + pid + ' ' + (item['nome'][:60] if item else motivo), file=sys.stderr)

    salvar('precos.json', precos)
    os.makedirs(os.path.join(AQUI, 'dia'), exist_ok=True)
    saida = os.path.join(AQUI, 'dia', f'{hoje}-{tema}.json')
    with open(saida, 'w') as f:
        json.dump({'data': hoje, 'tema': tema, 'produtos': aprovados, 'recusados': recusas}, f, ensure_ascii=False, indent=1)
    print(saida)


if __name__ == '__main__':
    main()
