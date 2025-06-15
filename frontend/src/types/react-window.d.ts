declare module 'react-window' {
  import * as React from 'react';

  export interface FixedSizeListProps {
    children: React.ComponentType<any>;
    height: number;
    itemCount: number;
    itemSize: number;
    width?: number | string;
    style?: React.CSSProperties;
  }

  export const FixedSizeList: React.ComponentType<FixedSizeListProps>;
}