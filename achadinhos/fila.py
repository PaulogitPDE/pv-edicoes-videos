"""Monta a fila de ofertas do grupo de WhatsApp (formato em whatsapp/README.md).
Uso (na raiz do repo): python3 achadinhos/fila.py AAAA-MM-DD achadinhos/dia/X.json [achadinhos/dia/Y.json ...] [--textos T.json]
Pega até 8 produtos aprovados pelo escolher.py, alternando os temas, fora dos usados nos últimos 14 dias,
e grava achadinhos/fila/AAAA-MM-DD.json. --textos = {id: {nome, texto}} com nome curto e frase escritos pela rotina;
sem ele usa o nome do anúncio encurtado e o primeiro destaque. Marca os escolhidos em achadinhos/usados.json."""
import datetime as dt
import json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
HORAS = ['09:00', '11:00', '13:00', '15:00', '18:00', '19:30', '20:30', '21:30']
DIAS_SEM_REPETIR = 14


def brl(v):
    return 'R$ ' + f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def curto(nome, n=60):
    return nome if len(nome) <= n else nome[:n].rsplit(' ', 1)[0].rstrip(' -,|')


def texto(p, t):
    nome = t.get('nome') or curto(p['nome'])
    frase = t.get('texto') or (p['destaques'][0] if p['destaques'] else '')
    if p.get('desconto_verificado') and p.get('preco_de'):
        preco = f"De {brl(p['preco_de'])} por *{brl(p['preco'])}* ({p['desconto_pct']}% off)"
    else:
        preco = f"*{brl(p['preco'])}*"
    frete = 'Frete grátis' if p['frete'] == 'grátis' else 'Entrega Full'
    return f"*{nome}*\n{frase}\n\n{preco} · {frete}\n\n👉 {p['link']}"


def main():
    args = sys.argv[1:]
    textos = {}
    if '--textos' in args:
        i = args.index('--textos')
        textos = json.load(open(args[i + 1]))
        del args[i:i + 2]
    data, arquivos = args[0], args[1:]
    usados_path = os.path.join(AQUI, 'usados.json')
    usados = json.load(open(usados_path)) if os.path.exists(usados_path) else {}
    limite = (dt.date.fromisoformat(data) - dt.timedelta(days=DIAS_SEM_REPETIR)).isoformat()
    listas = [json.load(open(a))['produtos'] for a in arquivos]
    escolhidos, vistos = [], set()
    for k in range(max(map(len, listas), default=0)):
        for l in listas:
            if k < len(l) and len(escolhidos) < len(HORAS):
                p = l[k]
                if p['id'] in vistos or usados.get(p['id'], '') >= limite:
                    continue
                vistos.add(p['id'])
                escolhidos.append(p)
    ofertas = [{'id': p['id'], 'hora': h, 'imagem': p['fotos'][0], 'texto': texto(p, textos.get(p['id'], {}))}
               for p, h in zip(escolhidos, HORAS)]
    for p in escolhidos:
        usados[p['id']] = data
    json.dump(usados, open(usados_path, 'w'), ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(AQUI, 'fila'), exist_ok=True)
    saida = os.path.join(AQUI, 'fila', f'{data}.json')
    json.dump({'data': data, 'ofertas': ofertas}, open(saida, 'w'), ensure_ascii=False, indent=1)
    print(f'{len(ofertas)} ofertas em {saida}')


if __name__ == '__main__':
    main()
