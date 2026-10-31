# Achadinhos (@pvedicoes, estratégia de 30/10)

1. `python3 achadinhos/escolher.py casa 8` busca os mais vendidos das categorias do tema, aplica os filtros anti-golpe
   (ver topo do arquivo) e grava `achadinhos/dia/AAAA-MM-DD-tema.json` com preço, vendedor, fotos e link de afiliado.
   Temas: casa, cozinha, tech, setup, beleza, carro.
2. Claude escolhe 5 dos aprovados (os mais "uau", sem produto de consumo comum tipo sabão) e escreve
   `achadinhos/roteiros/AAAA-MM-DD-tema.json` (nome curto, benefício, texto da pílula, foto do anúncio).
3. `python3 achadinhos/carrossel.py achadinhos/roteiros/....json pasta/` gera os slides (capa + produtos + CTA QUERO).

Limites da API com token de app (31/10): avaliações e nº de vendidos do anúncio dão 403, então a nota NÃO é checada;
o filtro usa "mais vendido da categoria" + vendedor verde e loja oficial/MercadoLíder 1.000+ vendas.
Fotos dos anúncios ficam em `achadinhos/cache/` (fora do git). `precos.json` guarda o histórico para validar desconto.
