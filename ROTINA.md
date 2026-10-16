# Rotina PV Edições

## Sexta (pesquisa da semana)
1. vidIQ `vidiq_instagram_tiktok_outlier_search`, no máximo 4 buscas (5 créditos cada; plano grátis = 150/mês). Nicho: anime + motivação/disciplina/mentalidade, últimos 7 dias. Complementar com `vidiq_youtube_search`/`vidiq_trending_videos` se sobrar crédito.
2. Gravar `plano/AAAA-MM-DD.md` (data do sábado): top virais (link, views, gancho, formato, personagem) e 7 dias (sáb→sex), cada um com tema viral de base e o roteiro.
3. Para cada dia, gravar `modelo/roteiros/AAAA-MM-DD.json` (formato de `exemplo.json`) e `modelo/roteiros/AAAA-MM-DD.txt` (legenda com hashtags). Frases ORIGINAIS em pt-BR inspiradas no tema, nunca copiar fala/legenda de outro criador. 4 a 7 cenas, 10–20 s.
4. Commit + push.

## Regras fixas (Sr Pv, 16/10/2026)
- **2 reels por dia** (11h46 e 18h46). Cada disparo posta 1, só se o `log.md` tiver menos de 2 postagens hoje.
- **Narração masculina da ElevenLabs em TODO vídeo**: `python3 modelo/scripts/narrar.py modelo/roteiros/<arquivo>.json` (voz padrão Adam pNInz6obpgDQGcFmaJgB; alternativa Eric cjVigY5qzO86Huf0OWal). O script sincroniza as palavras com a fala e põe o CTA (campo `cta`) no cartão final.
- Orçamento ElevenLabs grátis: 10 mil caracteres/mês para ~60 vídeos → **máximo ~110 caracteres por vídeo, CTA incluso**. Conferir saldo em GET /v1/user/subscription antes; se faltar, avisar na thread.
- Frases de abertura sugeridas por ele (usar e variar): "Não desista", "Supere seus limites", "Você não tem inimigos", "Desistir custa um sonho" (já usada em 16/10).
- Frases curtas, 4 a 6 cenas, uma imagem do banco por cena, sem repetir imagens do dia anterior.

## Todo dia (postagem)
0. Se `log.md` já tem 2 postagens com a data de hoje (fuso America/Sao_Paulo), NÃO postar: só atualizar o status e parar. Nomes de arquivo: `<hoje>.json` para o 1º e `<hoje>-b.json` para o 2º.
1. Pegar `modelo/roteiros/<hoje>.json`. Se não existir, criar um na hora no mesmo estilo.
   - Formato preferido: frames de mangá (`imagem` em cada cena) das pastas boas do Drive "PV Edições – banco" (Mangá - ação e shōnen, Mangá - emocional e aesthetic, Aesthetic colorido; ver "LEIA - Índice do banco.txt" e `banco/drive-pastas.json`). Baixar com o conector do Drive para `modelo/public/banco/<id>.jpg` (não vai pro git). Não repetir as mesmas imagens de dias seguidos.
   - Música: um phonk da pasta Músicas do Drive em `modelo/public/banco/`, com `inicioMusica` no drop (ponto onde o volume sobe). Na falta, usar `gerar_beat.py`.
   - Narração: rodar `scripts/narrar.py` (ver Regras fixas) antes do render; o CTA falado vai no campo `cta`.
2. (Só se não houver phonk do Drive) `python3 modelo/scripts/gerar_beat.py modelo/public/beat.wav 30 <AAAAMMDD>`.
3. `cd modelo && npm i && npx remotion render src/index.ts Reel ../postados/<hoje>.mp4 --codec h264 --crf 24 --props=roteiros/<hoje>.json --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`
4. Commit + push do MP4 (o Instagram baixa pelo link raw).
5. `python3 modelo/scripts/publicar.py postados/<hoje>.mp4 modelo/roteiros/<hoje>.txt`
6. Anotar data, link e tema em `log.md`, commit + push.
