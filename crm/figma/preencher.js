// Cola este código no use_figma (arquivo OfsjRUS67zWUEMJOJ9jYt3), trocando só o objeto POST.
// Cria uma instância do componente "Post / frase" (1:54) na página "Posts", preenche e devolve o id para exportar.
// <palavras> entre sinais de menor/maior ficam em lime. rotulo/sub vazios = escondidos.
const POST = {nome: 'AAAA-MM-DD-p1', rotulo: 'tá todo mundo falando', headline: 'Texto com <destaque>', sub: '', cta: 'bio', palavra: 'FUNIL'};
const LIME = {r:198/255,g:1,b:61/255};
const CTA = {direct:`MANDA ${POST.palavra||'FUNIL'} NO DIRECT`, bio:'LINK NA BIO', comenta:`COMENTA ${POST.palavra||'FUNIL'}`, arrasta:'ARRASTA PRO LADO', salva:'SALVA ESSE POST'};
await Promise.all(['Black','Bold','Medium'].map(s=>figma.loadFontAsync({family:'Inter',style:s})));
const comp = await figma.getNodeByIdAsync('1:54');
let pg = figma.root.children.find(p=>p.name==='Posts');
if(!pg){ pg = figma.createPage(); pg.name='Posts'; }
await figma.setCurrentPageAsync(pg);
const old = pg.children.find(n=>n.name===POST.nome); if(old) old.remove();
let maxY = 0; for(const n of pg.children) maxY = Math.max(maxY, n.y + n.height);
const inst = comp.createInstance(); pg.appendChild(inst); inst.name = POST.nome; inst.x = 0; inst.y = pg.children.length>1 ? maxY+200 : 0;
const T = n => inst.findOne(x=>x.type==='TEXT' && x.name===n);
const raw = POST.headline.toUpperCase(); const plain = raw.replace(/[<>]/g,'');
const h = T('headline'); h.characters = plain;
const n = plain.split(/\s+/).length; h.fontSize = n<=4?118:n<=8?104:n<=13?86:72;
let i=0, k=0, ini=null; for(const ch of raw){ if(ch==='<'){ini=k;continue;} if(ch==='>'){h.setRangeFills(ini,k,[{type:'SOLID',color:LIME}]);continue;} k++; }
const r = T('rotulo'); if(POST.rotulo){ r.characters = POST.rotulo.toUpperCase(); } else r.visible=false;
const s = T('sub'); if(POST.sub){ s.characters = POST.sub; } else s.visible=false;
T('cta_texto').characters = CTA[POST.cta] || POST.cta.toUpperCase();
await inst.screenshot({scale:0.5});
return {id: inst.id, nome: inst.name};
