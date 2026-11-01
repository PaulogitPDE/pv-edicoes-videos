# Rotina diária dos achadinhos (@pvedicoes, assinatura "Achadinhos do PV")

Regras do usuário: carrossel no modelo de cards coloridos (achadinhos/carrossel.py), SEM pílula de link nos slides,
nunca citar "PV Edições" nos posts, Direct do QUERO manda SÓ o link do grupo (achadinhos/grupo.txt).
Nada de posts com rosto falso ou alegação inventada ("uso todo dia"); slide diz o que o produto faz.
Tudo que o PC precisa ler (fila, comandos) tem que estar na branch `main`.

## Manhã (08:13 BRT)
1. `git pull origin main`.
2. Tema do dia pela ordem: seg casa, ter tech, qua cozinha, qui setup, sex beleza, sáb carro, dom casa.
   `python3 achadinhos/escolher.py TEMA 15` e também `python3 achadinhos/escolher.py tech 10` (para variar a fila).
3. Escolher 5 produtos "uau" do tema (nada de produto de consumo comum tipo sabão/detergente; gadgets e coisas úteis)
   e escrever `achadinhos/roteiros/AAAA-MM-DD-TEMA.json` (capa linha1/linha2/sub, rotulo, produtos com nome curto,
   beneficio, foto = índice da foto mais limpa do anúncio, cta). Ver o roteiro de 2026-10-31-casa como modelo.
4. `python3 achadinhos/carrossel.py achadinhos/roteiros/X.json /tmp/slides` e OLHAR os slides (texto cortado, foto ruim).
   Copiar para `postados-img/achadinhos/AAAA-MM-DD-TEMA-N.jpg`.
5. Legenda curta: lista dos 5, "Comenta QUERO que eu te mando no Direct o link do grupo", aviso de afiliado, 5 hashtags.
   Salvar em `achadinhos/legendas/AAAA-MM-DD.txt`.
6. Fila do WhatsApp: `python3 achadinhos/fila.py AAAA-MM-DD achadinhos/dia/<arquivos de hoje> --textos T.json`
   (8 ofertas, 09:00 a 21:30). Formato aprovado em 01/11 (modelo de grupo de promoções): T.json = {id: {emoji, titulo,
   modelo, specs}}, ex. {"emoji": "🎧", "titulo": "Fone bluetooth com 30h de bateria", "modelo": "Soundcore by Anker P20i",
   "specs": "Bluetooth 5.3 - Graves reforçados - Preto"}. Specs SÓ com dados dos atributos/destaques do produto.
   O script gera a arte amarela de cada oferta em achadinhos/ofertas/DATA/: OLHAR as artes (recorte ruim -> trocar produto).
7. Commit e `git push origin HEAD:main` (o PC lê a fila da main).
8. Publicar o carrossel: `modelo/scripts/publicar_carrossel.py achadinhos/legendas/AAAA-MM-DD.txt postados-img/achadinhos/...-1.jpg ...`
   (usa raw da main, por isso o push vem antes). Gravar o media id em `achadinhos/postados.json` e os ids em
   `achadinhos/usados.json`. Commit e push na main.
9. Registrar em achadinhos/log.md: tema, produtos, link do post. Se algo falhar, avisar o usuário no thread.

## QUERO (a cada 2 horas, 08h às 22h)
`python3 achadinhos/responder_quero.py`; se respondeu alguém, commit de `achadinhos/respondidos.json` na main.
Ler `whatsapp/status.json` na main para ver se algum comando falhou.

## Comandos do grupo
Escrever em `achadinhos/comandos.json` (formato em whatsapp/README.md), sempre com id novo, push na main.
O PC executa em até 1 minuto e devolve em `whatsapp/status.json`.
