// Achadinhos do PV na nuvem: WhatsApp (Baileys) + painel web + fila + busca automática no Mercado Livre.
// Roda 24h num servidor (systemd reinicia se cair). Configuração em variáveis de ambiente (/etc/achadinhos.env):
//   PAINEL_SENHA, ML_CLIENT_ID, ML_CLIENT_SECRET, BASE_URL (https://...), PORT (3000), DADOS (/var/lib/achadinhos)
// Nada de segredo vai para o repositório: sessão do WhatsApp, tokens e fila ficam na pasta DADOS.
import fs from 'node:fs'
import path from 'node:path'
import http from 'node:http'
import crypto from 'node:crypto'
import { execFile } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import pino from 'pino'
import QRCode from 'qrcode'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const REPO = path.resolve(AQUI, '..')
const DADOS = process.env.DADOS || path.join(AQUI, 'dados')
const PORT = Number(process.env.PORT || 3000)
const BASE_URL = (process.env.BASE_URL || `http://localhost:${PORT}`).replace(/\/$/, '')
const SENHA = process.env.PAINEL_SENHA || ''
const RAW = 'https://raw.githubusercontent.com/PaulogitPDE/pv-edicoes-videos/main/'
const AFILIADO = 'matt_word=paulovitorlemes&matt_tool=37931087'
const HORAS_AUTO = ['09:00', '11:00', '13:00', '15:00', '18:00', '19:30', '20:30', '21:30']
// tema do dia (0 = domingo); a busca mistura com um segundo tema para não faltar produto
const TEMAS = ['casa', 'casa', 'tech', 'cozinha', 'setup', 'beleza', 'carro']
const MISTURA = { casa: 'cozinha', tech: 'casa', cozinha: 'casa', setup: 'tech', beleza: 'casa', carro: 'casa' }

fs.mkdirSync(path.join(DADOS, 'fila'), { recursive: true })
if (!SENHA) console.log('AVISO: PAINEL_SENHA vazia, o painel fica sem senha')

// ---------- arquivos ----------
const arq = n => path.join(DADOS, n)
function ler(n, padrao) { try { return JSON.parse(fs.readFileSync(arq(n), 'utf8')) } catch { return padrao } }
function salvar(n, v) { const f = arq(n); fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f + '.tmp', JSON.stringify(v, null, 1)); fs.renameSync(f + '.tmp', f) }

const CONFIG_PADRAO = { grupos: ['120363411602138203@g.us'], pausado: false, busca_auto: true, hora_busca: '07:00', intervalo_seg: 90, atraso_max_min: 90 }
const config = () => ({ ...CONFIG_PADRAO, ...ler('config.json', {}) })
const mudarConfig = p => salvar('config.json', { ...config(), ...p })

const eventos = []
function log(msg) {
  const l = `${agora().data} ${agora().hora} ${msg}`
  console.log(l); eventos.unshift(l); if (eventos.length > 200) eventos.pop()
}

function agora() {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false, weekday: 'short' }).formatToParts(new Date()).map(x => [x.type, x.value]))
  const dia = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(p.weekday)
  return { data: `${p.year}-${p.month}-${p.day}`, hora: `${p.hour === '24' ? '00' : p.hour}:${p.minute}`, dia }
}
const espera = ms => new Promise(r => setTimeout(r, ms))
const minutos = h => { const [a, b] = h.split(':').map(Number); return a * 60 + b }

// ---------- fila ----------
// fila do servidor (busca automática + ofertas manuais) em DADOS/fila/DATA.json; se não existir, usa a do repo (rotina do Claude)
async function filaDoDia(data) {
  const local = ler(`fila/${data}.json`, null)
  if (local) return { ...local, origem: 'servidor' }
  try {
    const r = await fetch(`${RAW}achadinhos/fila/${data}.json?t=${Date.now()}`)
    if (r.ok) return { ...(await r.json()), origem: 'repositorio' }
  } catch {}
  return { data, ofertas: [], origem: 'vazia' }
}
async function filaEditavel(data) {
  // ao editar, a fila do repo vira cópia local para as mudanças valerem
  const f = await filaDoDia(data)
  return { data, ofertas: f.ofertas || [] }
}
const enviados = () => ler('enviados.json', {})
function marcarEnviado(chave, valor) { const e = enviados(); e[chave] = valor; salvar('enviados.json', e) }

function comAfiliado(link) {
  try {
    const u = new URL(link.trim())
    if (/mercadoli(vre|bre)\.com/.test(u.hostname) && !u.searchParams.has('matt_word')) {
      for (const [k, v] of new URLSearchParams(AFILIADO)) u.searchParams.set(k, v)
    }
    return u.toString()
  } catch { return link.trim() }
}
const brl = v => 'R$ ' + Number(v).toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.')
function precoNum(s) { if (s === undefined || s === null || s === '') return null; const n = Number(String(s).replace(/[^\d,.]/g, '').replace(/\.(?=\d{3})/g, '').replace(',', '.')); return isFinite(n) && n > 0 ? n : null }

// mesmo formato do achadinhos/fila.py (aprovado pelo usuário em 01/11)
function textoOferta(o) {
  const l = [`${o.emoji || '🔥'} *${(o.titulo || '').toUpperCase()}*`, '']
  if (o.modelo) l.push(`*${o.modelo}*`, '')
  if (o.specs) l.push(o.specs, '')
  const de = precoNum(o.de), por = precoNum(o.por)
  if (de && por && de > por) l.push(`~De: ${brl(de)}~`)
  if (por) l.push(`*Por: ${brl(por)}*`, '')
  l.push('Link para compra:', comAfiliado(o.link), '', '📌 Anúncio | Preços podem subir rapidamente')
  return l.join('\n')
}

// ---------- WhatsApp ----------
let B = null, sock = null, qrAtual = null, estadoWa = 'desconectado', reconectando = false
const enviadasCache = new Map(), gruposCache = new Map()

async function conectarWa() {
  B = B || await import('@whiskeysockets/baileys')
  const makeWASocket = B.makeWASocket || B.default
  const logger = pino({ level: 'warn' }, pino.destination({ dest: arq('baileys.log'), sync: false }))
  const { state, saveCreds } = await B.useMultiFileAuthState(arq('auth'))
  let version
  try { version = (await B.fetchLatestBaileysVersion()).version } catch {}
  estadoWa = 'conectando'
  const s = makeWASocket({
    ...(version ? { version } : {}), logger,
    auth: { creds: state.creds, keys: B.makeCacheableSignalKeyStore(state.keys, logger) },
    getMessage: async k => enviadasCache.get(k.id),
    cachedGroupMetadata: async jid => gruposCache.get(jid),
    markOnlineOnConnect: false,
  })
  sock = s
  s.ev.on('creds.update', saveCreds)
  const atualizaGrupo = async id => { try { gruposCache.set(id, await s.groupMetadata(id)) } catch {} }
  s.ev.on('groups.update', ([ev]) => atualizaGrupo(ev.id))
  s.ev.on('group-participants.update', ev => atualizaGrupo(ev.id))
  s.ev.on('connection.update', async u => {
    if (u.qr) { qrAtual = await QRCode.toDataURL(u.qr, { margin: 1, width: 300 }); estadoWa = 'aguardando QR' }
    if (u.connection === 'open') {
      qrAtual = null; estadoWa = 'conectado'; log('WhatsApp conectado')
      for (const g of config().grupos) atualizaGrupo(g)
    }
    if (u.connection === 'close') {
      const codigo = u.lastDisconnect?.error?.output?.statusCode
      estadoWa = 'desconectado'; sock = null
      if (codigo === B.DisconnectReason.loggedOut) {
        log('WhatsApp desconectado pelo celular: gerando QR novo')
        fs.rmSync(arq('auth'), { recursive: true, force: true })
      } else log(`conexão caiu (${codigo}), reconectando`)
      reconectar()
    }
  })
}
async function reconectar() {
  if (reconectando) return
  reconectando = true
  await espera(5000)
  reconectando = false
  conectarWa().catch(e => { log('erro ao conectar: ' + e.message); reconectar() })
}

async function enviar(jid, conteudo) {
  if (!sock || estadoWa !== 'conectado') throw new Error('WhatsApp não está conectado')
  const m = await sock.sendMessage(jid, conteudo)
  if (m?.key?.id && m.message) {
    enviadasCache.set(m.key.id, m.message)
    if (enviadasCache.size > 500) enviadasCache.delete(enviadasCache.keys().next().value)
  }
  return m
}
async function imagemDaOferta(o, data) {
  const local = path.join(DADOS, 'ofertas', data, `${o.id}.jpg`)
  if (fs.existsSync(local)) return fs.readFileSync(local)
  if (!o.imagem) return null
  try { const r = await fetch(o.imagem); if (r.ok) return Buffer.from(await r.arrayBuffer()) } catch {}
  return null
}
async function enviarParaGrupos(texto, imagem) {
  const grupos = config().grupos
  if (!grupos.length) throw new Error('nenhum grupo marcado para receber')
  for (const [i, g] of grupos.entries()) {
    if (i) await espera(4000 + Math.random() * 4000)
    await enviar(g, imagem ? { image: imagem, caption: texto } : { text: texto })
  }
}
async function enviarOferta(o, data) {
  await enviarParaGrupos(o.texto, await imagemDaOferta(o, data))
  marcarEnviado(`${data}:${o.id}`, new Date().toISOString())
  log(`oferta enviada: ${o.texto.split('\n')[0].slice(0, 60)}`)
}

// ---------- agendador ----------
let ultimoEnvio = 0, rodandoCiclo = false
async function ciclo() {
  if (rodandoCiclo) return
  rodandoCiclo = true
  try {
    const c = config(), { data, hora, dia } = agora()
    if (c.busca_auto && hora >= c.hora_busca && ler('busca.json', {}).data !== data && !ler(`fila/${data}.json`, null) && mlConectado()) {
      await buscarProdutos(TEMAS[dia]).catch(e => log('busca automática falhou: ' + e.message))
    }
    if (c.pausado || estadoWa !== 'conectado') return
    const fila = await filaDoDia(data), env = enviados()
    for (const o of fila.ofertas || []) {
      const chave = `${data}:${o.id}`
      if (env[chave] || o.hora > hora) continue
      if (minutos(hora) - minutos(o.hora) > c.atraso_max_min) { marcarEnviado(chave, 'perdida (servidor fora do ar no horário)'); continue }
      const falta = c.intervalo_seg * 1000 - (Date.now() - ultimoEnvio)
      if (falta > 0) await espera(falta)
      try { await enviarOferta(o, data) } catch (e) { log('falha ao enviar: ' + e.message); break }
      ultimoEnvio = Date.now()
    }
  } catch (e) { log('erro no ciclo: ' + e.message) } finally { rodandoCiclo = false }
}

// ---------- Mercado Livre (OAuth da conta do usuário) ----------
const ML_REDIRECT = `${BASE_URL}/ml/retorno`
const mlConectado = () => !!ler('ml.json', null)?.refresh_token
async function mlToken() {
  const t = ler('ml.json', null)
  if (!t) return null
  if (t.expira > Date.now() + 5 * 60 * 1000) return t.access_token
  const r = await fetch('https://api.mercadolibre.com/oauth/token', {
    method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded', accept: 'application/json' },
    body: new URLSearchParams({ grant_type: 'refresh_token', client_id: process.env.ML_CLIENT_ID, client_secret: process.env.ML_CLIENT_SECRET, refresh_token: t.refresh_token }),
  })
  const j = await r.json()
  if (!r.ok) { log('ML: falha ao renovar token: ' + (j.message || r.status)); return null }
  salvar('ml.json', { ...t, access_token: j.access_token, refresh_token: j.refresh_token || t.refresh_token, expira: Date.now() + j.expires_in * 1000 })
  return j.access_token
}
async function mlTeste() {
  const tok = await mlToken()
  if (!tok) return { conectado: false }
  const st = async p => (await fetch('https://api.mercadolibre.com' + p, { headers: { Authorization: 'Bearer ' + tok } })).status
  return { conectado: true, usuario: ler('ml.json', {}).nickname, ofertas_do_produto: await st('/products/MLB17001072/items'), mais_vendidos: await st('/highlights/MLB/category/MLB1618') }
}

function python(script, args, env) {
  return new Promise((res, rej) => execFile('python3', [path.join(REPO, 'achadinhos', script), ...args], { cwd: REPO, env: { ...process.env, ...env }, timeout: 15 * 60 * 1000, maxBuffer: 1 << 24 }, (e, out, err) => {
    if (e) return rej(new Error((err || e.message).trim().split('\n').slice(-3).join(' | ')))
    res(out.trim())
  }))
}
let buscando = false
async function buscarProdutos(tema) {
  if (buscando) throw new Error('já tem uma busca rodando')
  buscando = true
  try {
    const tok = await mlToken()
    if (!tok) throw new Error('Mercado Livre não conectado')
    const { data } = agora()
    const env = { ML_ACCESS_TOKEN: tok, ACHADINHOS_DIR: DADOS }
    log(`busca de produtos: ${tema} + ${MISTURA[tema]}`)
    const arquivos = []
    for (const t of [tema, MISTURA[tema]]) arquivos.push((await python('escolher.py', [t, '20'], env)).split('\n').pop())
    const aprovados = arquivos.reduce((n, a) => n + (JSON.parse(fs.readFileSync(a, 'utf8')).produtos || []).length, 0)
    if (!aprovados) throw new Error('nenhum produto passou nos filtros (a API pode estar bloqueando preço/vendedor)')
    const atual = ler(`fila/${data}.json`, null)
    await python('fila.py', [data, ...arquivos], env)
    // mantém as ofertas manuais que já estavam na fila de hoje
    if (atual) {
      const nova = ler(`fila/${data}.json`, { data, ofertas: [] })
      nova.ofertas = [...nova.ofertas, ...atual.ofertas.filter(o => o.manual)].sort((a, b) => a.hora.localeCompare(b.hora))
      salvar(`fila/${data}.json`, nova)
    }
    salvar('busca.json', { data, quando: new Date().toISOString(), tema })
    log(`busca pronta: ${ler(`fila/${data}.json`, { ofertas: [] }).ofertas.length} ofertas na fila de hoje`)
  } finally { buscando = false }
}

// ---------- painel ----------
const sessoes = new Set()
const tentativas = new Map()
function logado(req) {
  if (!SENHA) return true
  const m = /(?:^|;\s*)s=([a-f0-9]{64})/.exec(req.headers.cookie || '')
  return !!m && sessoes.has(m[1])
}
function corpo(req) {
  return new Promise((res, rej) => {
    let d = ''
    req.on('data', c => { d += c; if (d.length > 2e6) { rej(new Error('grande demais')); req.destroy() } })
    req.on('end', () => { try { res(d ? JSON.parse(d) : {}) } catch { res({}) } })
  })
}
function json(res, cod, v) { res.writeHead(cod, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }); res.end(JSON.stringify(v)) }

async function estado() {
  const { data } = agora(), c = config(), fila = await filaDoDia(data), env = enviados()
  return {
    whatsapp: estadoWa, qr: qrAtual, numero: sock?.user?.id?.split(':')[0] || null,
    config: c, ml: { conectado: mlConectado(), usuario: ler('ml.json', {}).nickname || null, busca: ler('busca.json', null), buscando },
    grupos: c.grupos.map(id => ({ id, nome: gruposCache.get(id)?.subject || id, membros: gruposCache.get(id)?.participants?.length })),
    fila: { data, origem: fila.origem, ofertas: (fila.ofertas || []).map(o => ({ ...o, status: env[`${data}:${o.id}`] || null })) },
    eventos: eventos.slice(0, 40),
  }
}

const rotas = {
  'GET /api/estado': async () => estado(),
  'GET /api/grupos': async () => {
    if (!sock) throw new Error('WhatsApp não está conectado')
    const todos = await sock.groupFetchAllParticipating()
    for (const g of Object.values(todos)) gruposCache.set(g.id, g)
    const marcados = new Set(config().grupos)
    return Object.values(todos).map(g => ({ id: g.id, nome: g.subject, membros: g.participants.length, recebe: marcados.has(g.id), so_admins: !!g.announce }))
  },
  'POST /api/grupos/recebe': async b => {
    const set = new Set(config().grupos)
    b.recebe ? set.add(b.id) : set.delete(b.id)
    mudarConfig({ grupos: [...set] }); return { ok: true }
  },
  'POST /api/grupos/link': async b => ({ link: 'https://chat.whatsapp.com/' + await sock.groupInviteCode(b.id) }),
  'POST /api/grupos/so-admins': async b => { await sock.groupSettingUpdate(b.id, b.ligar ? 'announcement' : 'not_announcement'); return { ok: true } },
  'POST /api/grupos/nome': async b => { await sock.groupUpdateSubject(b.id, b.nome); return { ok: true } },
  'POST /api/grupos/descricao': async b => { await sock.groupUpdateDescription(b.id, b.descricao); return { ok: true } },
  'POST /api/config': async b => {
    const p = {}
    for (const k of ['pausado', 'busca_auto']) if (k in b) p[k] = !!b[k]
    if (/^\d\d:\d\d$/.test(b.hora_busca || '')) p.hora_busca = b.hora_busca
    mudarConfig(p); return { ok: true }
  },
  'POST /api/oferta': async b => {
    if (!b.link || !b.titulo) throw new Error('preencha pelo menos o link e o título')
    const { data, hora } = agora()
    const dia = /^\d{4}-\d\d-\d\d$/.test(b.data || '') ? b.data : data
    const f = await filaEditavel(dia)
    const o = { id: 'manual-' + crypto.randomBytes(4).toString('hex'), manual: true, hora: /^\d\d:\d\d$/.test(b.hora || '') ? b.hora : hora, imagem: b.imagem || null, texto: textoOferta(b) }
    f.ofertas.push(o); f.ofertas.sort((a, c) => a.hora.localeCompare(c.hora))
    salvar(`fila/${dia}.json`, f); log(`oferta adicionada para ${dia} ${o.hora}`)
    return o
  },
  'POST /api/oferta/previa': async b => ({ texto: textoOferta(b) }),
  'POST /api/oferta/editar': async b => {
    const dia = b.data || agora().data, f = await filaEditavel(dia), o = f.ofertas.find(x => x.id === b.id)
    if (!o) throw new Error('oferta não encontrada')
    if (typeof b.texto === 'string') o.texto = b.texto
    if (/^\d\d:\d\d$/.test(b.hora || '')) o.hora = b.hora
    f.ofertas.sort((a, c) => a.hora.localeCompare(c.hora)); salvar(`fila/${dia}.json`, f); return { ok: true }
  },
  'POST /api/oferta/remover': async b => {
    const dia = b.data || agora().data, f = await filaEditavel(dia)
    f.ofertas = f.ofertas.filter(x => x.id !== b.id); salvar(`fila/${dia}.json`, f); return { ok: true }
  },
  'POST /api/oferta/enviar': async b => {
    const dia = b.data || agora().data, o = (await filaDoDia(dia)).ofertas.find(x => x.id === b.id)
    if (!o) throw new Error('oferta não encontrada')
    await enviarOferta(o, dia); return { ok: true }
  },
  'POST /api/mensagem': async b => {
    if (!b.texto) throw new Error('mensagem vazia')
    let img = null
    if (b.imagem) { const r = await fetch(b.imagem); if (!r.ok) throw new Error('não consegui baixar a imagem'); img = Buffer.from(await r.arrayBuffer()) }
    await enviarParaGrupos(b.texto, img); log('mensagem avulsa enviada'); return { ok: true }
  },
  'POST /api/whatsapp/sair': async () => { try { await sock?.logout() } catch {} fs.rmSync(arq('auth'), { recursive: true, force: true }); return { ok: true } },
  'POST /api/ml/teste': async () => mlTeste(),
  'POST /api/ml/buscar': async b => { buscarProdutos(b.tema || TEMAS[agora().dia]).catch(e => log('busca falhou: ' + e.message)); return { ok: true } },
  'POST /api/atualizar': async () => {
    await new Promise((res, rej) => execFile('bash', ['-c', 'git pull --ff-only && cd nuvem && npm install --omit=dev --no-audit --no-fund'], { cwd: REPO, timeout: 5 * 60 * 1000 }, (e, out, err) => e ? rej(new Error((err || e.message).slice(-300))) : res(out)))
    setTimeout(() => process.exit(0), 1000); return { ok: true, msg: 'atualizado, reiniciando' }
  },
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, BASE_URL)
  try {
    if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/index.html')) {
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' })
      return res.end(fs.readFileSync(path.join(AQUI, 'painel.html')))
    }
    if (req.method === 'POST' && url.pathname === '/api/login') {
      const ip = req.headers['x-forwarded-for']?.split(',')[0] || req.socket.remoteAddress
      const t = tentativas.get(ip) || { n: 0, ate: 0 }
      if (t.ate > Date.now()) return json(res, 429, { erro: 'muitas tentativas, espere 10 minutos' })
      const b = await corpo(req)
      const ok = SENHA && b.senha && crypto.timingSafeEqual(crypto.createHash('sha256').update(String(b.senha)).digest(), crypto.createHash('sha256').update(SENHA).digest())
      if (!ok) { t.n++; if (t.n >= 5) { t.ate = Date.now() + 10 * 60 * 1000; t.n = 0 } tentativas.set(ip, t); return json(res, 401, { erro: 'senha errada' }) }
      const s = crypto.randomBytes(32).toString('hex'); sessoes.add(s)
      res.setHeader('set-cookie', `s=${s}; Path=/; HttpOnly;${BASE_URL.startsWith('https') ? ' Secure;' : ''} SameSite=Lax; Max-Age=${60 * 60 * 24 * 60}`)
      return json(res, 200, { ok: true })
    }
    if (!logado(req)) return json(res, 401, { erro: 'faça login' })
    if (req.method === 'GET' && url.pathname === '/ml/conectar') {
      const st = crypto.randomBytes(16).toString('hex'); salvar('ml-state.json', { st, ate: Date.now() + 15 * 60 * 1000 })
      res.writeHead(302, { location: `https://auth.mercadolivre.com.br/authorization?response_type=code&client_id=${encodeURIComponent(process.env.ML_CLIENT_ID || '')}&redirect_uri=${encodeURIComponent(ML_REDIRECT)}&state=${st}` })
      return res.end()
    }
    if (req.method === 'GET' && url.pathname === '/ml/retorno') {
      const esperado = ler('ml-state.json', {})
      if (!url.searchParams.get('code') || url.searchParams.get('state') !== esperado.st || esperado.ate < Date.now()) throw new Error('retorno do Mercado Livre inválido, tente conectar de novo')
      const r = await fetch('https://api.mercadolibre.com/oauth/token', {
        method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded', accept: 'application/json' },
        body: new URLSearchParams({ grant_type: 'authorization_code', client_id: process.env.ML_CLIENT_ID, client_secret: process.env.ML_CLIENT_SECRET, code: url.searchParams.get('code'), redirect_uri: ML_REDIRECT }),
      })
      const j = await r.json()
      if (!r.ok) throw new Error('Mercado Livre recusou: ' + (j.message || j.error || r.status))
      let nickname = null
      try { nickname = (await (await fetch('https://api.mercadolibre.com/users/me', { headers: { Authorization: 'Bearer ' + j.access_token } })).json()).nickname } catch {}
      salvar('ml.json', { access_token: j.access_token, refresh_token: j.refresh_token, expira: Date.now() + j.expires_in * 1000, user_id: j.user_id, nickname })
      fs.rmSync(arq('ml-state.json'), { force: true })
      log(`Mercado Livre conectado (${nickname || j.user_id})`)
      res.writeHead(302, { location: '/#ml' }); return res.end()
    }
    const rota = rotas[`${req.method} ${url.pathname}`]
    if (!rota) return json(res, 404, { erro: 'não encontrado' })
    return json(res, 200, await rota(req.method === 'POST' ? await corpo(req) : {}))
  } catch (e) {
    return json(res, 400, { erro: e.message })
  }
}).listen(PORT, '127.0.0.1', () => log(`painel em ${BASE_URL} (porta ${PORT})`))

conectarWa().catch(e => { log('erro ao conectar: ' + e.message); reconectar() })
setInterval(ciclo, 60 * 1000)
setTimeout(ciclo, 15 * 1000)
