# Rotina PV Edições

## Sexta (pesquisa da semana)
1. vidIQ `vidiq_instagram_tiktok_outlier_search`, no máximo 4 buscas (5 créditos cada; plano grátis = 150/mês). Nicho: anime + motivação/disciplina/mentalidade, últimos 7 dias. Complementar com `vidiq_youtube_search`/`vidiq_trending_videos` se sobrar crédito.
2. Gravar `plano/AAAA-MM-DD.md` (data do sábado): top virais (link, views, gancho, formato, personagem) e 7 dias (sáb→sex), cada um com tema viral de base e o roteiro.
3. Para cada dia, gravar `modelo/roteiros/AAAA-MM-DD.json` (formato de `exemplo.json`) e `modelo/roteiros/AAAA-MM-DD.txt` (legenda com hashtags). Frases ORIGINAIS em pt-BR inspiradas no tema, nunca copiar fala/legenda de outro criador. 4 a 7 cenas, 10–20 s.
4. Commit + push.

## Todo dia (postagem)
1. Pegar `modelo/roteiros/<hoje>.json` (fuso America/Sao_Paulo). Se não existir, criar um na hora no mesmo estilo.
2. `python3 modelo/scripts/gerar_beat.py modelo/public/beat.wav 30 <AAAAMMDD>` (batida nova a cada dia).
3. `cd modelo && npm i && npx remotion render src/index.ts Reel ../postados/<hoje>.mp4 --codec h264 --crf 24 --props=roteiros/<hoje>.json --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`
4. Commit + push do MP4 (o Instagram baixa pelo link raw).
5. `python3 modelo/scripts/publicar.py postados/<hoje>.mp4 modelo/roteiros/<hoje>.txt`
6. Anotar data, link e tema em `log.md`, commit + push.
