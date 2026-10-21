import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';

// Post de imagem (feed 4:5): headline editada direto na foto + linha aesthetic em serifa.
export type PostProps = {imagem: string; headline: string; destaque?: string[]; sub?: string; posicao?: 'topo' | 'baixo'; foco?: string; pb?: boolean};

const VERMELHO = '#E5192E';
const CREME = '#F4F1EA';

export const Post: React.FC<PostProps> = ({imagem, headline, destaque = [], sub, posicao = 'baixo', foco, pb}) => {
  const topo = posicao === 'topo';
  const palavras = headline.split(' ');
  const tam = headline.length <= 22 ? 112 : headline.length <= 40 ? 92 : 76;
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Img src={staticFile(imagem)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: foco || 'center', filter: pb ? 'grayscale(1) contrast(1.25) brightness(0.9)' : 'contrast(1.08) saturate(0.9)'}} />
      <AbsoluteFill style={{background: topo
        ? 'linear-gradient(180deg, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.6) 38%, rgba(0,0,0,0) 62%)'
        : 'linear-gradient(0deg, rgba(0,0,0,0.94) 0%, rgba(0,0,0,0.62) 40%, rgba(0,0,0,0) 66%)'}} />
      <AbsoluteFill style={{boxShadow: 'inset 0 0 220px rgba(0,0,0,0.75)'}} />
      {/* grão */}
      <AbsoluteFill style={{opacity: 0.1, mixBlendMode: 'screen'}}>
        <svg width="1080" height="1350"><filter id="g"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={7} /></filter><rect width="100%" height="100%" filter="url(#g)" /></svg>
      </AbsoluteFill>
      <div style={{position: 'absolute', inset: 28, border: `2px solid rgba(244,241,234,0.35)`}} />
      <div style={{position: 'absolute', left: 84, right: 84, [topo ? 'top' : 'bottom']: 110, display: 'flex', flexDirection: 'column', gap: 30}}>
        <div style={{width: 90, height: 8, background: VERMELHO}} />
        <div style={{fontFamily: "'Inter Display', 'Inter', sans-serif", fontWeight: 900, fontSize: tam, lineHeight: 1.02, letterSpacing: -2, wordSpacing: 10, textTransform: 'uppercase', color: CREME, textShadow: '0 6px 30px rgba(0,0,0,0.6)'}}>
          {palavras.map((p, i) => destaque.includes(p)
            ? <span key={i} style={{background: VERMELHO, color: CREME, padding: '0 14px', margin: '0 6px 0 0', display: 'inline-block', lineHeight: 1.1, transform: 'rotate(-1.5deg)'}}>{p}</span>
            : <span key={i}>{p} </span>)}
        </div>
        {sub && <div style={{fontFamily: "'Bitstream Charter', 'DejaVu Serif', serif", fontStyle: 'italic', fontSize: 44, lineHeight: 1.3, color: 'rgba(244,241,234,0.88)'}}>{sub}</div>}
      </div>
      <div style={{position: 'absolute', [topo ? 'bottom' : 'top']: 64, right: 72, fontFamily: "'Inter', sans-serif", fontWeight: 700, fontSize: 30, letterSpacing: 4, color: 'rgba(244,241,234,0.8)'}}>@PVEDICOES</div>
    </AbsoluteFill>
  );
};
