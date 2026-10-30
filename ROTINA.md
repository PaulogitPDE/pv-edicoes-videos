# Rotina PV Edições

## Sexta (pesquisa da semana)
1. Puxar os insights da semana (reach, views, ig_reels_avg_watch_time, shares, saved, comments) de cada post e comparar por obra/personagem e por voz. vidIQ `vidiq_instagram_tiktok_outlier_search` só se tiver crédito (zerado até 13/11); senão WebSearch: animes/mangás em alta na semana (lançamentos, episódios novos, capítulos que viralizaram).
2. Gravar `plano/AAAA-MM-DD.md` (data do sábado): o que funcionou, obras em alta e 7 dias (sáb→sex) com 2 personagens/histórias por dia (ver "Estratégia 22/10").
3. Para cada dia, gravar `modelo/roteiros/AAAA-MM-DD.json` (formato de `exemplo.json`) e `modelo/roteiros/AAAA-MM-DD.txt` (legenda com hashtags). Texto ORIGINAL em pt-BR contando a história do personagem (pode citar a fala real da obra traduzida), nunca copiar legenda de outro criador. Sempre com `serie`, `gancho` e `pergunta`. 7 a 9 cenas, ~18–22 s (ver Regras fixas de 21/10).
   - Se já existir roteiro para alguma data (ex.: reels que não saíram e foram remarcados), NÃO sobrescrever: planejar só as datas livres.
4. Commit + push.

## Estratégia 22/10 (Sr Pv: "está saindo muito genérico")
Dados de 22/10: reels com ~100–150 de alcance e só 3–5 s de tempo médio em vídeos de ~18 s (gente arrasta no começo), 0 compartilhamentos, 0 comentários; posts de imagem únicos com alcance 2–3. Causa: frase motivacional genérica sobre painel aleatório, sem dizer de quem é a história.
- **Todo reel é a história de UM personagem real** (arco, fala ou momento verdadeiro da obra): Thorfinn, Musashi, Guts, Eren, Rock Lee, Tanjiro, Saitama, Asta, Killua... Fatos corretos (conferir na web se tiver dúvida). A lição vem DA história, no fim, nunca no lugar dela.
- **Campos novos no roteiro**: `serie` ("OBRA · PERSONAGEM", etiqueta vermelha), `gancho` (frase que fica fixa no topo desde o frame 0 e cria curiosidade: "Venceu todas as lutas. E perguntou se merecia viver.") e `pergunta` (fecha o vídeo no cartão final e puxa comentário: opinião, "certo ou errado?", "qual personagem eu conto no próximo?").
- Cena 1 já conta a história (nada de "Não desista"). Imagens do próprio personagem/obra em pelo menos 3 cenas; o resto, painéis que combinem com o momento. Se o banco não tiver imagem do personagem, escolher outro personagem.
- Legenda: 1ª linha começa com o nome da obra + o resumo do momento (busca do IG lê isso), uma pergunta, "manda pra alguém que..." (envio por DM é o sinal que mais distribui) e hashtags da obra/personagem (#vinlandsaga #thorfinn), não genéricas.
- Não repetir personagem em menos de 7 dias. Bom repertório: Vinland Saga, Vagabond, Berserk, AoT, Naruto, Demon Slayer, OPM, Black Clover, HxH, Bleach, Blue Lock, Hajime no Ippo, Tokyo Revengers, JJK.
- Posts viram **carrossel** (ver seção "Posts (carrossel)").
- Sexta: a análise compara tempo médio de visualização, compartilhamentos, salvamentos e comentários por personagem/obra e por voz; dobrar nas obras que seguram mais.

## Animação 30/10 (Sr Pv: "vamos postar vídeos só de animação também")
- SUSPENSO 30/10 (Sr Pv achou o Ronin horrível; reels das 18h46 voltaram a ser de personagem até definir o novo formato). Antes: o reel das **18h46 (`<hoje>-b.json`) era 100% animado**; o das 11h46 continua sendo história de personagem de anime com frames do banco.
- Série própria "Animação · O Ronin": um samurai de tinta com cachecol vermelho, fundo claro de papel (primeiro frame claro, como sugeriu a análise de 29/10). Cada vídeo é um episódio ("o ronin, ep. N" na legenda).
- No roteiro, cada cena usa `"anim": "<cena>"` em vez de `imagem`. Cenas prontas em `motor/anima.py`: sombra, chuva, levanta, escada, corrida, multidao, sol, espada, poste. Cena nova = nova função lá (Pillow puro, sem biblioteca extra, sem Remotion; a skill Hypit fica só para vídeo avulso, porque depende de geração paga).
- Gancho no topo é PERGUNTA (análise 29/10), não spoiler. Temas que mais seguraram (29/10): monstro interno (Ichigo, 5,9 s e o 1º compartilhamento), "ninguém vem te salvar", "para de se comparar", "só um sobra" (Blue Lock).
- Roteiros prontos esperando data ficam em `modelo/roteiros/fila/` (anim-comparar, anim-sobra; e os de anime onepiece-zoro, naruto-sasuke, que saíram das 18h46 de 30 e 31/10 e vão para as 11h46 a partir de 1/11). Ao montar a semana, mover da fila para a data com `git mv`.

## Correções 30/10 (Sr Pv: "falas genéricas", "headline cobre o rosto", "efeito nas bordas")
- Toda fala cita NOME e FATO concreto ("Naruto reprovou três vezes na academia", nunca "Nasceu numa família de assassinos" sem dizer quem). Narrar todas as falas.
- Só usar imagens DO PRÓPRIO personagem/obra. Se o banco tem menos de 2 imagens dele, escolher outro personagem e deixar o roteiro em `modelo/roteiros/fila/` até chegarem imagens (Killua está lá esperando).
- Visual: o quadro aparece inteiro sobre fundo desfocado (rosto visível), legenda embaixo, rótulo pequeno no topo e o gancho some depois de ~2,5 s. Sem moldura nem linhas fixas nas bordas.

## Regras fixas (Sr Pv, 16/10/2026)
- **2 reels por dia** (11h46 e 18h46). Cada disparo posta 1, só se o `log.md` tiver menos de 2 postagens hoje.
- **Narração em TODAS as falas** (Sr Pv, 30/10: "por que está gerando poucas falas?"; substitui a regra de 21/10 de narrar só 2-3 cenas): marcar `"narrar": true` em todas as cenas. O **CTA continua NÃO falado**. Visual 30/10: sem moldura de painel e sem linhas de velocidade fixas nas bordas. Rodar `cd modelo && python3 scripts/narrar.py roteiros/<arquivo>.json` (DENTRO de modelo/). Voz padrão Adam pNInz6obpgDQGcFmaJgB; alternativa Eric cjVigY5qzO86Huf0OWal. A música abaixa sozinha nas cenas narradas.
- **Rodízio de vozes** (Sr Pv, 21/10): a voz muda a cada vídeo para testar engajamento. `narrar.py` pega a próxima de `modelo/vozes.json` (8 vozes masculinas premade: Adam, Brian, Harry, George, Bill, Charlie, Roger, Eric; vozes da biblioteca, como as brasileiras, exigem plano pago) e grava `vozNome` no roteiro. No `log.md`, sempre anotar a voz: `- data · tema (voz Nome) · link`. A análise semanal compara engajamento por voz.
- Orçamento ElevenLabs grátis: 10 mil caracteres/mês (renova dia 13). Com tudo narrado são ~200 caracteres por vídeo; 30/10 sobravam 5.284. Conferir saldo em GET /v1/user/subscription antes; se faltar, avisar na thread.
- Frases sugeridas por ele ("Não desista", "Supere seus limites", "Você não tem inimigos", "Desistir custa um sonho") entram como LIÇÃO no fim de uma história de personagem, não como abertura ("Você não tem inimigos" = Thors, Vinland Saga, usado em 22/10).
- **Duração dobrada** (Sr Pv, 21/10): 7 a 9 cenas curtas, ~18–22 s no total (antes eram ~9 s). Uma imagem do banco por cena, sem repetir imagens do dia anterior.
- **Motion nas frases de impacto** (Sr Pv, 21/10): marcar `"impacto": true` na frase forte (normalmente a última, às vezes a virada). O motor faz a palavra bater na tela com desfoque, separação RGB, tremida, flash vermelho e risco embaixo.
- **Sem Remotion e sem biblioteca de motion** (Sr Pv, 21/10): o vídeo e a imagem são feitos pelo nosso próprio código em `motor/` (Python desenhando cada frame com Pillow/numpy, ffmpeg só codifica). Toda animação (zoom, tremida, pop das palavras, frase de impacto, linhas de velocidade, flash) é calculada à mão em `motor/reel.py`. Não instalar Remotion, nem pacotes de animação/efeitos.

## Todo dia (postagem)
0. Se `log.md` já tem 2 postagens com a data de hoje (fuso America/Sao_Paulo), NÃO postar: só atualizar o status e parar. Nomes de arquivo: `<hoje>.json` para o 1º e `<hoje>-b.json` para o 2º.
1. Pegar `modelo/roteiros/<hoje>.json`. Se não existir, criar um na hora no mesmo estilo.
   - Formato preferido: frames de mangá (`imagem` em cada cena) das pastas boas do Drive "PV Edições – banco" (Mangá - ação e shōnen, Mangá - emocional e aesthetic, Aesthetic colorido; ver "LEIA - Índice do banco.txt", "LEIA - Índice do banco (21-10).txt", `banco/novas-2026-10-21.json` com 132 imagens novas e `banco/drive-pastas.json`). Dar preferência às imagens novas até todas serem usadas. Baixar com o conector do Drive para `modelo/public/banco/<id>.jpg` (não vai pro git). Não repetir as mesmas imagens de dias seguidos.
   - Música: um phonk da pasta Músicas do Drive em `modelo/public/banco/`, com `inicioMusica` no drop (ponto onde o volume sobe). Na falta, usar `gerar_beat.py`.
   - Narração: rodar `scripts/narrar.py` (ver Regras fixas) antes do render. Se `postados/<arquivo>.mp4` já existe no git e o roteiro já tem `audio` nas cenas, pular narração e render (já foi preparado) e ir direto ao passo 5.
2. (Só se não houver phonk do Drive) `python3 modelo/scripts/gerar_beat.py modelo/public/beat.wav 30 <AAAAMMDD>`.
3. `python3 motor/reel.py modelo/roteiros/<hoje>.json postados/<hoje>.mp4` (na raiz do repo; ~1–2 min). Conferir alguns frames com ffmpeg antes de postar.
4. Commit + push do MP4 (o Instagram baixa pelo link raw).
5. `python3 modelo/scripts/publicar.py postados/<hoje>.mp4 modelo/roteiros/<hoje>.txt`
6. Anotar data, link e tema em `log.md`, commit + push.

## Posts (carrossel) – 2 por dia, 9h16 e 21h16 (Sr Pv 21/10; virou carrossel na estratégia de 22/10)
0. Se `log-imagens.md` já tem 2 posts com a data de hoje, NÃO postar. Arquivos: `<hoje>.json` / `<hoje>-b.json`.
1. Formatos (alternar): **lista** ("5 personagens que perderam tudo", "4 vilões que tinham razão", "3 mestres que ensinaram sem falar"); **história em slides** (um personagem, um momento, 4–6 slides contando em ordem); **fala real** (a fala da obra traduzida + o contexto + o que ela ensina). Personagens com fatos corretos, nada de motivação genérica.
2. `modelo/posts/<arquivo>.json`: `{"serie": "etiqueta curta", "slides": [{imagem, headline, destaque, sub, pb, posicao, foco}, ...]}` com 5–7 slides. Slide 1 = capa com promessa ("arrasta. o último dói mais."); último = pergunta pra comentar ("qual deles é você?"). Imagens do banco não usadas em post antes (ver `log-imagens.md`). OLHAR as imagens antes de escrever. `destaque` = 1 palavra exatamente como na headline (com pontuação).
3. Legenda `modelo/posts/<arquivo>.txt`: 2–4 linhas aesthetic em minúsculas, a pergunta, "salva pra..." e hashtags das obras + #anime #manga #pvedicoes.
4. `python3 motor/post.py modelo/posts/<arquivo>.json postados-img/<arquivo>.jpg` gera `<arquivo>-1.jpg`, `-2.jpg`... Conferir todos (texto legível, não cobre o rosto).
5. Commit + push, depois `python3 modelo/scripts/publicar_carrossel.py modelo/posts/<arquivo>.txt postados-img/<arquivo>-1.jpg postados-img/<arquivo>-2.jpg ...` (post único continua possível com `publicar_imagem.py`).
6. Anotar em `log-imagens.md`: `- data · carrossel: tema · imagens <ids> · link`, commit + push. Sucesso: só atualizar o status da thread; reply só se falhar.
