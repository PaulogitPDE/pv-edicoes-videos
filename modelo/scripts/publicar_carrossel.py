"""Publica um carrossel (2 a 10 JPEGs já commitados em postados-img/) no @pvedicoes.
Uso: python3 modelo/scripts/publicar_carrossel.py legenda.txt postados-img/X-1.jpg postados-img/X-2.jpg ..."""
import json, subprocess, sys, time, urllib.parse

IG = '17841429538755844'
API = 'https://graph.facebook.com/v21.0'
RAW = 'https://raw.githubusercontent.com/PaulogitPDE/pv-edicoes-videos/main/'

def call(method, path, data=None):
    cmd = ['curl', '-sS', '-X', method, f'{API}/{path}']
    for k, v in (data or {}).items():
        cmd += ['--data-urlencode', f'{k}={v}']
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    r = json.loads(out)
    if 'error' in r:
        sys.exit(f'ERRO Meta: {out}')
    return r

def espera(c):
    for _ in range(30):
        s = call('GET', f'{c}?fields=status_code')
        if s.get('status_code') in (None, 'FINISHED'):
            return
        if s['status_code'] == 'ERROR':
            sys.exit(f'ERRO processamento: {s}')
        time.sleep(4)

legenda = open(sys.argv[1], encoding='utf-8').read().strip()
filhos = []
for arq in sys.argv[2:]:
    c = call('POST', f'{IG}/media', {'image_url': RAW + urllib.parse.quote(arq), 'is_carousel_item': 'true'})['id']
    espera(c)
    filhos.append(c)
c = call('POST', f'{IG}/media', {'media_type': 'CAROUSEL', 'children': ','.join(filhos), 'caption': legenda})['id']
espera(c)
m = call('POST', f'{IG}/media_publish', {'creation_id': c})['id']
print(json.dumps(call('GET', f'{m}?fields=permalink,timestamp')))
