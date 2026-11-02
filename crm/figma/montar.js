// Monta um post do @crmquevende no Figma (arquivo OfsjRUS67zWUEMJOJ9jYt3, componente base "Post / frase" 1:54).
// Uso: no use_figma, cole este arquivo inteiro trocando só a linha "const POSTS = [...]" pelos JSONs dos posts (crm/posts/<arq>.json + "_frame").
// Um post = [ {...} ]; carrossel = um objeto por slide, na ordem.
// Layouts: frase | data | numero | lista | chat | antes_depois. <palavras> entre < > ficam em lime.
// Cria (ou recria) um frame com o nome do post na página "Posts" e devolve o id para o get_screenshot.
const POSTS = [{"_frame": "teste", "layout": "frase", "rotulo": "", "headline": "Texto com <destaque>", "sub": "", "cta": "bio"}];

const c = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 });
const BG = c(11, 15, 20), LIME = c(198, 255, 61), TXT = c(245, 243, 238), MUTED = c(138, 148, 166),
  VERM = c(255, 92, 92), ROSA = c(255, 77, 196), VIDRO = c(24, 32, 46), CINZA = c(44, 52, 68);
const CORES = { lime: LIME, vermelho: VERM, rosa: ROSA, branco: TXT };
await Promise.all(['Black', 'Extra Bold', 'Bold', 'Semi Bold', 'Medium'].map(s => figma.loadFontAsync({ family: 'Inter', style: s })));
const glowFx = (col, a = 0.55, r = 28) => ({ type: 'DROP_SHADOW', color: { ...col, a }, offset: { x: 0, y: 0 }, radius: r, spread: 0, visible: true, blendMode: 'NORMAL' });
const solid = (col, opacity = 1) => [{ type: 'SOLID', color: col, opacity }];
function texto(txt, style, size, color, o = {}) {
  const t = figma.createText(); t.fontName = { family: 'Inter', style }; t.fontSize = size;
  const raw = o.upper ? txt.toUpperCase() : txt; const plain = raw.replace(/[<>]/g, '');
  t.characters = plain; t.fills = solid(color); t.textAlignHorizontal = o.align || 'CENTER';
  if (o.ls) t.letterSpacing = { unit: 'PIXELS', value: o.ls };
  if (o.lh) t.lineHeight = { unit: 'PERCENT', value: o.lh };
  let k = 0, ini = null; for (const ch of raw) { if (ch === '<') { ini = k; continue; } if (ch === '>') { t.setRangeFills(ini, k, solid(o.dest || LIME)); continue; } k++; }
  if (o.w) { t.resize(o.w, t.height); t.textAutoResize = 'HEIGHT'; }
  return t;
}
function caixa(dir, o = {}) {
  const f = figma.createAutoLayout(dir, { itemSpacing: o.gap ?? 0, paddingLeft: o.px ?? 0, paddingRight: o.px ?? 0, paddingTop: o.py ?? 0, paddingBottom: o.py ?? 0 });
  f.fills = o.fill ? solid(o.fill, o.op ?? 1) : []; if (o.r) f.cornerRadius = o.r;
  if (o.stroke) { f.strokes = solid(o.stroke, o.sop ?? 1); f.strokeWeight = o.sw ?? 2; }
  if (o.name) f.name = o.name; return f;
}
function fixa(f, w) { if (f.layoutMode === 'HORIZONTAL') { f.primaryAxisSizingMode = 'FIXED'; f.resize(w, f.height); f.counterAxisSizingMode = 'AUTO'; } else { f.counterAxisSizingMode = 'FIXED'; f.resize(w, f.height); } return f; }
function add(pai, filho, fill) { pai.appendChild(filho); if (fill) filho.layoutSizingHorizontal = 'FILL'; return filho; }
function icone(ok, size = 34) {
  const svg = ok
    ? `<svg width="${size}" height="${size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="1" width="22" height="22" rx="5" fill="#C6FF3D"/><path d="M6.5 12.5l3.5 3.5 7.5-8" stroke="#0B0F14" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`
    : `<svg width="${size}" height="${size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M6 6l12 12M18 6L6 18" stroke="#FF5C5C" stroke-width="3" fill="none" stroke-linecap="round"/></svg>`;
  return figma.createNodeFromSvg(svg);
}
function check(ok, size = 26) {
  const svg = ok
    ? `<svg width="${size}" height="${size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M4 12.5l5 5L20 6" stroke="#C6FF3D" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`
    : `<svg width="${size}" height="${size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M6 6l12 12M18 6L6 18" stroke="#FF5C5C" stroke-width="3" fill="none" stroke-linecap="round"/></svg>`;
  return figma.createNodeFromSvg(svg);
}

const comp = await figma.getNodeByIdAsync('1:54');
let pg = figma.root.children.find(p => p.name === 'Posts');
if (!pg) { pg = figma.createPage(); pg.name = 'Posts'; }
await figma.setCurrentPageAsync(pg);
const feitos = [];
for (const POST of POSTS) {
// ---- base: instância do componente, destacada ----
for (const n of pg.children.filter(n => n.name === POST._frame)) n.remove();
let maxX = -1200; for (const n of pg.children) maxX = Math.max(maxX, n.x + n.width);
const inst = comp.createInstance(); pg.appendChild(inst);
const post = inst.detachInstance(); post.name = POST._frame; post.x = maxX + 120; post.y = 0;
const col = post.findOne(n => n.name === 'conteudo');
const rot = col.findOne(n => n.name === 'rotulo'), head = col.findOne(n => n.name === 'headline'), sub = col.findOne(n => n.name === 'sub');
const L = POST.layout || 'frase';

// rótulo, headline, sub
if (POST.rotulo) { rot.characters = POST.rotulo.toUpperCase(); if (POST.cor_rotulo) rot.fills = solid(CORES[POST.cor_rotulo] || LIME); } else rot.remove();
const hraw = POST.headline.toUpperCase(), hplain = hraw.replace(/[<>]/g, '');
head.characters = hplain; head.fills = solid(TXT);
const nw = hplain.split(/\s+/).length;
const compacto = ['lista', 'chat', 'antes_depois'].includes(L);
head.fontSize = POST.tam || (compacto ? (nw <= 5 ? 92 : nw <= 9 ? 76 : 64) : (nw <= 4 ? 118 : nw <= 8 ? 104 : nw <= 13 ? 86 : 72));
{ let k = 0, ini = null; for (const ch of hraw) { if (ch === '<') { ini = k; continue; } if (ch === '>') { head.setRangeFills(ini, k, solid(LIME)); continue; } k++; } }
if (POST.sub) { sub.characters = POST.sub; } else sub.remove();
col.itemSpacing = compacto ? 40 : 44;

// bloco do layout
let bloco = null, antes = false;
if (L === 'data') {
  antes = true;
  bloco = caixa('VERTICAL', { name: 'calendario', r: 26, fill: TXT });
  bloco.counterAxisAlignItems = 'CENTER'; bloco.clipsContent = true;
  const topo = add(bloco, caixa('HORIZONTAL', { fill: LIME, py: 16, px: 30 }), false);
  topo.primaryAxisAlignItems = 'CENTER';
  add(topo, texto(POST.mes || '', 'Black', 34, BG, { upper: true }));
  const dia = add(bloco, caixa('HORIZONTAL', { py: 14, px: 30 }), false); dia.primaryAxisAlignItems = 'CENTER';
  add(dia, texto(String(POST.dia || ''), 'Black', 150, BG));
  fixa(bloco, 260); topo.layoutSizingHorizontal = 'FILL'; dia.layoutSizingHorizontal = 'FILL';
  bloco.rotation = -5; bloco.effects = [glowFx(LIME, 0.35, 40)];
} else if (L === 'numero') {
  const cor = CORES[POST.cor] || LIME;
  bloco = caixa('HORIZONTAL', { name: 'numero', px: 60, py: 40, r: 999, stroke: cor, sw: 4 });
  bloco.primaryAxisAlignItems = 'CENTER'; bloco.counterAxisAlignItems = 'CENTER';
  const t = add(bloco, texto(String(POST.numero), 'Black', String(POST.numero).length > 7 ? 130 : 160, cor));
  t.effects = [glowFx(cor, 0.7, 30)]; bloco.effects = [glowFx(cor, 0.45, 24)];
  // número vem entre o rótulo e a headline
  col.insertChild(POST.rotulo ? 1 : 0, bloco); bloco = null;
} else if (L === 'lista') {
  bloco = caixa('VERTICAL', { name: 'lista', gap: 18 });
  for (const it of POST.itens || []) {
    const card = add(bloco, caixa('HORIZONTAL', { gap: 22, px: 28, py: 24, r: 18, fill: VIDRO, op: 0.94, stroke: TXT, sop: 0.08, sw: 2 }), false);
    card.counterAxisAlignItems = 'CENTER';
    add(card, icone(it.ok !== false));
    const t = add(card, texto(it.t, 'Semi Bold', 34, TXT, { align: 'LEFT', lh: 125 }));
    t.layoutSizingHorizontal = 'FILL';
  }
  fixa(bloco, 860); for (const ch of bloco.children) ch.layoutSizingHorizontal = 'FILL';
} else if (L === 'chat') {
  bloco = caixa('VERTICAL', { name: 'chat', gap: 22, px: 30, py: 30, r: 28, fill: VIDRO, op: 0.96, stroke: TXT, sop: 0.08 });
  const top = add(bloco, caixa('HORIZONTAL', { gap: 16 }), false); top.counterAxisAlignItems = 'CENTER';
  const av = caixa('HORIZONTAL', { r: 999, fill: CORES[POST.cor] || ROSA }); av.primaryAxisAlignItems = 'CENTER'; av.counterAxisAlignItems = 'CENTER';
  av.primaryAxisSizingMode = 'FIXED'; av.counterAxisSizingMode = 'FIXED'; av.resize(56, 56);
  add(av, texto((POST.nome || '?')[0].toUpperCase(), 'Black', 28, BG)); add(top, av);
  const nm = add(top, caixa('VERTICAL', { gap: 2 }));
  add(nm, texto(POST.nome || '', 'Bold', 30, TXT, { align: 'LEFT' }));
  if (POST.status) add(nm, texto(POST.status, 'Medium', 20, MUTED, { align: 'LEFT' }));
  for (const m of POST.mensagens || []) {
    const eu = m.de === 'eu';
    const linha = add(bloco, caixa('HORIZONTAL'), false); linha.primaryAxisAlignItems = eu ? 'MAX' : 'MIN';
    const b = add(linha, caixa('VERTICAL', { gap: 6, px: 24, py: 16, r: 20, fill: eu ? LIME : CINZA }));
    b.counterAxisAlignItems = 'MAX';
    const tt = texto(m.texto, 'Medium', 30, eu ? BG : TXT, { align: 'LEFT', lh: 125 });
    if (tt.width > 500) { tt.resize(500, tt.height); tt.textAutoResize = 'HEIGHT'; }
    add(b, tt);
    if (m.meta) add(b, texto(m.meta, 'Medium', 18, eu ? BG : MUTED, { align: 'RIGHT' })).opacity = 0.7;
  }
  fixa(bloco, 860); for (const ch of bloco.children) ch.layoutSizingHorizontal = 'FILL';
  if (POST.carimbo) {
    const cor = CORES[POST.cor_carimbo] || VERM;
    const linha = add(bloco, caixa('HORIZONTAL', { py: 6 }), true); linha.primaryAxisAlignItems = 'CENTER';
    const st = add(linha, caixa('HORIZONTAL', { px: 26, py: 12, r: 12, stroke: cor, sw: 5 }));
    add(st, texto(POST.carimbo, 'Black', 46, cor, { upper: true }));
    st.rotation = -7; st.effects = [glowFx(cor, 0.4, 18)];
  }
} else if (L === 'antes_depois') {
  bloco = caixa('HORIZONTAL', { name: 'antes_depois', gap: 22 });
  const lado = (titulo, itens, ok) => {
    const cor = ok ? LIME : VERM;
    const cx = add(bloco, caixa('VERTICAL', { gap: 22, px: 26, py: 28, r: 22, fill: VIDRO, op: 0.94, stroke: cor, sop: 0.55, sw: 2 }));
    add(cx, texto(titulo, 'Extra Bold', 22, cor, { upper: true, ls: 3 }), false);
    for (const t of itens) {
      const ln = add(cx, caixa('HORIZONTAL', { gap: 12 }), false);
      add(ln, check(ok)); const tx = add(ln, texto(t, 'Semi Bold', 27, TXT, { align: 'LEFT', lh: 125 })); tx.layoutSizingHorizontal = 'FILL';
    }
    return cx;
  };
  const a = lado(POST.titulo_antes || 'Antes', POST.antes || [], false), d = lado(POST.titulo_depois || 'Depois', POST.depois || [], true);
  fixa(bloco, 900);
  for (const cx of [a, d]) { cx.layoutSizingHorizontal = 'FILL'; cx.layoutAlign = 'STRETCH'; for (const ch of cx.children) ch.layoutSizingHorizontal = 'FILL'; }
}
if (bloco) { if (antes) col.insertChild(0, bloco); else col.appendChild(bloco); }

// CTA
const pal = (POST.palavra || 'FUNIL').toUpperCase();
const CTA = { direct: `MANDA ${pal} NO DIRECT`, bio: 'LINK NA BIO', comenta: `COMENTA ${pal}`, arrasta: 'ARRASTA PRO LADO', salva: 'SALVA ESSE POST' };
post.findOne(n => n.name === 'cta_texto').characters = CTA[POST.cta] || String(POST.cta || '').toUpperCase();
const pill = post.findOne(n => n.name === 'cta'); pill.x = 1080 - 70 - pill.width;

feitos.push({ id: post.id, nome: post.name, altura_conteudo: Math.round(col.height) });
await post.screenshot({ scale: 0.4 });
}
return feitos;
