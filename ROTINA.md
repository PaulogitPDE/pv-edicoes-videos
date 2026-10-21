# Rotina PV Edições

## Sexta (pesquisa da semana)
1. vidIQ `vidiq_instagram_tiktok_outlier_search`, no máximo 4 buscas (5 créditos cada; plano grátis = 150/mês). Nicho: anime + motivação/disciplina/mentalidade, últimos 7 dias. Complementar com `vidiq_youtube_search`/`vidiq_trending_videos` se sobrar crédito.
2. Gravar `plano/AAAA-MM-DD.md` (data do sábado): top virais (link, views, gancho, formato, personagem) e 7 dias (sáb→sex), cada um com tema viral de base e o roteiro.
3. Para cada dia, gravar `modelo/roteiros/AAAA-MM-DD.json` (formato de `exemplo.json`) e `modelo/roteiros/AAAA-MM-DD.txt` (legenda com hashtags). Frases ORIGINAIS em pt-BR inspiradas no tema, nunca copiar fala/legenda de outro criador. 7 a 9 cenas, ~18–22 s (ver Regras fixas de 21/10).
   - Se já existir roteiro para alguma data (ex.: reels que não saíram e foram remarcados), NÃO sobrescrever: planejar só as datas livres.
4. Commit + push.

## Regras fixas (Sr Pv, 16/10/2026)
- **2 reels por dia** (11h46 e 18h46). Cada disparo posta 1, só se o `log.md` tiver menos de 2 postagens hoje.
- **Narração masculina da ElevenLabs só nos pontos importantes** (Sr Pv, 21/10): marcar `"narrar": true` em 2 a 3 cenas-chave (abertura, virada, frase final). Nem todo texto da tela é narrado e o **CTA NÃO é falado**. Rodar `cd modelo && python3 scripts/narrar.py roteiros/<arquivo>.json` (DENTRO de modelo/). Voz padrão Adam pNInz6obpgDQGcFmaJgB; alternativa Eric cjVigY5qzO86Huf0OWal. A música abaixa sozinha nas cenas narradas.
- **Rodízio de vozes** (Sr Pv, 21/10): a voz muda a cada vídeo para testar engajamento. `narrar.py` pega a próxima de `modelo/vozes.json` (8 vozes masculinas premade: Adam, Brian, Harry, George, Bill, Charlie, Roger, Eric; vozes da biblioteca, como as brasileiras, exigem plano pago) e grava `vozNome` no roteiro. No `log.md`, sempre anotar a voz: `- data · tema (voz Nome) · link`. A análise semanal compara engajamento por voz.
- Orçamento ElevenLabs grátis: 10 mil caracteres/mês → ~70 caracteres narrados por vídeo. Conferir saldo em GET /v1/user/subscription antes; se faltar, avisar na thread.
- Frases de abertura sugeridas por ele (usar e variar): "Não desista", "Supere seus limites", "Você não tem inimigos", "Desistir custa um sonho" (já usada em 16/10).
- **Duração dobrada** (Sr Pv, 21/10): 7 a 9 cenas curtas, ~18–22 s no total (antes eram ~9 s). Uma imagem do banco por cena, sem repetir imagens do dia anterior.
- **Motion nas frases de impacto** (Sr Pv, 21/10): marcar `"impacto": true` na frase forte (normalmente a última, às vezes a virada). O motor faz a palavra bater na tela com desfoque, separação RGB, tremida, flash vermelho e risco embaixo.
- **Sem Remotion e sem biblioteca de motion** (Sr Pv, 21/10): o vídeo e a imagem são feitos pelo nosso próprio código em `motor/` (Python desenhando cada frame com Pillow/numpy, ffmpeg só codifica). Toda animação (zoom, tremida, pop das palavras, frase de impacto, linhas de velocidade, flash) é calculada à mão em `motor/reel.py`. Não instalar Remotion, nem pacotes de animação/efeitos.

## Todo dia (postagem)
0. Se `log.md` já tem 2 postagens com a data de hoje (fuso America/Sao_Paulo), NÃO postar: só atualizar o status e parar. Nomes de arquivo: `<hoje>.json` para o 1º e `<hoje>-b.json` para o 2º.
1. Pegar `modelo/roteiros/<hoje>.json`. Se não existir, criar um na hora no mesmo estilo.
   - Formato preferido: frames de mangá (`imagem` em cada cena) das pastas boas do Drive "PV Edições – banco" (Mangá - ação e shōnen, Mangá - emocional e aesthetic, Aesthetic colorido; ver "LEIA - Índice do banco.txt" e `banco/drive-pastas.json`). Baixar com o conector do Drive para `modelo/public/banco/<id>.jpg` (não vai pro git). Não repetir as mesmas imagens de dias seguidos.
   - Música: um phonk da pasta Músicas do Drive em `modelo/public/banco/`, com `inicioMusica` no drop (ponto onde o volume sobe). Na falta, usar `gerar_beat.py`.
   - Narração: rodar `scripts/narrar.py` (ver Regras fixas) antes do render. Se `postados/<arquivo>.mp4` já existe no git e o roteiro já tem `audio` nas cenas, pular narração e render (já foi preparado) e ir direto ao passo 5.
2. (Só se não houver phonk do Drive) `python3 modelo/scripts/gerar_beat.py modelo/public/beat.wav 30 <AAAAMMDD>`.
3. `python3 motor/reel.py modelo/roteiros/<hoje>.json postados/<hoje>.mp4` (na raiz do repo; ~1–2 min). Conferir alguns frames com ffmpeg antes de postar.
4. Commit + push do MP4 (o Instagram baixa pelo link raw).
5. `python3 modelo/scripts/publicar.py postados/<hoje>.mp4 modelo/roteiros/<hoje>.txt`
6. Anotar data, link e tema em `log.md`, commit + push.

## Posts de imagem (2 por dia, 9h16 e 21h16) – Sr Pv, 21/10
0. Se `log-imagens.md` já tem 2 posts com a data de hoje, NÃO postar. Arquivos: `<hoje>.jpg`/`<hoje>-b.jpg`.
1. Escolher uma imagem do banco (`modelo/public/banco/`, incluindo as novas de `banco/novas-*.json`) que não foi usada em post de imagem antes (ver `log-imagens.md`) e de preferência não usada nos reels do dia. OLHAR a imagem antes de escrever.
2. Escrever `modelo/posts/<arquivo>.json`: `imagem`, `headline` (curta e chamativa, em pt-BR, original), `destaque` (1 palavra exatamente como na headline, com pontuação, vira tarja vermelha), `sub` (linha aesthetic em minúsculas, serifa itálica), `pb` true para mangá P&B, `posicao` "topo" se o rosto/ação estiver embaixo, `foco` se precisar.
   - O texto faz uma crítica ligada ao que acontece no painel (o personagem, a cena) OU é uma frase filosófica original que faça pensar. Nada de frase famosa copiada, nada de motivação genérica de reel.
3. Legenda `modelo/posts/<arquivo>.txt`: 2–4 linhas aesthetic (minúsculas, ritmo poético), uma pergunta que puxe comentário, e hashtags (#anime #manga #aesthetic #reflexão #pvedicoes + 2–3 do personagem/obra).
4. `python3 motor/post.py modelo/posts/<arquivo>.json postados-img/<arquivo>.jpg` (na raiz do repo). Abrir o JPG e conferir (texto legível, não cobre o rosto).
5. Commit + push, depois `python3 modelo/scripts/publicar_imagem.py postados-img/<arquivo>.jpg modelo/posts/<arquivo>.txt`.
6. Anotar em `log-imagens.md`: `- data · headline · imagem <id> · link`, commit + push. Sucesso: só atualizar o status da thread; reply só se falhar.
