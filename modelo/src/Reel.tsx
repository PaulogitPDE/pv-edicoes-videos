import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {loadFont} from '@remotion/fonts';

const fonte = 'Inter';
[700, 800].forEach((w) => loadFont({family: fonte, url: staticFile(`inter-latin-${w}-normal.woff2`), weight: String(w)}));
const fonteKanji = "'WenQuanYi Zen Hei', 'Noto Sans CJK JP', sans-serif";

export type Cena = {texto: string; destaque?: string[]; kanji?: string; impacto?: boolean; imagem?: string; foco?: string; tempos?: number[]; duracao?: number; narrar?: boolean; audio?: string};
export type Roteiro = {cenas: Cena[]; musica?: string; inicioMusica?: number; vozFinal?: string; narracao?: string; duracaoFinal?: number; cta?: string; voz?: string; assinatura?: string};

// Ritmo: 1 palavra a cada meio tempo (120 bpm = 15 frames por tempo).
const POR_PALAVRA = 8;
const SEGURA = 26;
const FINAL = 60;
const VERMELHO = '#E5192E';
const BRANCO = '#F4F1EA';

const duracaoCena = (c: Cena) => c.duracao ?? Math.round(c.texto.split(' ').length * POR_PALAVRA * (c.impacto ? 1.6 : 1)) + SEGURA + (c.impacto ? 22 : 0);
const duracaoFinal = (r: Roteiro) => r.duracaoFinal ?? (r.vozFinal ? 135 : FINAL);
export const duracaoTotal = (r: Roteiro) => r.cenas.reduce((a, c) => a + duracaoCena(c), 0) + duracaoFinal(r);

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

// Retícula de mangá + vinheta + granulação
const Fundo: React.FC<{seed: number}> = ({seed}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: '#050505'}}>
      <AbsoluteFill style={{backgroundImage: 'radial-gradient(rgba(255,255,255,0.13) 2.2px, transparent 2.6px)', backgroundSize: '18px 18px', transform: `rotate(${15 + seed * 7}deg) scale(1.6)`, opacity: 0.55, WebkitMaskImage: 'radial-gradient(ellipse 70% 55% at 50% 50%, transparent 30%, black 95%)'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 80% 60% at 50% 50%, transparent 40%, rgba(0,0,0,0.92) 100%)'}} />
      <AbsoluteFill style={{opacity: 0.12, mixBlendMode: 'screen'}}>
        <svg width="1080" height="1920"><filter id="g"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={f % 12} /></filter><rect width="100%" height="100%" filter="url(#g)" /></svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Linhas de velocidade (estilo painel de mangá)
const Linhas: React.FC<{seed: number; forca: number}> = ({seed, forca}) => {
  const f = useCurrentFrame();
  const linhas = Array.from({length: 120}, (_, i) => {
    const ang = random(`a${seed}-${i}`) * Math.PI * 2;
    const larg = 0.004 + random(`w${seed}-${i}`) * 0.012;
    const r0 = 520 + random(`r${seed}-${i}-${Math.floor(f / 2)}`) * 260;
    const R = 2000;
    const cx = 540, cy = 960;
    const p = (a: number, r: number) => `${cx + Math.cos(a) * r},${cy + Math.sin(a) * r}`;
    return <polygon key={i} points={`${p(ang - larg, R)} ${p(ang + larg, R)} ${p(ang, r0)}`} fill={BRANCO} />;
  });
  return <AbsoluteFill style={{opacity: 0.16 + forca * 0.5}}><svg width="1080" height="1920">{linhas}</svg></AbsoluteFill>;
};


// Frame de mangá "animado": zoom lento, tremida nas palavras, alto contraste
const FrameManga: React.FC<{src: string; foco?: string; dur: number; palavras: number}> = ({src, foco, dur, palavras}) => {
  const f = useCurrentFrame();
  const zoom = interpolate(f, [0, dur], [1.22, 1.06], clamp);
  const pulso = f % POR_PALAVRA < 3 && f < palavras * POR_PALAVRA ? 1 : 0;
  const tx = pulso ? (random(`x${f}`) - 0.5) * 22 : 0;
  const ty = pulso ? (random(`y${f}`) - 0.5) * 22 : 0;
  return (
    <AbsoluteFill>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: foco || 'center', transform: `translate(${tx}px, ${ty}px) scale(${zoom + pulso * 0.02})`, filter: 'grayscale(1) contrast(1.6) brightness(0.55)'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 85% 35% at 50% 50%, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 70%, rgba(0,0,0,0.65) 100%)'}} />
    </AbsoluteFill>
  );
};

const Palavra: React.FC<{t: string; i: number; vermelha: boolean; ini?: number}> = ({t, i, vermelha, ini: iniDado}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ini = iniDado ?? i * POR_PALAVRA;
  const s = spring({frame: f - ini, fps, config: {damping: 11, mass: 0.6, stiffness: 180}});
  const tremor = f - ini < 6 && f >= ini ? (random(`t${i}-${f}`) - 0.5) * 18 : 0;
  return (
    <span style={{display: 'inline-block', margin: '0 0.18em', opacity: f >= ini ? 1 : 0, transform: `translate(${tremor}px, ${tremor * 0.6}px) scale(${0.4 + s * 0.6})`, color: vermelha ? VERMELHO : BRANCO, textShadow: vermelha ? `0 0 38px ${VERMELHO}aa, 4px 4px 0 #000` : '4px 4px 0 #000, 0 0 24px rgba(0,0,0,0.9)'}}>
      {t}
    </span>
  );
};

// Frase de impacto em motion: palavra "bate" na tela com desfoque, separação RGB e tremida
const PalavraImpacto: React.FC<{t: string; i: number; vermelha: boolean; ini: number}> = ({t, i, vermelha, ini}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const d = f - ini;
  const s = spring({frame: d, fps, config: {damping: 9, mass: 0.5, stiffness: 220}});
  const escala = interpolate(s, [0, 1], [2.8, 1]);
  const blur = interpolate(d, [0, 6], [14, 0], clamp);
  const rgb = interpolate(d, [0, 10], [18, 0], clamp) + (d >= 0 ? Math.sin(f / 3) * 1.5 : 0);
  const tremor = d >= 0 && d < 8 ? (random(`ti${i}-${f}`) - 0.5) * 26 : 0;
  const cor = vermelha ? VERMELHO : BRANCO;
  const base: React.CSSProperties = {position: 'absolute', left: 0, top: 0};
  return (
    <span style={{position: 'relative', display: 'inline-block', margin: '0 0.16em', opacity: d >= 0 ? 1 : 0, transform: `translate(${tremor}px, ${tremor * 0.5}px) scale(${escala}) rotate(${interpolate(d, [0, 8], [i % 2 ? 6 : -6, 0], clamp)}deg)`, filter: `blur(${blur}px)`}}>
      <span style={{...base, color: '#ff2b3a', transform: `translate(${-rgb}px, 0)`, mixBlendMode: 'screen', opacity: 0.8}}>{t}</span>
      <span style={{...base, color: '#22e5ff', transform: `translate(${rgb}px, 0)`, mixBlendMode: 'screen', opacity: 0.6}}>{t}</span>
      <span style={{position: 'relative', color: cor, textShadow: vermelha ? `0 0 50px ${VERMELHO}, 5px 5px 0 #000` : `5px 5px 0 #000, 0 0 30px rgba(0,0,0,0.9)`}}>{t}</span>
    </span>
  );
};

const CenaView: React.FC<{c: Cena; n: number; dur: number}> = ({c, n, dur}) => {
  const f = useCurrentFrame();
  const palavras = c.texto.split(' ');
  const flash = interpolate(f, [0, 4], [0.85, 0], clamp);
  const zoom = interpolate(f, [0, dur], [1.08, 1.0], {...clamp, easing: Easing.out(Easing.quad)});
  const forca = interpolate(f, [0, 10], [1, 0], clamp) + (c.impacto ? interpolate(f, [palavras.length * POR_PALAVRA, palavras.length * POR_PALAVRA + 12], [1, 0.3], clamp) : 0);
  const sai = interpolate(f, [dur - 5, dur], [1, 0], clamp);
  const tamanho = palavras.length <= 2 ? 150 : palavras.length <= 4 ? 118 : 100;
  const ultima = c.tempos?.[palavras.length - 1] ?? (palavras.length - 1) * POR_PALAVRA * (c.impacto ? 1.6 : 1);
  const sacode = c.impacto && f >= ultima && f < ultima + 10 ? (random(`s${n}-${f}`) - 0.5) * 30 : 0;
  return (
    <AbsoluteFill style={{transform: `translate(${sacode}px, ${sacode * 0.6}px) scale(${zoom})`, opacity: sai}}>
      <Fundo seed={n} />
      {c.imagem && <FrameManga src={c.imagem} foco={c.foco} dur={dur} palavras={palavras.length} />}
      <Linhas seed={n} forca={Math.min(forca, 1) * (c.imagem ? 0.6 : 1)} />
      {c.kanji && !c.imagem && (
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
          <div style={{fontFamily: fonteKanji, fontSize: 780, color: VERMELHO, opacity: 0.16, transform: `translateY(${interpolate(f, [0, dur], [40, -40])}px)`}}>{c.kanji}</div>
        </AbsoluteFill>
      )}
      {/* moldura de painel */}
      <div style={{position: 'absolute', inset: 36, border: `5px solid ${BRANCO}`, outline: '14px solid #000', borderRadius: 6, opacity: 0.85}} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column', padding: '0 90px'}}>
        <div style={{fontFamily: fonte, fontWeight: 800, fontSize: tamanho, lineHeight: 1.08, letterSpacing: -2, textAlign: 'center', textTransform: 'uppercase'}}>
          {palavras.map((p, i) => c.impacto
            ? <PalavraImpacto key={i} t={p} i={i} ini={c.tempos?.[i] ?? i * POR_PALAVRA * 1.6} vermelha={(c.destaque || []).includes(p)} />
            : <Palavra key={i} t={p} i={i} ini={c.tempos?.[i]} vermelha={(c.destaque || []).includes(p)} />)}
        </div>
        {c.impacto && <div style={{height: 14, marginTop: 30, background: VERMELHO, boxShadow: `0 0 30px ${VERMELHO}`, width: `${interpolate(f, [ultima + 4, ultima + 14], [0, 70], {...clamp, easing: Easing.out(Easing.cubic)})}%`, transform: 'skewX(-20deg)'}} />}
      </AbsoluteFill>
      {c.audio && <Audio src={staticFile(c.audio)} volume={1} />}
      {c.impacto && <AbsoluteFill style={{background: VERMELHO, mixBlendMode: 'multiply', opacity: interpolate(f, [ultima, ultima + 3, ultima + 12], [0, 0.55, 0], clamp)}} />}
      <AbsoluteFill style={{background: '#fff', opacity: flash}} />
    </AbsoluteFill>
  );
};

const Final: React.FC<{assinatura: string}> = ({assinatura}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f, fps, config: {damping: 14}});
  return (
    <AbsoluteFill style={{background: '#050505', alignItems: 'center', justifyContent: 'center'}}>
      <Linhas seed={99} forca={0.2} />
      <div style={{fontFamily: fonte, fontWeight: 800, fontSize: 96, color: BRANCO, letterSpacing: -2, transform: `scale(${0.6 + s * 0.4})`, opacity: s, textShadow: `0 0 40px ${VERMELHO}88`}}>{assinatura}</div>
      <div style={{fontFamily: fonte, fontWeight: 700, fontSize: 44, color: VERMELHO, marginTop: 24, opacity: interpolate(f, [10, 20], [0, 1], clamp)}}>SALVA E MANDA PRA QUEM PRECISA</div>
    </AbsoluteFill>
  );
};

export const Reel: React.FC<Roteiro> = (r) => {
  let ini = 0;
  const total = duracaoTotal(r);
  // música abaixa nas cenas narradas (rampa de 6 frames)
  const janelas: [number, number][] = [];
  r.cenas.reduce((a, c) => { const d = duracaoCena(c); if (c.audio) janelas.push([a, a + d]); return a + d; }, 0);
  const abaixa = (f: number) => r.narracao ? 0.3 : Math.min(1, ...janelas.map(([a, b]) => interpolate(f, [a - 6, a, b - 4, b + 2], [1, 0.32, 0.32, 1], clamp)));
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {r.narracao && <Audio src={staticFile(r.narracao)} volume={1} />}
      {r.musica && <Audio src={staticFile(r.musica)} startFrom={Math.round((r.inicioMusica || 0) * 30)} volume={(f) => abaixa(f) * interpolate(f, [0, 8, total - duracaoFinal(r), total - duracaoFinal(r) + 10, total - 15, total], [0, 1, 1, r.vozFinal ? 0.35 : 1, r.vozFinal ? 0.35 : 1, 0], clamp)} />}
      {r.cenas.map((c, n) => {
        const d = duracaoCena(c);
        const el = (
          <Sequence key={n} from={ini} durationInFrames={d}>
            <CenaView c={c} n={n} dur={d} />
          </Sequence>
        );
        ini += d;
        return el;
      })}
      <Sequence from={ini} durationInFrames={duracaoFinal(r)}>
        <Final assinatura={r.assinatura || '@pvedicoes'} />
        {r.vozFinal && <Audio src={staticFile(r.vozFinal)} volume={1} />}
      </Sequence>
    </AbsoluteFill>
  );
};
