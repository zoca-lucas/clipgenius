'use client';

import { Play, ArrowRight, RotateCw } from 'lucide-react';
import { AnimationIn, AnimationOut, AnimationLoop } from '@/lib/editorApi';
import {
  ANIMATION_IN_OPTIONS,
  ANIMATION_OUT_OPTIONS,
  ANIMATION_LOOP_OPTIONS,
} from '@/lib/textAnimations';

interface AnimationSelectorProps {
  animationIn: AnimationIn;
  animationOut: AnimationOut;
  animationLoop: AnimationLoop;
  onAnimationInChange: (value: AnimationIn) => void;
  onAnimationOutChange: (value: AnimationOut) => void;
  onAnimationLoopChange: (value: AnimationLoop) => void;
}

export default function AnimationSelector({
  animationIn,
  animationOut,
  animationLoop,
  onAnimationInChange,
  onAnimationOutChange,
  onAnimationLoopChange,
}: AnimationSelectorProps) {
  return (
    <div className="space-y-4">
      {/* Animation In */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <Play className="w-4 h-4 text-green-400" />
          Entrada
        </label>
        <div className="grid grid-cols-2 gap-2">
          {ANIMATION_IN_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => onAnimationInChange(option.value)}
              className={`px-3 py-2 rounded-lg text-sm transition-all ${
                animationIn === option.value
                  ? 'bg-primary text-white'
                  : 'bg-dark-700 text-gray-300 hover:bg-dark-600'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Animation Out */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <ArrowRight className="w-4 h-4 text-red-400" />
          Saida
        </label>
        <div className="grid grid-cols-2 gap-2">
          {ANIMATION_OUT_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => onAnimationOutChange(option.value)}
              className={`px-3 py-2 rounded-lg text-sm transition-all ${
                animationOut === option.value
                  ? 'bg-primary text-white'
                  : 'bg-dark-700 text-gray-300 hover:bg-dark-600'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Animation Loop */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <RotateCw className="w-4 h-4 text-blue-400" />
          Loop
        </label>
        <div className="grid grid-cols-2 gap-2">
          {ANIMATION_LOOP_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => onAnimationLoopChange(option.value)}
              className={`px-3 py-2 rounded-lg text-sm transition-all ${
                animationLoop === option.value
                  ? 'bg-primary text-white'
                  : 'bg-dark-700 text-gray-300 hover:bg-dark-600'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
