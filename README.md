# PV Edições – vídeos automáticos

- `modelo/`: modelo Remotion do reel (texto palavra por palavra, retícula de mangá, linhas de velocidade, kanji ao fundo).
  - Roteiro em `modelo/roteiros/*.json` (cenas com `texto`, `destaque`, `kanji`, `impacto`).
  - Batida própria sem direitos autorais: `python3 modelo/scripts/gerar_beat.py modelo/public/beat.wav 30 <semente>`.
  - Render: `cd modelo && npm i && npx remotion render src/index.ts Reel out.mp4 --codec h264 --crf 24 --props=roteiros/<arquivo>.json`
- `postados/`: MP4 publicados. O Instagram baixa o vídeo pelo link raw deste repositório público.
