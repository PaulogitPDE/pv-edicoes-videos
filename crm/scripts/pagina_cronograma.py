"""Gera a página do cronograma (artefato "Cronograma CRM que vende") a partir de crm/calendario/*.json.
Uso (na raiz do repo): python3 crm/scripts/pagina_cronograma.py  → crm/calendario/cronograma.html (publicar com a ferramenta Artifact)."""
import glob, json

meses = [json.load(open(p, encoding='utf-8')) for p in sorted(glob.glob('crm/calendario/20*.json'))]
dados = json.dumps(meses, ensure_ascii=False)

html = r'''<title>Cronograma CRM que vende</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Figtree:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap">
<style>
/* Agenda por semana: cada dia é uma linha com a data à esquerda e as publicações do dia em colunas por horário. */
:root {
  --bg: #0b0f14; --panel: #121a26; --panel2: #18222f; --line: #263244;
  --fg: #f2f0ea; --muted: #8d97a8; --lime: #c6ff3d; --cyan: #3de0ff; --pink: #ff4dc4; --red: #ff6b6b;
  --f-display: "Bricolage Grotesque", "Figtree", system-ui, sans-serif;
  --f-body: "Figtree", system-ui, sans-serif;
  --f-mono: "JetBrains Mono", ui-monospace, monospace;
  color-scheme: dark;
}
body { background: var(--bg); color: var(--fg); font: 15px/1.45 var(--f-body); }
.wrap { max-width: 1240px; margin: 0 auto; padding-block: 28px 64px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); display: grid; gap: 22px; }
header { display: grid; gap: 10px; }
.eyebrow { font: 600 12px var(--f-mono); letter-spacing: .14em; text-transform: uppercase; color: var(--lime); display: flex; align-items: center; gap: 8px; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--lime); box-shadow: 0 0 10px var(--lime); animation: blink 1.6s infinite; }
@keyframes blink { 50% { opacity: .25 } }
@media (prefers-reduced-motion: reduce) { .dot { animation: none } }
h1 { font: 800 clamp(30px, 5vw, 52px)/1.02 var(--f-display); margin: 0; text-wrap: balance; letter-spacing: -.02em; }
h1 em { font-style: normal; color: var(--lime); }
.lede { color: var(--muted); max-width: 70ch; margin: 0; }
.regras { display: flex; flex-wrap: wrap; gap: 8px; }
.regras span { border: 1px solid var(--line); border-radius: 999px; padding: 5px 12px; font-size: 13px; color: var(--muted); }
.regras b { color: var(--fg); font-weight: 600; }
.tabs { display: flex; gap: 8px; flex-wrap: wrap; }
.tabs button { font: 600 14px var(--f-body); color: var(--muted); background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 8px 16px; cursor: pointer; }
.tabs button[aria-pressed="true"] { color: #0b0f14; background: var(--lime); border-color: var(--lime); }
.tabs button:focus-visible, .filtro:focus-visible { outline: 2px solid var(--cyan); outline-offset: 2px; }
.legenda { display: flex; flex-wrap: wrap; gap: 14px; font-size: 13px; color: var(--muted); align-items: center; }
.cta { font: 600 11px var(--f-mono); letter-spacing: .06em; text-transform: uppercase; border-radius: 6px; padding: 2px 7px; white-space: nowrap; }
.cta.direct { background: rgba(198,255,61,.14); color: var(--lime); }
.cta.bio { background: rgba(61,224,255,.14); color: var(--cyan); }
.cta.comenta { background: rgba(255,77,196,.15); color: var(--pink); }
.cta.salva { background: rgba(255,255,255,.08); color: var(--muted, #9aa4b2); }
.semana { display: grid; gap: 8px; }
.semana h2 { font: 600 12px var(--f-mono); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin: 10px 0 0; }
.dia { display: grid; grid-template-columns: 150px 1fr; gap: 14px; background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 14px; }
.dia.especial { border-color: var(--lime); box-shadow: 0 0 0 1px var(--lime) inset, 0 0 24px rgba(198,255,61,.12); }
.dia.hoje { outline: 2px solid var(--cyan); outline-offset: 3px; }
.data { display: grid; align-content: start; gap: 4px; }
.data .num { font: 800 34px/1 var(--f-display); font-variant-numeric: tabular-nums; }
.data .sem { font-weight: 600; text-transform: capitalize; }
.data .pilar { font-size: 12.5px; color: var(--muted); }
.badge { justify-self: start; font: 700 11px var(--f-mono); letter-spacing: .05em; text-transform: uppercase; color: #0b0f14; background: var(--lime); padding: 3px 8px; border-radius: 6px; margin-top: 4px; }
.badge.hoje { background: var(--cyan); }
.slots { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 8px; min-width: 0; }
.slot { background: var(--panel2); border: 1px solid var(--line); border-radius: 10px; padding: 10px 11px; display: grid; gap: 6px; align-content: start; min-width: 0; }
.slot.data-com { border-color: rgba(198,255,61,.55); }
.slot.trend { border-style: dashed; border-color: rgba(255,77,196,.6); }
.topo { display: flex; justify-content: space-between; align-items: center; gap: 6px; }
.tipo { font: 600 12px var(--f-mono); color: var(--muted); }
.tipo b { color: var(--fg); font-weight: 600; }
.tema { font-weight: 600; line-height: 1.3; overflow-wrap: anywhere; }
.fmt { font-size: 12.5px; color: var(--muted); }
.vazio { color: var(--muted); }
@media (max-width: 680px) { .dia { grid-template-columns: 1fr; } .data { grid-template-columns: auto 1fr; align-items: baseline; column-gap: 10px; } .data .pilar, .badge { grid-column: 1 / -1; } }
</style>

<div class="wrap">
  <header>
    <div class="eyebrow"><span class="dot"></span>@crmquevende · no automático</div>
    <h1>Cronograma <em>CRM que vende</em></h1>
    <p class="lede">Todo dia, sem exceção: 2 reels e 1 post (desde 29/10). O reel 1 é só conteúdo, sem venda; o reel 2 leva a oferta Orçamento que Volta. Nas datas comemorativas, o reel 1 e o post 1 são da data. Segunda, quarta e sexta tem um carrossel extra com o assunto da semana na capa. O tema de cada peça vira roteiro no próprio dia.</p>
    <div class="regras">
      <span><b>08h37</b> post 1</span><span><b>10h27</b> trend (seg/qua/sex)</span><span><b>12h17</b> reel 1</span><span><b>17h37</b> post 2</span><span><b>19h57</b> reel 2</span>
    </div>
  </header>
  <div class="tabs" id="tabs" role="group" aria-label="Mês"></div>
  <div class="legenda">
    <span><span class="cta direct">Direct</span> manda FUNIL no Direct</span>
    <span><span class="cta bio">Bio</span> link na bio (WhatsApp)</span>
    <span><span class="cta comenta">Comenta</span> comenta FUNIL</span>
  </div>
  <main id="lista"></main>
</div>

<script>
const MESES = __DADOS__;
const NOMES = {'01':'Janeiro','02':'Fevereiro','03':'Março','04':'Abril','05':'Maio','06':'Junho','07':'Julho','08':'Agosto','09':'Setembro','10':'Outubro','11':'Novembro','12':'Dezembro'};
const CTA = {direct: 'Direct', bio: 'Bio', comenta: 'Comenta', salva: 'Sem venda'};
const LAYOUT = {frase: 'post de frase', data: 'post de data', chat: 'print de conversa', numero: 'post de número', lista: 'checklist', antes_depois: 'antes x depois'};
const hoje = new Date(Date.now() - 3 * 3600e3).toISOString().slice(0, 10);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));

function slot(tipo, nome, s, extra) {
  const fmt = s.layout ? (LAYOUT[s.layout] || s.layout) : (s.cenas ? 'cenas: ' + s.cenas : '');
  return `<div class="slot ${extra || ''}"><div class="topo"><span class="tipo"><b>${s.hora}</b> · ${nome}</span><span class="cta ${s.cta}">${CTA[s.cta] || s.cta}</span></div>
    <div class="tema">${esc(s.tema)}</div>${fmt ? `<div class="fmt">${esc(fmt)}</div>` : ''}</div>`;
}

function render(i) {
  const m = MESES[i];
  document.querySelectorAll('#tabs button').forEach((b, k) => b.setAttribute('aria-pressed', k === i));
  let html = '', semana = null;
  for (const d of m.dias) {
    const dt = new Date(d.data + 'T12:00:00');
    const seg = new Date(dt); seg.setDate(dt.getDate() - ((dt.getDay() + 6) % 7));
    const chave = seg.toISOString().slice(0, 10);
    if (chave !== semana) {
      if (semana) html += '</section>';
      html += `<section class="semana"><h2>Semana de ${seg.getDate()}/${seg.getMonth() + 1}</h2>`;
      semana = chave;
    }
    const esp = !!d.data_comemorativa, eh = d.data === hoje;
    const slots = [slot('p', 'post 1', d.p1, esp ? 'data-com' : '')];
    if (d.trend) slots.push(slot('t', 'trend', d.trend, 'trend'));
    slots.push(slot('r', d.r1.conteudo ? 'reel 1 · conteúdo' + (d.r1.tarja === false ? ', sem tarja' : '') : 'reel 1', d.r1, esp ? 'data-com' : ''), ...(d.p2 ? [slot('p', 'post 2', d.p2)] : []), slot('r', 'reel 2', d.r2));
    html += `<article class="dia ${esp ? 'especial' : ''} ${eh ? 'hoje' : ''}" id="d${d.data}">
      <div class="data"><span class="num">${d.data.slice(8)}/${d.data.slice(5, 7)}</span><span class="sem">${d.semana}</span>
      <span class="pilar">${esc(d.pilar)}</span>${esp ? `<span class="badge">${esc(d.data_comemorativa)}</span>` : ''}${eh ? '<span class="badge hoje">hoje</span>' : ''}</div>
      <div class="slots">${slots.join('')}</div></article>`;
  }
  html += '</section>';
  document.getElementById('lista').innerHTML = html;
}

const tabs = document.getElementById('tabs');
MESES.forEach((m, i) => {
  const b = document.createElement('button');
  b.type = 'button'; b.id = 'mes-' + m.mes;
  const [a, mm] = m.mes.split('-');
  b.textContent = `${NOMES[mm]} ${a}` + (m.dias[0].data.slice(8) !== '01' ? ` (a partir de ${m.dias[0].data.slice(8)})` : '');
  b.onclick = () => render(i);
  tabs.appendChild(b);
});
let ini = MESES.findIndex(m => hoje.startsWith(m.mes));
render(ini < 0 ? 0 : ini);
</script>
'''
open('crm/calendario/cronograma.html', 'w', encoding='utf-8').write(html.replace('__DADOS__', dados))
print('ok crm/calendario/cronograma.html')
