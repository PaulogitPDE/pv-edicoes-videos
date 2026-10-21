# PV Edições – vídeos automáticos

- `motor/`: motor próprio em Python (Pillow/numpy + ffmpeg), sem Remotion. `reel.py` gera o reel; `post.py` gera o post de imagem com headline.
- `modelo/`: roteiros, posts, vozes, banco de imagens (`public/banco`, fora do git) e scripts de narração/publicação.
  - Roteiro em `modelo/roteiros/*.json` (cenas com `texto`, `destaque`, `kanji`, `impacto`).
  - Batida própria sem direitos autorais: `python3 modelo/scripts/gerar_beat.py modelo/public/beat.wav 30 <semente>`.
  - Render: `python3 motor/reel.py modelo/roteiros/<arquivo>.json postados/<arquivo>.mp4`
- `postados/`: MP4 publicados. O Instagram baixa o vídeo pelo link raw deste repositório público.
