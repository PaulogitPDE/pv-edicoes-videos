// Envia as ofertas do dia no grupo de WhatsApp e executa as ordens da nuvem.
// A nuvem publica achadinhos/fila/AAAA-MM-DD.json e achadinhos/comandos.json no repo; este script roda no PC,
// confere os dois a cada minuto, manda cada oferta no horario dela e executa cada comando novo uma vez
// (trocar nome, descricao ou foto do grupo, pegar o link de convite, mandar mensagem avulsa).
// O resultado dos comandos vai para whatsapp/status.json, que este script commita e da push se a pasta
// estiver dentro de um clone do repo; assim a nuvem le o resultado (ex.: o link do grupo).
//   node enviador.js          -> roda o dia todo
//   node enviador.js grupos   -> lista os grupos e seus IDs (para o config.json)
//   node enviador.js teste    -> manda 1 mensagem de teste no grupo do config
const fs = require('fs')
const path = require('path')
// Baileys 7 (só ESM): carregado com import() dentro de conectar(). A versão 6 deixava as mensagens do grupo
// como "Aguardando mensagem" para os participantes (criptografia de grupo com LID, 02/11).
let B = null

const DIR = __dirname
const CONFIG = path.join(DIR, 'config.json')
const ENVIADOS = path.join(DIR, 'enviados.json')
const FEITOS = path.join(DIR, 'comandos-feitos.json')
const STATUS = path.join(DIR, 'status.json')
const { execFileSync, execSync } = require('child_process')
const modo = process.argv[2] || 'rodar'

// Depois de um "atualizar", instala sozinho as dependências novas do package.json (ex.: Baileys 7)
function versaoInstalada(pacote) {
  try { return JSON.parse(fs.readFileSync(path.join(DIR, 'node_modules', pacote, 'package.json'), 'utf8')).version } catch { return null }
}
function garantirDependencias() {
  const deps = JSON.parse(fs.readFileSync(path.join(DIR, 'package.json'), 'utf8')).dependencies
  // falta o pacote, ou a versão é fixa (sem ^ ou ~) e a instalada é outra
  const faltando = Object.entries(deps).filter(([nome, v]) => {
    const inst = versaoInstalada(nome)
    return !inst || (!/^[\^~]/.test(v) && inst !== v)
  })
  if (!faltando.length) return
  console.log(`Instalando dependencias novas: ${faltando.map(([n, v]) => n + '@' + v).join(', ')}`)
  execSync('npm install --no-audit --no-fund', { cwd: DIR, stdio: 'inherit' })
}
if (Number(process.versions.node.split('.')[0]) < 20) {
  console.log(`Node ${process.versions.node} e antigo: instale o Node 20 ou mais novo (nodejs.org, versao LTS).`)
}
garantirDependencias()
const pino = require('pino')
const qrcode = require('qrcode-terminal')

function ler(arq, padrao) {
  try { return JSON.parse(fs.readFileSync(arq, 'utf8')) } catch { return padrao }
}

const config = ler(CONFIG, null)
if (!config && modo !== 'grupos') {
  console.log('Falta o config.json. Copie config.exemplo.json para config.json e preencha o grupo_id.')
  console.log('Para descobrir o ID do grupo: node enviador.js grupos')
  process.exit(1)
}

// Data e hora de Brasilia, independente do relogio do Windows
function agoraBR() {
  const p = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false,
  }).formatToParts(new Date())
  const v = Object.fromEntries(p.map(x => [x.type, x.value]))
  return { data: `${v.year}-${v.month}-${v.day}`, hora: `${v.hour === '24' ? '00' : v.hour}:${v.minute}` }
}

async function baixarFila(data) {
  const url = config.fila_url.replace('{data}', data) + `?t=${Date.now()}`
  const r = await fetch(url)
  if (r.status === 404) return null
  if (!r.ok) throw new Error(`fila ${r.status}`)
  return r.json()
}

async function baixarComandos() {
  const base = config.comandos_url ||
    'https://raw.githubusercontent.com/PaulogitPDE/pv-edicoes-videos/main/achadinhos/comandos.json'
  const r = await fetch(base + `?t=${Date.now()}`)
  if (r.status === 404) return []
  if (!r.ok) throw new Error(`comandos ${r.status}`)
  return (await r.json()).comandos || []
}

// Grava o resultado e tenta mandar para o repo (so funciona se a pasta for um clone com git logado)
function publicarStatus(status) {
  fs.writeFileSync(STATUS, JSON.stringify(status, null, 1))
  try {
    const git = args => execFileSync('git', args, { cwd: DIR, stdio: 'pipe' })
    git(['add', 'status.json'])
    git(['commit', '-m', 'WhatsApp: resultado dos comandos'])
    git(['pull', '--rebase', '--autostash'])
    git(['push'])
  } catch (e) {
    console.log(`  status salvo so no PC (git: ${String(e.stderr || e.message).split('\n')[0]})`)
  }
}

async function executarComando(sock, c) {
  const g = config.grupo_id
  switch (c.tipo) {
    case 'nome': await sock.groupUpdateSubject(g, c.valor); return 'ok'
    case 'descricao': await sock.groupUpdateDescription(g, c.valor); return 'ok'
    case 'foto': await sock.updateProfilePicture(g, await baixarImagem(c.url)); return 'ok'
    case 'so_admins': await sock.groupSettingUpdate(g, 'announcement'); return 'ok'
    case 'todos': await sock.groupSettingUpdate(g, 'not_announcement'); return 'ok'
    case 'link': return 'https://chat.whatsapp.com/' + await sock.groupInviteCode(g)
    case 'mensagem':
      if (c.imagem) await enviar(sock, g, { image: await baixarImagem(c.imagem), caption: c.texto })
      else await enviar(sock, g, { text: c.texto })
      return 'ok'
    case 'trava_dados': await sock.groupSettingUpdate(g, 'locked'); return 'ok'
    case 'atualizar': setTimeout(() => process.exit(0), 3000); return 'reiniciando com a versao nova'
    case 'info': {
      const m = await sock.groupMetadata(g)
      return { nome: m.subject, descricao: m.desc || '', participantes: m.participants.length,
        so_admins_falam: !!m.announce, so_admins_editam: !!m.restrict,
        node: process.versions.node, baileys: versaoInstalada('@whiskeysockets/baileys') }
    }
    default: throw new Error(`tipo desconhecido: ${c.tipo}`)
  }
}

async function rodarComandos(sock) {
  const feitos = ler(FEITOS, {})
  const novos = (await baixarComandos()).filter(c => c.id && !feitos[c.id])
  if (!novos.length) return
  const status = ler(STATUS, { resultados: {} })
  for (const c of novos) {
    let resultado
    try { resultado = await executarComando(sock, c) } catch (e) { resultado = `erro: ${e.message}` }
    feitos[c.id] = new Date().toISOString()
    status.resultados[c.id] = { tipo: c.tipo, resultado, quando: feitos[c.id] }
    console.log(`comando ${c.id} (${c.tipo}): ${JSON.stringify(resultado)}`)
  }
  fs.writeFileSync(FEITOS, JSON.stringify(feitos, null, 1))
  status.atualizado = new Date().toISOString()
  publicarStatus(status)
}

async function baixarImagem(url) {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`imagem ${r.status}`)
  return Buffer.from(await r.arrayBuffer())
}

const espera = ms => new Promise(res => setTimeout(res, ms))

async function enviar(sock, jid, conteudo) {
  const m = await sock.sendMessage(jid, conteudo)
  if (m?.key?.id && m.message) {
    enviadasCache.set(m.key.id, m.message)
    if (enviadasCache.size > 500) enviadasCache.delete(enviadasCache.keys().next().value)
  }
  return m
}

// Mensagens enviadas ficam guardadas para reenviar quando o celular de alguém pede de novo (retry de criptografia)
const enviadasCache = new Map()
const gruposCache = new Map()

async function conectar() {
  B = B || await import('@whiskeysockets/baileys')
  const makeWASocket = B.makeWASocket || B.default
  const logger = pino({ level: 'silent' })
  const { state, saveCreds } = await B.useMultiFileAuthState(path.join(DIR, 'auth'))
  const { version } = await B.fetchLatestBaileysVersion()
  const sock = makeWASocket({
    version,
    logger,
    auth: { creds: state.creds, keys: B.makeCacheableSignalKeyStore(state.keys, logger) },
    getMessage: async key => enviadasCache.get(key.id),
    cachedGroupMetadata: async jid => gruposCache.get(jid),
  })
  sock.ev.on('creds.update', saveCreds)
  sock.ev.on('groups.update', async ([ev]) => {
    try { gruposCache.set(ev.id, await sock.groupMetadata(ev.id)) } catch {}
  })
  sock.ev.on('group-participants.update', async ev => {
    try { gruposCache.set(ev.id, await sock.groupMetadata(ev.id)) } catch {}
  })
  return new Promise((resolve, reject) => {
    sock.ev.on('connection.update', u => {
      if (u.qr) {
        console.log('\nEscaneie com o WhatsApp do chip do grupo (Aparelhos conectados > Conectar aparelho):\n')
        qrcode.generate(u.qr, { small: true })
      }
      if (u.connection === 'open') { console.log('WhatsApp conectado.'); resolve(sock) }
      if (u.connection === 'close') {
        const codigo = u.lastDisconnect?.error?.output?.statusCode
        if (codigo === B.DisconnectReason.loggedOut) {
          console.log('Sessao desconectada pelo celular. Apague a pasta auth e rode de novo para gerar outro QR.')
          process.exit(1)
        }
        reject(new Error(`conexao fechou (${codigo})`))
      }
    })
  })
}

async function listarGrupos(sock) {
  const grupos = await sock.groupFetchAllParticipating()
  console.log('\nGrupos deste numero:')
  for (const g of Object.values(grupos)) console.log(`  ${g.id}   ${g.subject}`)
  console.log('\nCopie o ID do grupo de promocoes para o grupo_id do config.json.')
}

async function enviarOferta(sock, oferta) {
  if (oferta.imagem) {
    try {
      const img = await baixarImagem(oferta.imagem)
      await enviar(sock, config.grupo_id, { image: img, caption: oferta.texto })
      return
    } catch (e) {
      console.log(`  sem imagem (${e.message}), mandando so o texto`)
    }
  }
  await enviar(sock, config.grupo_id, { text: oferta.texto })
}

async function rodar(sock) {
  const enviados = ler(ENVIADOS, {})
  let ultimoEnvio = 0
  try { gruposCache.set(config.grupo_id, await sock.groupMetadata(config.grupo_id)) } catch {}
  console.log('Rodando. Deixe esta janela aberta; as ofertas saem nos horarios da fila.')
  for (;;) {
    try {
      await rodarComandos(sock)
      const { data, hora } = agoraBR()
      const fila = await baixarFila(data)
      for (const oferta of fila?.ofertas || []) {
        const chave = `${data}:${oferta.id}`
        if (enviados[chave] || oferta.hora > hora) continue
        const desde = Date.now() - ultimoEnvio
        const minimo = (config.intervalo_min_segundos || 90) * 1000
        if (desde < minimo) await espera(minimo - desde)
        await enviarOferta(sock, oferta)
        ultimoEnvio = Date.now()
        enviados[chave] = new Date().toISOString()
        fs.writeFileSync(ENVIADOS, JSON.stringify(enviados, null, 1))
        console.log(`${data} ${agoraBR().hora} enviada: ${oferta.id}`)
      }
    } catch (e) {
      console.log(`erro: ${e.message} (tento de novo em 1 minuto)`)
      if (/conexao|Connection Closed/i.test(e.message)) throw e
    }
    await espera(60 * 1000)
  }
}

async function main() {
  for (;;) {
    try {
      const sock = await conectar()
      if (modo === 'grupos') { await listarGrupos(sock); process.exit(0) }
      if (modo === 'teste') {
        await enviar(sock, config.grupo_id, { text: 'Teste do PV Achadinhos: se chegou, o envio automatico funciona.' })
        console.log('Mensagem de teste enviada.')
        process.exit(0)
      }
      await rodar(sock)
    } catch (e) {
      console.log(`${e.message}. Reconectando em 10 segundos...`)
      await espera(10 * 1000)
    }
  }
}

main()
