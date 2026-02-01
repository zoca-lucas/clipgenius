/**
 * ClipGenius - Subtitle Templates (CapCut/TikTok Style)
 * Pre-defined subtitle styles for quick selection
 */

import { SubtitleStyle } from './editorApi';

export interface SubtitleTemplate {
  id: string;
  name: string;
  description: string;
  category: 'trending' | 'classic' | 'minimal' | 'creative';
  style: SubtitleStyle;
}

export const SUBTITLE_TEMPLATES: SubtitleTemplate[] = [
  {
    id: 'tiktok-bold',
    name: 'TikTok Bold',
    description: 'Texto grande e impactante com outline forte',
    category: 'trending',
    style: {
      fontName: 'Impact',
      fontSize: 56,
      primaryColor: '#FFFFFF',
      highlightColor: '#FFFF00',
      outlineColor: '#000000',
      outlineSize: 4,
      shadowSize: 2,
      marginV: 120,
      karaokeEnabled: true,
      scaleEffect: true,
      animationIn: 'bounce',
      animationOut: 'none',
      animationLoop: 'none',
      uppercase: true,
      backgroundEnabled: false,
      backgroundColor: 'rgba(0,0,0,0.5)',
    },
  },
  {
    id: 'minimal',
    name: 'Minimal',
    description: 'Clean e moderno, perfeito para conteudo profissional',
    category: 'minimal',
    style: {
      fontName: 'Helvetica',
      fontSize: 32,
      primaryColor: '#FFFFFF',
      highlightColor: '#00D4FF',
      outlineColor: '#000000',
      outlineSize: 1,
      shadowSize: 0,
      marginV: 80,
      karaokeEnabled: false,
      scaleEffect: false,
      animationIn: 'fadeIn',
      animationOut: 'fadeOut',
      animationLoop: 'none',
      uppercase: false,
      backgroundEnabled: true,
      backgroundColor: 'rgba(0,0,0,0.6)',
    },
  },
  {
    id: 'neon-glow',
    name: 'Neon Glow',
    description: 'Efeito neon vibrante que brilha',
    category: 'creative',
    style: {
      fontName: 'Arial',
      fontSize: 48,
      primaryColor: '#FF00FF',
      highlightColor: '#00FFFF',
      outlineColor: '#FF00FF',
      outlineSize: 3,
      shadowSize: 8,
      marginV: 100,
      karaokeEnabled: true,
      scaleEffect: true,
      animationIn: 'zoomIn',
      animationOut: 'zoomOut',
      animationLoop: 'pulse',
      uppercase: false,
      backgroundEnabled: false,
      backgroundColor: 'rgba(0,0,0,0.5)',
    },
  },
  {
    id: 'karaoke-pop',
    name: 'Karaoke Pop',
    description: 'Destaque palavra por palavra com bounce',
    category: 'trending',
    style: {
      fontName: 'Arial',
      fontSize: 46,
      primaryColor: '#FFFFFF',
      highlightColor: '#FF6B6B',
      outlineColor: '#000000',
      outlineSize: 3,
      shadowSize: 2,
      marginV: 100,
      karaokeEnabled: true,
      scaleEffect: true,
      animationIn: 'slideUp',
      animationOut: 'fadeOut',
      animationLoop: 'none',
      uppercase: false,
      backgroundEnabled: false,
      backgroundColor: 'rgba(0,0,0,0.5)',
    },
  },
  {
    id: 'classic-subtitle',
    name: 'Classico',
    description: 'Estilo Netflix/YouTube tradicional',
    category: 'classic',
    style: {
      fontName: 'Arial',
      fontSize: 36,
      primaryColor: '#FFFFFF',
      highlightColor: '#FFFF00',
      outlineColor: '#000000',
      outlineSize: 2,
      shadowSize: 1,
      marginV: 60,
      karaokeEnabled: false,
      scaleEffect: false,
      animationIn: 'none',
      animationOut: 'none',
      animationLoop: 'none',
      uppercase: false,
      backgroundEnabled: true,
      backgroundColor: 'rgba(0,0,0,0.7)',
    },
  },
  {
    id: 'gradient-fire',
    name: 'Gradient Fire',
    description: 'Cores quentes com transicao suave',
    category: 'creative',
    style: {
      fontName: 'Impact',
      fontSize: 50,
      primaryColor: '#FF6B35',
      highlightColor: '#FFD700',
      outlineColor: '#8B0000',
      outlineSize: 3,
      shadowSize: 4,
      marginV: 110,
      karaokeEnabled: true,
      scaleEffect: true,
      animationIn: 'slideLeft',
      animationOut: 'slideRight',
      animationLoop: 'none',
      uppercase: true,
      backgroundEnabled: false,
      backgroundColor: 'rgba(0,0,0,0.5)',
    },
  },
  {
    id: 'gaming',
    name: 'Gaming',
    description: 'Estilo gamer com cores vibrantes',
    category: 'creative',
    style: {
      fontName: 'Impact',
      fontSize: 52,
      primaryColor: '#00FF00',
      highlightColor: '#FF0000',
      outlineColor: '#000000',
      outlineSize: 4,
      shadowSize: 3,
      marginV: 90,
      karaokeEnabled: true,
      scaleEffect: true,
      animationIn: 'bounce',
      animationOut: 'zoomOut',
      animationLoop: 'shake',
      uppercase: true,
      backgroundEnabled: false,
      backgroundColor: 'rgba(0,0,0,0.5)',
    },
  },
  {
    id: 'elegant',
    name: 'Elegante',
    description: 'Sofisticado e discreto',
    category: 'classic',
    style: {
      fontName: 'Georgia',
      fontSize: 34,
      primaryColor: '#F5F5DC',
      highlightColor: '#DAA520',
      outlineColor: '#2F2F2F',
      outlineSize: 1,
      shadowSize: 2,
      marginV: 70,
      karaokeEnabled: false,
      scaleEffect: false,
      animationIn: 'fadeIn',
      animationOut: 'fadeOut',
      animationLoop: 'none',
      uppercase: false,
      backgroundEnabled: false,
      backgroundColor: 'rgba(0,0,0,0.5)',
    },
  },
];

/**
 * Get templates by category
 */
export function getTemplatesByCategory(category: SubtitleTemplate['category']): SubtitleTemplate[] {
  return SUBTITLE_TEMPLATES.filter((t) => t.category === category);
}

/**
 * Get template by ID
 */
export function getTemplateById(id: string): SubtitleTemplate | undefined {
  return SUBTITLE_TEMPLATES.find((t) => t.id === id);
}

/**
 * Get all categories with their templates
 */
export function getTemplateCategories(): { category: SubtitleTemplate['category']; label: string; templates: SubtitleTemplate[] }[] {
  return [
    { category: 'trending', label: 'Em Alta', templates: getTemplatesByCategory('trending') },
    { category: 'classic', label: 'Classicos', templates: getTemplatesByCategory('classic') },
    { category: 'minimal', label: 'Minimalistas', templates: getTemplatesByCategory('minimal') },
    { category: 'creative', label: 'Criativos', templates: getTemplatesByCategory('creative') },
  ];
}
