/**
 * ClipGenius - Text Animations (CapCut Style)
 * CSS keyframe animations for subtitle text
 */

import { AnimationIn, AnimationOut, AnimationLoop } from './editorApi';

export interface AnimationConfig {
  name: string;
  keyframes: string;
  duration: number;
  easing: string;
  fillMode?: string;
}

// ============ Entry Animations (In) ============

export const ANIMATIONS_IN: Record<Exclude<AnimationIn, 'none'>, AnimationConfig> = {
  bounce: {
    name: 'bounceIn',
    keyframes: `
      @keyframes bounceIn {
        0% {
          opacity: 0;
          transform: scale(0.3) translateY(100px);
        }
        50% {
          opacity: 1;
          transform: scale(1.05) translateY(-10px);
        }
        70% {
          transform: scale(0.95) translateY(5px);
        }
        100% {
          transform: scale(1) translateY(0);
        }
      }
    `,
    duration: 600,
    easing: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },
  zoomIn: {
    name: 'zoomIn',
    keyframes: `
      @keyframes zoomIn {
        0% {
          opacity: 0;
          transform: scale(0);
        }
        100% {
          opacity: 1;
          transform: scale(1);
        }
      }
    `,
    duration: 400,
    easing: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  },
  slideLeft: {
    name: 'slideLeft',
    keyframes: `
      @keyframes slideLeft {
        0% {
          opacity: 0;
          transform: translateX(-100%);
        }
        100% {
          opacity: 1;
          transform: translateX(0);
        }
      }
    `,
    duration: 300,
    easing: 'ease-out',
  },
  slideUp: {
    name: 'slideUp',
    keyframes: `
      @keyframes slideUp {
        0% {
          opacity: 0;
          transform: translateY(50px);
        }
        100% {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `,
    duration: 300,
    easing: 'ease-out',
  },
  fadeIn: {
    name: 'fadeIn',
    keyframes: `
      @keyframes fadeIn {
        0% {
          opacity: 0;
        }
        100% {
          opacity: 1;
        }
      }
    `,
    duration: 300,
    easing: 'ease-in-out',
  },
  typewriter: {
    name: 'typewriter',
    keyframes: `
      @keyframes typewriter {
        0% {
          clip-path: inset(0 100% 0 0);
        }
        100% {
          clip-path: inset(0 0 0 0);
        }
      }
    `,
    duration: 1000,
    easing: 'steps(40, end)',
  },
};

// ============ Exit Animations (Out) ============

export const ANIMATIONS_OUT: Record<Exclude<AnimationOut, 'none'>, AnimationConfig> = {
  bounce: {
    name: 'bounceOut',
    keyframes: `
      @keyframes bounceOut {
        0% {
          transform: scale(1);
        }
        25% {
          transform: scale(1.1);
        }
        100% {
          opacity: 0;
          transform: scale(0.3) translateY(100px);
        }
      }
    `,
    duration: 500,
    easing: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },
  zoomOut: {
    name: 'zoomOut',
    keyframes: `
      @keyframes zoomOut {
        0% {
          opacity: 1;
          transform: scale(1);
        }
        100% {
          opacity: 0;
          transform: scale(0);
        }
      }
    `,
    duration: 400,
    easing: 'cubic-bezier(0.55, 0.085, 0.68, 0.53)',
  },
  slideRight: {
    name: 'slideRight',
    keyframes: `
      @keyframes slideRight {
        0% {
          opacity: 1;
          transform: translateX(0);
        }
        100% {
          opacity: 0;
          transform: translateX(100%);
        }
      }
    `,
    duration: 300,
    easing: 'ease-in',
  },
  fadeOut: {
    name: 'fadeOut',
    keyframes: `
      @keyframes fadeOut {
        0% {
          opacity: 1;
        }
        100% {
          opacity: 0;
        }
      }
    `,
    duration: 300,
    easing: 'ease-in-out',
  },
};

// ============ Loop Animations ============

export const ANIMATIONS_LOOP: Record<Exclude<AnimationLoop, 'none'>, AnimationConfig> = {
  pulse: {
    name: 'pulse',
    keyframes: `
      @keyframes pulse {
        0%, 100% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.05);
        }
      }
    `,
    duration: 1000,
    easing: 'ease-in-out',
  },
  shake: {
    name: 'shake',
    keyframes: `
      @keyframes shake {
        0%, 100% {
          transform: translateX(0);
        }
        10%, 30%, 50%, 70%, 90% {
          transform: translateX(-2px);
        }
        20%, 40%, 60%, 80% {
          transform: translateX(2px);
        }
      }
    `,
    duration: 800,
    easing: 'ease-in-out',
  },
  float: {
    name: 'float',
    keyframes: `
      @keyframes float {
        0%, 100% {
          transform: translateY(0);
        }
        50% {
          transform: translateY(-8px);
        }
      }
    `,
    duration: 2000,
    easing: 'ease-in-out',
  },
};

// ============ Animation Labels for UI ============

export const ANIMATION_IN_OPTIONS: { value: AnimationIn; label: string }[] = [
  { value: 'none', label: 'Nenhuma' },
  { value: 'bounce', label: 'Bounce' },
  { value: 'zoomIn', label: 'Zoom In' },
  { value: 'slideLeft', label: 'Deslizar Esquerda' },
  { value: 'slideUp', label: 'Deslizar Cima' },
  { value: 'fadeIn', label: 'Fade In' },
  { value: 'typewriter', label: 'Maquina de Escrever' },
];

export const ANIMATION_OUT_OPTIONS: { value: AnimationOut; label: string }[] = [
  { value: 'none', label: 'Nenhuma' },
  { value: 'bounce', label: 'Bounce' },
  { value: 'zoomOut', label: 'Zoom Out' },
  { value: 'slideRight', label: 'Deslizar Direita' },
  { value: 'fadeOut', label: 'Fade Out' },
];

export const ANIMATION_LOOP_OPTIONS: { value: AnimationLoop; label: string }[] = [
  { value: 'none', label: 'Nenhuma' },
  { value: 'pulse', label: 'Pulsar' },
  { value: 'shake', label: 'Tremer' },
  { value: 'float', label: 'Flutuar' },
];

// ============ CSS Generation ============

/**
 * Generate all animation keyframes CSS
 */
export function generateAnimationCSS(): string {
  const allKeyframes: string[] = [];

  Object.values(ANIMATIONS_IN).forEach((anim) => {
    allKeyframes.push(anim.keyframes);
  });

  Object.values(ANIMATIONS_OUT).forEach((anim) => {
    allKeyframes.push(anim.keyframes);
  });

  Object.values(ANIMATIONS_LOOP).forEach((anim) => {
    allKeyframes.push(anim.keyframes);
  });

  return allKeyframes.join('\n');
}

/**
 * Get animation style object for a subtitle
 */
export function getAnimationStyle(
  animationIn: AnimationIn,
  animationOut: AnimationOut,
  animationLoop: AnimationLoop,
  phase: 'in' | 'visible' | 'out'
): React.CSSProperties {
  const style: React.CSSProperties = {};

  if (phase === 'in' && animationIn !== 'none') {
    const anim = ANIMATIONS_IN[animationIn];
    style.animation = `${anim.name} ${anim.duration}ms ${anim.easing} forwards`;
  } else if (phase === 'out' && animationOut !== 'none') {
    const anim = ANIMATIONS_OUT[animationOut];
    style.animation = `${anim.name} ${anim.duration}ms ${anim.easing} forwards`;
  } else if (phase === 'visible' && animationLoop !== 'none') {
    const anim = ANIMATIONS_LOOP[animationLoop];
    style.animation = `${anim.name} ${anim.duration}ms ${anim.easing} infinite`;
  }

  return style;
}

/**
 * Get animation duration for phase calculation
 */
export function getAnimationDuration(animation: AnimationIn | AnimationOut): number {
  if (animation === 'none') return 0;

  if (animation in ANIMATIONS_IN) {
    return ANIMATIONS_IN[animation as keyof typeof ANIMATIONS_IN].duration;
  }

  if (animation in ANIMATIONS_OUT) {
    return ANIMATIONS_OUT[animation as keyof typeof ANIMATIONS_OUT].duration;
  }

  return 0;
}
