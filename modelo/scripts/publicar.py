"""Publica um MP4 já commitado em postados/ como Reel no @pvedicoes.
Uso: python3 modelo/scripts/publicar.py postados/ARQUIVO.mp4 legenda.txt"""
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
c = call('POST', f'{IG}/media', {'media_type': 'REELS', 'video_url': url, 'caption': legenda, 'share_to_feed': 'true'})['id']
for _ in range(40):
    s = call('GET', f'{c}?fields=status_code,status')
    if s['status_code'] == 'FINISHED':
        break
    if s['status_code'] == 'ERROR':
        sys.exit(f'ERRO processamento: {s}')
    time.sleep(10)
else:
    sys.exit('ERRO: vídeo não terminou de processar em ~7 min')
m = call('POST', f'{IG}/media_publish', {'creation_id': c})['id']
print(json.dumps(call('GET', f'{m}?fields=permalink,timestamp')))
