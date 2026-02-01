'use client';

import { useState } from 'react';
import { Palette, Type, Move, Sparkles, Wand2, Play, ChevronDown, ChevronUp } from 'lucide-react';
import { SubtitleStyle, AnimationIn, AnimationOut, AnimationLoop } from '@/lib/editorApi';
import AnimationSelector from './AnimationSelector';
import TemplateSelector from './TemplateSelector';

interface SubtitleStylePanelProps {
  style: SubtitleStyle;
  onStyleChange: (style: SubtitleStyle) => void;
}

const FONT_OPTIONS = [
  { value: 'Arial', label: 'Arial' },
  { value: 'Helvetica', label: 'Helvetica' },
  { value: 'Impact', label: 'Impact' },
  { value: 'Verdana', label: 'Verdana' },
  { value: 'Georgia', label: 'Georgia' },
  { value: 'Times New Roman', label: 'Times New Roman' },
  { value: 'Courier New', label: 'Courier New' },
  { value: 'Comic Sans MS', label: 'Comic Sans' },
];

const PRESET_COLORS = [
  { name: 'Branco', value: '#FFFFFF' },
  { name: 'Amarelo', value: '#FFFF00' },
  { name: 'Ciano', value: '#00FFFF' },
  { name: 'Verde', value: '#00FF00' },
  { name: 'Rosa', value: '#FF00FF' },
  { name: 'Laranja', value: '#FFA500' },
  { name: 'Vermelho', value: '#FF0000' },
];

export default function SubtitleStylePanel({
  style,
  onStyleChange,
}: SubtitleStylePanelProps) {
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  const [showAnimations, setShowAnimations] = useState(false);

  const updateStyle = (updates: Partial<SubtitleStyle>) => {
    onStyleChange({ ...style, ...updates });
  };

  const handleSelectTemplate = (templateStyle: SubtitleStyle) => {
    onStyleChange(templateStyle);
  };

  return (
    <>
      <TemplateSelector
        isOpen={showTemplateSelector}
        onClose={() => setShowTemplateSelector(false)}
        onSelectTemplate={handleSelectTemplate}
        currentStyle={style}
      />
    <div className="bg-dark-800 rounded-lg p-4 space-y-4">
      <h3 className="font-medium text-sm text-gray-300 uppercase tracking-wide flex items-center gap-2">
        <span className="text-lg">🎨</span> Estilo da Legenda
      </h3>

      {/* Template Button */}
      <button
        onClick={() => setShowTemplateSelector(true)}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 rounded-lg text-white font-medium transition-all hover:scale-[1.02]"
      >
        <Wand2 className="w-5 h-5" />
        Usar Template
      </button>

      {/* Font Selection */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <Type className="w-4 h-4" />
          Fonte
        </label>
        <select
          value={style.fontName}
          onChange={(e) => updateStyle({ fontName: e.target.value })}
          className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-1 focus:ring-primary focus:border-primary outline-none"
        >
          {FONT_OPTIONS.map((font) => (
            <option key={font.value} value={font.value}>
              {font.label}
            </option>
          ))}
        </select>
      </div>

      {/* Font Size */}
      <div className="space-y-2">
        <label className="flex items-center justify-between text-sm text-gray-400">
          <span>Tamanho</span>
          <span className="text-white">{style.fontSize}px</span>
        </label>
        <input
          type="range"
          min="12"
          max="80"
          value={style.fontSize}
          onChange={(e) => updateStyle({ fontSize: parseInt(e.target.value) })}
          className="w-full h-2 bg-dark-700 rounded-lg appearance-none cursor-pointer accent-primary"
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>12px</span>
          <span>80px</span>
        </div>
      </div>

      {/* Primary Color */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <Palette className="w-4 h-4" />
          Cor Principal
        </label>
        <div className="flex items-center gap-2">
          <input
            type="color"
            value={style.primaryColor}
            onChange={(e) => updateStyle({ primaryColor: e.target.value })}
            className="w-10 h-10 rounded cursor-pointer border-2 border-dark-600"
          />
          <div className="flex gap-1 flex-wrap">
            {PRESET_COLORS.slice(0, 4).map((color) => (
              <button
                key={color.value}
                onClick={() => updateStyle({ primaryColor: color.value })}
                className={`w-6 h-6 rounded border-2 transition-all ${
                  style.primaryColor === color.value
                    ? 'border-primary scale-110'
                    : 'border-dark-600 hover:border-dark-500'
                }`}
                style={{ backgroundColor: color.value }}
                title={color.name}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Highlight Color (for Karaoke) */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <Sparkles className="w-4 h-4" />
          Cor de Destaque
        </label>
        <div className="flex items-center gap-2">
          <input
            type="color"
            value={style.highlightColor}
            onChange={(e) => updateStyle({ highlightColor: e.target.value })}
            className="w-10 h-10 rounded cursor-pointer border-2 border-dark-600"
          />
          <div className="flex gap-1 flex-wrap">
            {PRESET_COLORS.slice(1, 5).map((color) => (
              <button
                key={color.value}
                onClick={() => updateStyle({ highlightColor: color.value })}
                className={`w-6 h-6 rounded border-2 transition-all ${
                  style.highlightColor === color.value
                    ? 'border-primary scale-110'
                    : 'border-dark-600 hover:border-dark-500'
                }`}
                style={{ backgroundColor: color.value }}
                title={color.name}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Outline Size */}
      <div className="space-y-2">
        <label className="flex items-center justify-between text-sm text-gray-400">
          <span>Contorno</span>
          <span className="text-white">{style.outlineSize}px</span>
        </label>
        <input
          type="range"
          min="0"
          max="10"
          value={style.outlineSize}
          onChange={(e) => updateStyle({ outlineSize: parseInt(e.target.value) })}
          className="w-full h-2 bg-dark-700 rounded-lg appearance-none cursor-pointer accent-primary"
        />
      </div>

      {/* Shadow Size */}
      <div className="space-y-2">
        <label className="flex items-center justify-between text-sm text-gray-400">
          <span>Sombra</span>
          <span className="text-white">{style.shadowSize}px</span>
        </label>
        <input
          type="range"
          min="0"
          max="10"
          value={style.shadowSize}
          onChange={(e) => updateStyle({ shadowSize: parseInt(e.target.value) })}
          className="w-full h-2 bg-dark-700 rounded-lg appearance-none cursor-pointer accent-primary"
        />
      </div>

      {/* Vertical Margin */}
      <div className="space-y-2">
        <label className="flex items-center justify-between text-sm text-gray-400">
          <span className="flex items-center gap-2">
            <Move className="w-4 h-4" />
            Margem Vertical
          </span>
          <span className="text-white">{style.marginV}px</span>
        </label>
        <input
          type="range"
          min="20"
          max="300"
          value={style.marginV}
          onChange={(e) => updateStyle({ marginV: parseInt(e.target.value) })}
          className="w-full h-2 bg-dark-700 rounded-lg appearance-none cursor-pointer accent-primary"
        />
      </div>

      {/* Karaoke Toggle */}
      <div className="flex items-center justify-between py-2">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <Sparkles className="w-4 h-4" />
          Efeito Karaoke
        </label>
        <button
          onClick={() => updateStyle({ karaokeEnabled: !style.karaokeEnabled })}
          className={`relative w-12 h-6 rounded-full transition-colors ${
            style.karaokeEnabled ? 'bg-primary' : 'bg-dark-600'
          }`}
        >
          <span
            className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
              style.karaokeEnabled ? 'left-7' : 'left-1'
            }`}
          />
        </button>
      </div>

      {/* Scale Effect Toggle */}
      <div className="flex items-center justify-between py-2">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <span className="text-lg">📐</span>
          Efeito de Escala
        </label>
        <button
          onClick={() => updateStyle({ scaleEffect: !style.scaleEffect })}
          className={`relative w-12 h-6 rounded-full transition-colors ${
            style.scaleEffect ? 'bg-primary' : 'bg-dark-600'
          }`}
        >
          <span
            className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
              style.scaleEffect ? 'left-7' : 'left-1'
            }`}
          />
        </button>
      </div>

      {/* Uppercase Toggle */}
      <div className="flex items-center justify-between py-2">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <Type className="w-4 h-4" />
          Maiusculas
        </label>
        <button
          onClick={() => updateStyle({ uppercase: !style.uppercase })}
          className={`relative w-12 h-6 rounded-full transition-colors ${
            style.uppercase ? 'bg-primary' : 'bg-dark-600'
          }`}
        >
          <span
            className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
              style.uppercase ? 'left-7' : 'left-1'
            }`}
          />
        </button>
      </div>

      {/* Background Toggle */}
      <div className="flex items-center justify-between py-2">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <Palette className="w-4 h-4" />
          Fundo
        </label>
        <button
          onClick={() => updateStyle({ backgroundEnabled: !style.backgroundEnabled })}
          className={`relative w-12 h-6 rounded-full transition-colors ${
            style.backgroundEnabled ? 'bg-primary' : 'bg-dark-600'
          }`}
        >
          <span
            className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
              style.backgroundEnabled ? 'left-7' : 'left-1'
            }`}
          />
        </button>
      </div>

      {/* Animations Section */}
      <div className="border-t border-dark-600 pt-3">
        <button
          onClick={() => setShowAnimations(!showAnimations)}
          className="w-full flex items-center justify-between text-sm text-gray-300 hover:text-white transition-colors"
        >
          <span className="flex items-center gap-2">
            <Play className="w-4 h-4" />
            Animacoes
          </span>
          {showAnimations ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {showAnimations && (
          <div className="mt-3">
            <AnimationSelector
              animationIn={style.animationIn}
              animationOut={style.animationOut}
              animationLoop={style.animationLoop}
              onAnimationInChange={(value: AnimationIn) => updateStyle({ animationIn: value })}
              onAnimationOutChange={(value: AnimationOut) => updateStyle({ animationOut: value })}
              onAnimationLoopChange={(value: AnimationLoop) => updateStyle({ animationLoop: value })}
            />
          </div>
        )}
      </div>

      {/* Preview */}
      <div className="pt-3 border-t border-dark-600">
        <p className="text-xs text-gray-500 mb-2">Preview</p>
        <div
          className="p-4 bg-dark-900 rounded-lg flex items-center justify-center"
          style={{ minHeight: '60px' }}
        >
          <span
            style={{
              fontFamily: style.fontName,
              fontSize: `${Math.min(style.fontSize, 32)}px`,
              color: style.primaryColor,
              textShadow: style.outlineSize > 0
                ? `${style.outlineSize}px ${style.outlineSize}px ${style.shadowSize}px ${style.outlineColor}`
                : 'none',
            }}
          >
            Texto de <span style={{ color: style.highlightColor }}>exemplo</span>
          </span>
        </div>
      </div>
    </div>
    </>
  );
}
