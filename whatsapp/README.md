# Envio automático no grupo de WhatsApp (roda no PC)

A nuvem escolhe as ofertas e publica a fila do dia em `achadinhos/fila/AAAA-MM-DD.json` (branch `main`).
Este programa roda no PC do Pv, confere a fila a cada minuto e manda cada oferta no grupo quando chega o horário dela.
O PC precisa ficar ligado e com a janela aberta nos horários das ofertas.

## Instalação (uma vez)
1. Ter o Node.js 20 ou mais novo (`node -v`).
2. Nesta pasta: `npm install`
3. `copy config.exemplo.json config.json`
4. `node enviador.js grupos` e escanear o QR code com o WhatsApp do **chip do grupo**
   (WhatsApp > Aparelhos conectados > Conectar aparelho). Copiar o ID do grupo (termina em `@g.us`) para `grupo_id` no `config.json`.
5. `node enviador.js teste` manda uma mensagem de teste no grupo.

## Uso diário
Dar dois cliques em `iniciar.bat` (ou colocar um atalho dele em `shell:startup` para abrir junto com o Windows).

## Formato da fila (gerada pela nuvem)
```json
{
  "data": "2026-11-01",
  "ofertas": [
    {
      "id": "MLB53222689",
      "hora": "09:00",
      "imagem": "https://http2.mlstatic.com/D_NQ_NP_....jpg",
      "texto": "*Kit 10 potes de vidro Starhouse*\nVai do freezer ao forno.\n\nR$ 92,08 no Pix\n\n👉 https://www.mercadolivre.com.br/p/MLB53222689?matt_word=paulovitorlemes&matt_tool=37931087"
    }
  ]
}
```
- `hora` em horário de Brasília, `HH:MM`. Ofertas atrasadas (PC desligado na hora) saem assim que o programa abre, com pelo menos `intervalo_min_segundos` entre uma e outra.
- `enviados.json` guarda o que já saiu, então reiniciar não repete oferta.
- Sessão do WhatsApp fica em `auth/` (não vai para o git). Se o celular desconectar, apagar `auth/` e escanear de novo.

## Cuidados
- Usar um número só para o grupo, nunca o pessoal: a conexão não é oficial e o WhatsApp pode banir números que mandam demais.
- Manter poucas mensagens por hora (a rotina planeja 8 por dia).
