"""Publica um JPEG já commitado em postados-img/ como post de imagem (feed) no @pvedicoes.
Uso: python3 modelo/scripts/publicar_imagem.py postados-img/ARQUIVO.jpg legenda.txt"""
import json, subprocess, sys, time, urllib.parse

IG = '17841429538755844'
API = 'https://graph.facebook.com/v21.0'

def call(method, path, data=None):
    cmd = ['curl', '-sS', '-X', method, f'{API}/{path}']
    for k, v in (data or {}).items():
        cmd += ['--data-urlencode', f'{k}={v}']
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    r = json.loads(out)
    if 'error' in r:
        sys.exit(f'ERRO Meta: {out}')
    return r

arquivo, legenda = sys.argv[1], open(sys.argv[2], encoding='utf-8').read().strip()
url = 'https://raw.githubusercontent.com/PaulogitPDE/pv-edicoes-videos/main/' + urllib.parse.quote(arquivo)
c = call('POST', f'{IG}/media', {'image_url': url, 'caption': legenda})['id']
for _ in range(20):
    s = call('GET', f'{c}?fields=status_code')
    if s.get('status_code') in (None, 'FINISHED'):
        break
    if s['status_code'] == 'ERROR':
        sys.exit(f'ERRO processamento: {s}')
    time.sleep(5)
m = call('POST', f'{IG}/media_publish', {'creation_id': c})['id']
print(json.dumps(call('GET', f'{m}?fields=permalink,timestamp')))
