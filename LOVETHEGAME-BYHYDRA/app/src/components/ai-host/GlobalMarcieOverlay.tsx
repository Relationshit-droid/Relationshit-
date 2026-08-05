import React from 'react';
import { ViewStyle } from 'react-native';
import DrMarcieOverlay, {
  MarcieAnimation,
  MarciePosition,
} from '../DrMarcieOverlay';

export type MarcieAnimationType = MarcieAnimation;

interface GlobalMarcieOverlayProps {
  animation?: MarcieAnimation;
  position?: MarciePosition;
  visible?: boolean;
  quote?: string;
  showBubble?: boolean;
  bubbleDuration?: number;
  onAnimationComplete?: () => void;
  size?: 'small' | 'medium' | 'large';
  style?: ViewStyle;
  zIndex?: number;
  gameState?: string;
}

export default function GlobalMarcieOverlay({
  gameState,
  ...overlayProps
}: GlobalMarcieOverlayProps) {
  return <DrMarcieOverlay {...overlayProps} />;
}
