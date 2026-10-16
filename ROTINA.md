# Rotina PV Edições

## Sexta (pesquisa da semana)
1. vidIQ `vidiq_instagram_tiktok_outlier_search`, no máximo 4 buscas (5 créditos cada; plano grátis = 150/mês). Nicho: anime + motivação/disciplina/mentalidade, últimos 7 dias. Complementar com `vidiq_youtube_search`/`vidiq_trending_videos` se sobrar crédito.
2. Gravar `plano/AAAA-MM-DD.md` (data do sábado): top virais (link, views, gancho, formato, personagem) e 7 dias (sáb→sex), cada um com tema viral de base e o roteiro.
3. Para cada dia, gravar `modelo/roteiros/AAAA-MM-DD.json` (formato de `exemplo.json`) e `modelo/roteiros/AAAA-MM-DD.txt` (legenda com hashtags). Frases ORIGINAIS em pt-BR inspiradas no tema, nunca copiar fala/legenda de outro criador. 4 a 7 cenas, 10–20 s.
4. Commit + push.

## Todo dia (postagem)
0. Se `log.md` já tem uma postagem com a data de hoje (fuso America/Sao_Paulo), NÃO postar de novo: só atualizar o status e parar.
1. Pegar `modelo/roteiros/<hoje>.json`. Se não existir, criar um na hora no mesmo estilo.
   - Formato preferido: frames de mangá (`imagem` em cada cena) das pastas boas do Drive "PV Edições – banco" (Mangá - ação e shōnen, Mangá - emocional e aesthetic, Aesthetic colorido; ver "LEIA - Índice do banco.txt" e `banco/drive-pastas.json`). Baixar com o conector do Drive para `modelo/public/banco/<id>.jpg` (não vai pro git). Não repetir as mesmas imagens de dias seguidos.
   - Música: um phonk da pasta Músicas do Drive em `modelo/public/banco/`, com `inicioMusica` no drop (ponto onde o volume sobe). Na falta, usar `gerar_beat.py`.
   - CTA falado no final (`vozFinal`): ElevenLabs (env ELEVENLABS_API_KEY, header xi-api-key), voz Eric cjVigY5qzO86Huf0OWal, eleven_multilingual_v2, frase curta tipo "Se isso falou com você, segue o PV Edições". Plano grátis = 10 mil caracteres/mês, então no máximo ~80 caracteres por dia.
2. (Só se não houver phonk do Drive) `python3 modelo/scripts/gerar_beat.py modelo/public/beat.wav 30 <AAAAMMDD>`.
3. `cd modelo && npm i && npx remotion render src/index.ts Reel ../postados/<hoje>.mp4 --codec h264 --crf 24 --props=roteiros/<hoje>.json --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`
4. Commit + push do MP4 (o Instagram baixa pelo link raw).
5. `python3 modelo/scripts/publicar.py postados/<hoje>.mp4 modelo/roteiros/<hoje>.txt`
6. Anotar data, link e tema em `log.md`, commit + push.
