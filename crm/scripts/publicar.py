"""Publica no @crmquevende um MP4 (Reel) ou JPG (post de imagem) que já foi commitado e enviado (git push).
Uso (na raiz do repo): python3 crm/scripts/publicar.py crm/postados/ARQUIVO.mp4 crm/roteiros/ARQUIVO.txt
Carrossel: passar 2 a 10 JPGs e a legenda por último (python3 crm/scripts/publicar.py a.jpg b.jpg c.jpg legenda.txt).
O Instagram baixa o arquivo pelo link raw do commit atual (funciona em qualquer branch do repositório público)."""
import json, subprocess, sys, time, urllib.parse

IG = '17841477784714532'  # @crmquevende (Página "CRM  Que Vende" 1053653491172442)
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


arquivos, legenda = sys.argv[1:-1], open(sys.argv[-1], encoding='utf-8').read().strip()
arquivo = arquivos[0]
sha = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
if subprocess.run(['git', 'branch', '-r', '--contains', sha], capture_output=True, text=True).stdout.strip() == '':
    sys.exit('ERRO: faça git push antes de publicar (o commit atual não está no GitHub)')
raw = lambda a: f'https://raw.githubusercontent.com/PaulogitPDE/pv-edicoes-videos/{sha}/' + urllib.parse.quote(a)
url = raw(arquivo)
video = arquivo.endswith('.mp4')


def criar():
    if len(arquivos) > 1:
        filhos = [call('POST', f'{IG}/media', {'image_url': raw(a), 'is_carousel_item': 'true'})['id'] for a in arquivos]
        dados = {'media_type': 'CAROUSEL', 'children': ','.join(filhos), 'caption': legenda}
    elif video:
        dados = {'media_type': 'REELS', 'video_url': url, 'caption': legenda, 'share_to_feed': 'true'}
    else:
        dados = {'image_url': url, 'caption': legenda}
    c = call('POST', f'{IG}/media', dados)['id']
    for _ in range(40):
        s = call('GET', f'{c}?fields=status_code,status')
        if s.get('status_code') in (None, 'FINISHED'):
            return c
        if s['status_code'] == 'ERROR':
            print(f'aviso: falha no processamento {s}', file=sys.stderr)
            return None
        time.sleep(10 if video else 5)
    sys.exit('ERRO: mídia não terminou de processar em ~7 min')


# O Instagram às vezes falha ao baixar a mídia (ex.: código 2207077); tenta de novo até 3 vezes.
for tentativa in range(3):
    c = criar()
    if c:
        break
    time.sleep(30)
else:
    sys.exit('ERRO: o Instagram recusou a mídia 3 vezes')
m = call('POST', f'{IG}/media_publish', {'creation_id': c})['id']
print(json.dumps(call('GET', f'{m}?fields=permalink,timestamp')))
