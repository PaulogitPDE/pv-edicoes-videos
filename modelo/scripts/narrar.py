"""Gera a narração masculina (ElevenLabs) só das cenas marcadas com "narrar": true e sincroniza as palavras.
Uso (dentro de modelo/): python3 scripts/narrar.py roteiros/AAAA-MM-DD.json
Regra (Sr Pv, 21/10): voz só nos pontos importantes; CTA não é falado; nem todo texto da tela é narrado.
Campo opcional "falar" na cena: texto falado diferente do texto da tela.
Grava public/narr-<nome>-<i>.mp3 por cena narrada e preenche cenas[].audio/tempos/duracao."""
import base64, json, os, subprocess, sys

FPS = 30
VOZ_PADRAO = 'pNInz6obpgDQGcFmaJgB'  # Adam (masculina, grave) – premade, funciona no plano grátis
POR_PALAVRA, SEGURA = 8, 26
caminho = sys.argv[1]
r = json.load(open(caminho, encoding='utf-8'))
nome = os.path.splitext(os.path.basename(caminho))[0]
voz = r.get('voz', VOZ_PADRAO)
total_chars = 0


def tts(texto):
    corpo = json.dumps({'text': texto, 'model_id': 'eleven_multilingual_v2',
                        'voice_settings': {'stability': 0.4, 'similarity_boost': 0.8, 'style': 0.45, 'speed': 0.95}})
    out = subprocess.run(['curl', '-sS', '-X', 'POST', f'https://api.elevenlabs.io/v1/text-to-speech/{voz}/with-timestamps',
                          '-H', f"xi-api-key: {os.environ['ELEVENLABS_API_KEY']}", '-H', 'Content-Type: application/json', '-d', corpo],
                         capture_output=True, text=True).stdout
    d = json.loads(out)
    if 'audio_base64' not in d:
        sys.exit(f'ERRO ElevenLabs: {out[:300]}')
    return d


for i, c in enumerate(r['cenas']):
    for k in ('audio', 'tempos', 'duracao'):
        c.pop(k, None)
    if not c.get('narrar'):
        continue
    falado = c.get('falar', c['texto'])
    d = tts(falado)
    total_chars += len(falado)
    mp3 = f'narr-{nome}-{i}.mp3'
    open(os.path.join('public', mp3), 'wb').write(base64.b64decode(d['audio_base64']))
    al = d['alignment']
    starts, novo = [], True
    for ch, t in zip(al['characters'], al['character_start_times_seconds']):
        if ch.isspace():
            novo = True
        elif novo:
            starts.append(t); novo = False
    fim = al['character_end_times_seconds'][-1]
    c['audio'] = mp3
    n = len(c['texto'].split())
    if not c.get('falar') and len(starts) == n:
        c['tempos'] = [round(t * FPS) for t in starts]
    padrao = round(n * POR_PALAVRA * (1.6 if c.get('impacto') else 1)) + SEGURA + (22 if c.get('impacto') else 0)
    c['duracao'] = max(padrao, round(fim * FPS) + 18)

for k in ('narracao', 'duracaoFinal', 'vozFinal', 'cta'):
    r.pop(k, None)
json.dump(r, open(caminho, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
seg = sum(c.get('duracao') or (round(len(c['texto'].split()) * POR_PALAVRA * (1.6 if c.get('impacto') else 1)) + SEGURA + (22 if c.get('impacto') else 0)) for c in r['cenas']) / FPS + 2
print('ok', nome, f'~{seg:.1f} s de vídeo,', total_chars, 'caracteres narrados')
