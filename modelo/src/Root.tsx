import React from 'react';
import {Composition, Still} from 'remotion';
import {Post, PostProps} from './Post';
import {Reel, duracaoTotal, Roteiro} from './Reel';
import exemplo from '../roteiros/exemplo.json';

export const Root: React.FC = () => (
  <>
  <Composition
    id="Reel"
    component={Reel}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={exemplo as Roteiro}
    calculateMetadata={({props}) => ({durationInFrames: duracaoTotal(props)})}
  />
  <Still id="Post" component={Post} width={1080} height={1350} defaultProps={{imagem: 'banco/1sEVBmbLPIp1XcCVmBzrzWT1-hxtzZUqG.jpg', headline: 'Teste de headline', destaque: ['headline']} as PostProps} />
  </>
);
