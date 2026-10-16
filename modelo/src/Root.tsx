import React from 'react';
import {Composition} from 'remotion';
import {Reel, duracaoTotal, Roteiro} from './Reel';
import exemplo from '../roteiros/exemplo.json';

export const Root: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={exemplo as Roteiro}
    calculateMetadata={({props}) => ({durationInFrames: duracaoTotal(props)})}
  />
);
