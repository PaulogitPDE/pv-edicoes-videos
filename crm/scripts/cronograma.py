"""Monta o cronograma do @crmquevende: 2 reels + 2 posts por dia, sem exceção, mais o post de trend (seg/qua/sex).
Uso (na raiz do repo): python3 crm/scripts/cronograma.py 2026-11  [primeiro-dia]
Grava crm/calendario/AAAA-MM.json. Os temas vêm de crm/scripts/temas.py; datas comemorativas viram reel 1 + post 1."""
import calendar, datetime as dt, json, os, sys

sys.path.insert(0, os.path.dirname(__file__))
from temas import DATAS, PILARES, POSTS_DIA, POSTS_EDU, REELS_DIA, REELS_OFERTA

HORAS = {'p1': '08:37', 'r1': '12:17', 'p2': '17:37', 'r2': '19:57', 'trend': '10:27'}
CTAS = ['direct', 'bio', 'comenta']
SEMANA = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']

ano, mes = map(int, sys.argv[1].split('-'))
inicio = int(sys.argv[2]) if len(sys.argv) > 2 else 1
dias = []
for d in range(inicio, calendar.monthrange(ano, mes)[1] + 1):
    data = dt.date(ano, mes, d)
    wd, sem = data.weekday(), data.toordinal() // 7
    n = data.toordinal()
    cta = lambda k: CTAS[(n * 4 + k) % 3]
    r_dia, r_of = REELS_DIA[wd][sem % 6], REELS_OFERTA[n % len(REELS_OFERTA)]
    p_dia, p_edu = POSTS_DIA[wd][(sem + 3) % 6], POSTS_EDU[(n + 5) % len(POSTS_EDU)]
    item = {'data': data.isoformat(), 'semana': SEMANA[wd], 'pilar': PILARES[wd], 'data_comemorativa': None,
            'p1': {'hora': HORAS['p1'], 'tema': p_dia[0], 'layout': p_dia[1], 'cta': cta(0)},
            'r1': {'hora': HORAS['r1'], 'tema': r_dia[0], 'cenas': r_dia[1], 'cta': cta(1)},
            'p2': {'hora': HORAS['p2'], 'tema': p_edu[0], 'layout': p_edu[1], 'cta': cta(2)},
            'r2': {'hora': HORAS['r2'], 'tema': r_of[0], 'cenas': r_of[1], 'cta': cta(3)}}
    if (d, mes) in DATAS:
        nome, angulo = DATAS[(d, mes)]
        item['data_comemorativa'] = nome
        item['p1'].update(tema=f'{nome}: {angulo}', layout='data')
        item['r1'].update(tema=f'{nome}: {angulo}', cenas='data, gancho, (cena do tema), cta')
    if wd in (0, 2, 4):
        item['trend'] = {'hora': HORAS['trend'], 'tema': 'pesquisar no dia o assunto do momento e ligar ao CRM que vende (estilo gancho "nada a ver")', 'cta': cta(4)}
    dias.append(item)
saida = f'crm/calendario/{ano}-{mes:02d}.json'
json.dump({'mes': f'{ano}-{mes:02d}', 'horarios_brt': HORAS, 'dias': dias}, open(saida, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', saida, len(dias), 'dias')
