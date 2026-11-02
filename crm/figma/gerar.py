"""Gera o código do use_figma para montar posts no Figma.
Uso: python3 crm/figma/gerar.py crm/posts/2026-11-03-p1.json [slide2.json ...] > /tmp/.../codigo.js
Cada JSON vira um frame com o nome do arquivo (sem .json) na página "Posts" do arquivo OfsjRUS67zWUEMJOJ9jYt3."""
import json, os, sys
aqui = os.path.dirname(os.path.abspath(__file__))
posts = []
for f in sys.argv[1:]:
    p = json.load(open(f)); p['_frame'] = os.path.basename(f)[:-5]; posts.append(p)
linhas = [l for l in open(os.path.join(aqui, 'montar.js')).read().split('\n') if not l.startswith('//')]
linhas = [('const POSTS = ' + json.dumps(posts, ensure_ascii=False) + ';') if l.startswith('const POSTS =') else l for l in linhas]
print('\n'.join(linhas).strip())
