"""Gera a narração masculina (ElevenLabs) do roteiro e sincroniza as palavras.
Uso: python3 scripts/narrar.py roteiros/AAAA-MM-DD.json
O JSON precisa de cenas[].texto e, opcional, "cta" (frase falada no cartão final) e "voz" (voice_id).
Grava public/narr-<nome>.mp3 e preenche narracao, cenas[].tempos/duracao e duracaoFinal."""
import base64, json, os, subprocess, sys

FPS = 30
VOZ_PADRAO = 'pNInz6obpgDQGcFmaJgB'  # Adam (masculina, grave) – premade, funciona no plano grátis
caminho = sys.argv[1]
r = json.load(open(caminho, encoding='utf-8'))
nome = os.path.splitext(os.path.basename(caminho))[0]
partes = [c['texto'] for c in r['cenas']] + ([r['cta']] if r.get('cta') else [])
texto = ' '.join(partes)
corpo = json.dumps({'text': texto, 'model_id': 'eleven_multilingual_v2',
                    'voice_settings': {'stability': 0.4, 'similarity_boost': 0.8, 'style': 0.45, 'speed': 0.95}})
voz = r.get('voz', VOZ_PADRAO)
out = subprocess.run(['curl', '-sS', '-X', 'POST', f'https://api.elevenlabs.io/v1/text-to-speech/{voz}/with-timestamps',
                      '-H', f"xi-api-key: {os.environ['ELEVENLABS_API_KEY']}", '-H', 'Content-Type: application/json', '-d', corpo],
                     capture_output=True, text=True).stdout
d = json.loads(out)
if 'audio_base64' not in d:
    sys.exit(f'ERRO ElevenLabs: {out[:300]}')
mp3 = f'narr-{nome}.mp3'
open(os.path.join('public', mp3), 'wb').write(base64.b64decode(d['audio_base64']))
al = d['alignment']
chars, ini, fim = al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']
# início de cada palavra
starts, novo = [], True
for ch, t in zip(chars, ini):
    if ch.isspace():
        novo = True
    elif novo:
        starts.append(t); novo = False
fim_audio = fim[-1]
k = 0
blocos = []
for p in partes:
    n = len(p.split())
    blocos.append(starts[k:k + n]); k += n
inicio_cenas = [b[0] for b in blocos[:len(r['cenas'])]]
inicio_cenas[0] = 0
fim_cenas = [b[0] for b in blocos[1:]] + ([] if r.get('cta') else [fim_audio + 0.6])
for i, c in enumerate(r['cenas']):
    a = inicio_cenas[i]
    c['tempos'] = [max(0, round((t - a) * FPS)) for t in blocos[i]]
    c['duracao'] = max(round((fim_cenas[i] - a) * FPS), c['tempos'][-1] + 12)
r['narracao'] = mp3
r['duracaoFinal'] = round((fim_audio - fim_cenas[len(r['cenas']) - 1]) * FPS) + 25 if r.get('cta') else 45
r.pop('vozFinal', None)
json.dump(r, open(caminho, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', mp3, round(fim_audio, 1), 's,', len(texto), 'caracteres')
