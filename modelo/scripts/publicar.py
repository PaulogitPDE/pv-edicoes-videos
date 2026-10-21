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
def criar():
    c = call('POST', f'{IG}/media', {'media_type': 'REELS', 'video_url': url, 'caption': legenda, 'share_to_feed': 'true'})['id']
    for _ in range(40):
        s = call('GET', f'{c}?fields=status_code,status')
        if s['status_code'] == 'FINISHED':
            return c
        if s['status_code'] == 'ERROR':
            print(f'aviso: falha no processamento {s}', file=sys.stderr)
            return None
        time.sleep(10)
    sys.exit('ERRO: vídeo não terminou de processar em ~7 min')

# O Instagram às vezes falha ao baixar o vídeo (ex.: código 2207077); tenta de novo até 3 vezes.
for tentativa in range(3):
    c = criar()
    if c:
        break
    time.sleep(30)
else:
    sys.exit('ERRO: o Instagram recusou o vídeo 3 vezes')
m = call('POST', f'{IG}/media_publish', {'creation_id': c})['id']
print(json.dumps(call('GET', f'{m}?fields=permalink,timestamp')))
