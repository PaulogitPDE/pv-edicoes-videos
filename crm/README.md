# CRM que vende – conteúdo automático do @crmquevende

Rotina completa em `ROTINA.md`. Motor próprio em `motor/` (Python + Pillow/numpy + ffmpeg, sem Remotion):
- `motor/reel.py`: reels 1080x1920 com câmera, transições, neon, desenhos e pop-ups de lead; trilha e efeitos em `motor/som.py`.
- `motor/post.py`: posts 1080x1350 (layouts frase, data, chat, numero, lista, antes_depois).
- `scripts/publicar.py`: publica MP4/JPG no @crmquevende pela API oficial.
- `scripts/cronograma.py` + `scripts/temas.py`: cronograma do mês em `calendario/`.
