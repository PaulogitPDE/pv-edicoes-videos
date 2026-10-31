// Envia as ofertas do dia no grupo de WhatsApp.
// A nuvem publica achadinhos/fila/AAAA-MM-DD.json no repo; este script roda no PC,
// confere a fila a cada minuto e manda cada oferta quando chega o horario dela.
//   node enviador.js          -> roda o dia todo
//   node enviador.js grupos   -> lista os grupos e seus IDs (para o config.json)
//   node enviador.js teste    -> manda 1 mensagem de teste no grupo do config
const fs = require('fs')
const path = require('path')
const pino = require('pino')
const qrcode = require('qrcode-terminal')
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} = require('@whiskeysockets/baileys')

const DIR = __dirname
const CONFIG = path.join(DIR, 'config.json')
const ENVIADOS = path.join(DIR, 'enviados.json')
const modo = process.argv[2] || 'rodar'

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

async function baixarImagem(url) {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`imagem ${r.status}`)
  return Buffer.from(await r.arrayBuffer())
}

const espera = ms => new Promise(res => setTimeout(res, ms))

async function conectar() {
  const { state, saveCreds } = await useMultiFileAuthState(path.join(DIR, 'auth'))
  const { version } = await fetchLatestBaileysVersion()
  const sock = makeWASocket({ version, auth: state, logger: pino({ level: 'silent' }) })
  sock.ev.on('creds.update', saveCreds)
  return new Promise((resolve, reject) => {
    sock.ev.on('connection.update', u => {
      if (u.qr) {
        console.log('\nEscaneie com o WhatsApp do chip do grupo (Aparelhos conectados > Conectar aparelho):\n')
        qrcode.generate(u.qr, { small: true })
      }
      if (u.connection === 'open') { console.log('WhatsApp conectado.'); resolve(sock) }
      if (u.connection === 'close') {
        const codigo = u.lastDisconnect?.error?.output?.statusCode
        if (codigo === DisconnectReason.loggedOut) {
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
      await sock.sendMessage(config.grupo_id, { image: img, caption: oferta.texto })
      return
    } catch (e) {
      console.log(`  sem imagem (${e.message}), mandando so o texto`)
    }
  }
  await sock.sendMessage(config.grupo_id, { text: oferta.texto })
}

async function rodar(sock) {
  const enviados = ler(ENVIADOS, {})
  let ultimoEnvio = 0
  console.log('Rodando. Deixe esta janela aberta; as ofertas saem nos horarios da fila.')
  for (;;) {
    try {
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
        await sock.sendMessage(config.grupo_id, { text: 'Teste do PV Achadinhos: se chegou, o envio automatico funciona.' })
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
