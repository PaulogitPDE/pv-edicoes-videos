# Rotina @crmquevende

Conta: Instagram **@crmquevende** (id `17841477784714532`, Página "CRM  Que Vende" `1053653491172442`), publicada pela API oficial do Instagram com o mesmo token do app "Eugencia API" (permissão `instagram_content_publish`). Tudo fica na pasta `crm/` deste repositório, na branch `claude/project-thread-j72f39` (o PV Edições usa a `main`; não misturar).

## Regras fixas (Sr Pv, 21/10/2026)
- **Todo dia, sem exceção: 2 reels + 2 posts de imagem.** Horários (Brasília): post 1 às **08h37**, reel 1 às **12h17**, post 2 às **17h37**, reel 2 às **19h57**.
- **Post de trend extra** segunda, quarta e sexta às **10h27** (seção "Trend" abaixo). É uma rotina à parte das 4 publicações.
- **Sem banco do Drive e sem pesquisa de trend na rotina diária.** Tudo é criado a partir da nossa oferta (abaixo) e do cronograma do mês em `crm/calendario/AAAA-MM.json`.
- **Datas comemorativas** (dia do dentista, dia do médico, dia das mães, dos pais, do professor, feriados, Black Friday...): nesses dias o **reel 1 e o post 1 são da data**; o reel 2 e o post 2 seguem o cronograma normal.
- **Dia da semana conta**: segunda (dor), terça (bastidor do funil), quarta (objeção), quinta (a conta), **sextou** (leve + vagas de fundador), sábado (dica rápida), domingo (reflexão/planejamento). Ver `crm/scripts/temas.py`.
- **CTAs alternados** (o cronograma já define qual vai em cada peça; não repetir o mesmo CTA nas 4 do dia):
  - `direct`: "Manda **FUNIL** no Direct" (a resposta automática da palavra FUNIL já está configurada no Meta Business Suite).
  - `bio`: "Link na bio" (o link da bio é o WhatsApp do Sr Pv, wa.me/5581985704921).
  - `comenta`: "Comenta **FUNIL** que eu te mando" (o Sr Pv responde os comentários).
- **Vídeo**: mesma pegada dos criativos antigos (fundo escuro com grade, lime #C6FF3D, cartões de vidro, tarja no topo, legenda grande), **com muito mais motion**: câmera mexendo, bolinha neon piscando, desenho sendo feito na tela, pop-ups de lead pulando animados nas cenas de CRM, tudo animado. Isso já está pronto no motor; o roteiro só precisa usar as cenas certas.
- **Sem Remotion e sem biblioteca de motion** (mesma regra do PV Edições): reel e imagem saem do nosso código em `crm/motor/` (Python + Pillow/numpy, ffmpeg só codifica). Trilha e efeitos sonoros são sintetizados no próprio motor (sem direitos autorais).
- **Sem narração da ElevenLabs** por enquanto: o plano grátis (10 mil caracteres/mês) é dividido com o PV Edições, que já usa quase tudo. O vídeo conta a história pelo texto na tela + efeitos sonoros. Se um dia o Sr Pv assinar um plano pago, dá para narrar 1 frase por reel.
- Nunca mexer em campanhas/orçamento da Meta (outra thread cuida disso).

## A oferta (base de todo conteúdo)
- **Orçamento que Volta**: o follow-up automático no WhatsApp da clínica, montado no Kommo. Toda paciente que pediu orçamento e disse "vou pensar" recebe 4 mensagens sozinhas: **+2h** (tirar dúvida), **+1 dia** (parcelar/começar pela avaliação), **+3 dias** (dois horários), **+7 dias** (encerrar sem pressão, "responde 'quero' que eu reabro"). Mais lembrete de consulta 1 dia e 1 hora antes, funil de orçamentos e treino da recepção.
- Nicho: **clínicas odontológicas e de estética** (implante, lentes, clareamento, ortodontia, harmonização, botox).
- Preço **R$ 1.497** (ou 3x R$ 550), **no ar em 7 dias úteis ou não paga**. **3 vagas de fundador a R$ 997** em troca de depoimento. Licença do Kommo à parte, paga direto à Kommo (não esconder).
- Isca: **Kit Orçamento que Volta** (as 4 mensagens + checklist de 5 itens), pedido com FUNIL no Direct. Depois: raio-x de 15 min no WhatsApp.
- Números: não inventar estatística como se fosse dado real. Contas de exemplo ("20 orçamentos × R$ 480") são ok quando ficam claras como exemplo; dado de mercado só com fonte.

## Arquivos
- `crm/calendario/AAAA-MM.json`: o cronograma do mês (tema, layout/cenas e CTA de cada peça). Página para o Sr Pv ver: artefato "Cronograma CRM que vende" https://claude.ai/artifact/BejguxivJhrExok5M4h3aq (gerar com `python3 crm/scripts/pagina_cronograma.py` e republicar nesse mesmo link, passando `url`, quando o mês mudar).
- Reels: roteiro `crm/roteiros/<data>-r1.json` / `-r2.json`, legenda `crm/roteiros/<data>-r1.txt`, vídeo `crm/postados/<data>-r1.mp4`.
- Posts: `crm/posts/<data>-p1.json` / `-p2.json` (e `-trend`), legenda `.txt` ao lado, imagem `crm/postados-img/<data>-p1.jpg`.
- `crm/log.md`: uma linha por publicação: `- AAAA-MM-DD · r1 · tema · CTA · link`.

## Como escrever o roteiro do reel (`crm/motor/reel.py`)
JSON: `{"tarja": "...", "semente": <número do dia>, "tema": "...", "cenas": [...]}`. Exemplo completo: `crm/roteiros/2026-10-22-r1.json`; todas as cenas juntas: `crm/roteiros/teste-todas.json`.
- **18 a 24 s, 5 a 7 cenas.** Primeira cena é `gancho` curto (até 2,5 s) e forte. Última cena é sempre `cta` no modo do cronograma (`direct`, `bio` ou `comenta`).
- **Tarja** fixa no topo em todo reel, no estilo "Eu faço o WhatsApp da sua clínica <chamar a paciente de volta> sozinho" (variar a frase).
- Texto entre `<sinais>` vira destaque lime com brilho. Toda cena tem `legenda` curta (é ela que conta a história, já que não há narração). Sem emoji (a fonte não tem).
- Usar **sempre** pelo menos uma cena "de CRM" com pop-ups (`leads`, `timeline` ou `chat`) e uma com desenho (`desenho`, ou `rabisco` no gancho). Variar a ordem e a `semente` todo dia para a câmera e a música mudarem.
- Cenas: `gancho` (texto batendo, `rotulo`, `rabisco`: sublinha|circulo|x), `chat` (conversa de WhatsApp com digitando..., `carimbo`), `leads` (pop-ups de "Novo lead" pulando e indo para o funil do Kommo, cards andando até "Agendado", `total` com `{valor}`), `timeline` (+2h, +1 dia... desenhada, com `resposta` da paciente e notificação), `numero` (contador com anel desenhado, `riscar`), `desenho` (`forma`: funil com bolinhas caindo, `vazando`: 0.4; ou grafico subindo com `valor`), `lista` (checklist com ✓/✗ desenhados), `cta` (direct: digitando FUNIL e resposta; bio: perfil + toque no link + card do WhatsApp; comenta: comentário com coração), `data` (calendário virando + confete, para datas comemorativas). Campo opcional `dur` em segundos.
- Render (na raiz do repo, ~1,5 min): `python3 crm/motor/reel.py crm/roteiros/<arq>.json crm/postados/<arq>.mp4`
- **Conferir antes de postar**: `ffmpeg -i crm/postados/<arq>.mp4 -vf "select='not(mod(n\,60))',scale=270:480,tile=6x2" -frames:v 1 -vsync 0 /tmp/conferir.png` e olhar a imagem (texto legível, nada cortado, nada sobreposto). Corrigir e renderizar de novo se precisar.

## Legenda do Instagram (`.txt`)
1ª linha = gancho (curto). 2 a 4 linhas de valor, em tom de conversa com a dona/dono de clínica. 1 linha de CTA igual ao do vídeo. Hashtags (5 a 8): #clinicaodontologica #odontologia #esteticaavancada #harmonizacaofacial #gestaodeclinica #kommo #followup #crmquevende.

## Como fazer o post de imagem (`crm/motor/post.py`)
JSON: `layout` (frase | data | chat | numero | lista | antes_depois), `headline` (com `<destaque>`), `rotulo`, `sub`, `rabisco`, `cta` e `palavra` (FUNIL). Campos por layout: data (`dia`, `mes`), chat (`nome`, `status`, `mensagens`, `carimbo`), numero (`numero`, `cor`), lista (`itens` com `t`/`ok`), antes_depois (`antes`, `depois`, `titulo_antes`, `titulo_depois`).
- Render: `python3 crm/motor/post.py crm/posts/<arq>.json crm/postados-img/<arq>.jpg` e **abrir o JPG para conferir**.

## Cada disparo (post ou reel)
0. `git pull`. Se hoje ainda não está no cronograma (a rotina começa em 22/10/2026), não postar nada. Descobrir hoje (America/Sao_Paulo) e a peça do disparo (o agendamento diz qual: p1, r1, p2 ou r2). Se `crm/log.md` já tem essa peça de hoje, não fazer nada. Se uma peça anterior de hoje ficou faltando (falha), fazer ela também, para fechar o dia sem exceção.
1. Ler o item de hoje em `crm/calendario/AAAA-MM.json` (tema, layout/cenas, CTA). Se o arquivo do mês não existir, rodar `python3 crm/scripts/cronograma.py AAAA-MM` antes.
2. Escrever o roteiro/post e a legenda (se ainda não existirem), renderizar e conferir.
3. `git add` + commit + `git push` (o Instagram baixa pelo link raw do commit).
4. `python3 crm/scripts/publicar.py <mp4 ou jpg> <legenda.txt>`
5. Anotar no `crm/log.md`, commit + push. Deu certo: só atualizar o checklist da thread com o link. Mandar mensagem só se algo falhar, dizendo o que falhou.

## Trend (segunda, quarta e sexta, 10h27) — rotina à parte
1. Pesquisar (WebSearch) o assunto que está bombando no Brasil **nesta semana** (futebol, novela, reality, meme, lançamento, celebridade, algo viral). Evitar tragédia, morte, doença grave, política partidária e religião.
2. Fazer um post no estilo do **prefeito Manga de Sorocaba**: um gancho que puxa o assunto do momento, quase "nada a ver", e vira para o CRM que vende numa frase. Todo mundo sabe que não tem nada a ver, e é isso que engaja. Ex.: "Fulano fez X essa semana. Enquanto isso, sua paciente tá há 3 dias esperando resposta." Não precisa vender a oferta; basta a chamada de atenção + uma frase sobre o CRM que vende.
3. Formato padrão: post de imagem `layout: frase` com `rotulo: "tá todo mundo falando"`. Se o assunto pedir, pode ser um reel curto (gancho + 1 cena + cta, ~10 s). Arquivos `<data>-trend.*`; CTA do cronograma.
4. Publicar e anotar no log como `trend`, citando o assunto. Não usar imagem, logo ou foto de terceiros; só o nosso motor.

## Cronograma do mês (dia 25, 10h07)
1. `python3 crm/scripts/cronograma.py <próximo mês>`. Antes, revisar `DATAS` em `crm/scripts/temas.py` e incluir as datas do próximo mês (comemorativas gerais e da saúde: dia das mães, dos pais, do professor, do médico 18/10, do dentista 25/10, feriados, Black Friday, Natal, Ano Novo, Carnaval, Dia da Mulher...). Se um banco de temas já foi usado 2 vezes, escrever temas novos em `temas.py`.
2. Commit + push e republicar o artefato "Cronograma CRM que vende" com o mês novo. Mandar uma mensagem curta na thread com as datas especiais do mês.
