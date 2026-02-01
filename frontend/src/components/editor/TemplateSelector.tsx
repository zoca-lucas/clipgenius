'use client';

import { useState } from 'react';
import { X, Check, Sparkles } from 'lucide-react';
import { SubtitleStyle } from '@/lib/editorApi';
import { SUBTITLE_TEMPLATES, SubtitleTemplate, getTemplateCategories } from '@/lib/subtitleTemplates';

interface TemplateSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTemplate: (style: SubtitleStyle) => void;
  currentStyle?: SubtitleStyle;
}

export default function TemplateSelector({
  isOpen,
  onClose,
  onSelectTemplate,
  currentStyle,
}: TemplateSelectorProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('trending');
  const [hoveredTemplate, setHoveredTemplate] = useState<string | null>(null);

  if (!isOpen) return null;

  const categories = getTemplateCategories();
  const currentCategoryTemplates = SUBTITLE_TEMPLATES.filter(
    (t) => selectedCategory === 'all' || t.category === selectedCategory
  );

  const handleSelectTemplate = (template: SubtitleTemplate) => {
    onSelectTemplate(template.style);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-dark-800 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden border border-dark-600">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-dark-600">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold text-white">Templates de Legenda</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-dark-700 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Category Tabs */}
        <div className="flex gap-2 px-6 py-3 border-b border-dark-700 overflow-x-auto">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors ${
              selectedCategory === 'all'
                ? 'bg-primary text-white'
                : 'bg-dark-700 text-gray-300 hover:bg-dark-600'
            }`}
          >
            Todos
          </button>
          {categories.map((cat) => (
            <button
              key={cat.category}
              onClick={() => setSelectedCategory(cat.category)}
              className={`px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors ${
                selectedCategory === cat.category
                  ? 'bg-primary text-white'
                  : 'bg-dark-700 text-gray-300 hover:bg-dark-600'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Templates Grid */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
          <div className="grid grid-cols-2 gap-4">
            {currentCategoryTemplates.map((template) => (
              <button
                key={template.id}
                onClick={() => handleSelectTemplate(template)}
                onMouseEnter={() => setHoveredTemplate(template.id)}
                onMouseLeave={() => setHoveredTemplate(null)}
                className={`relative p-4 bg-dark-900 rounded-lg border-2 transition-all hover:scale-[1.02] ${
                  hoveredTemplate === template.id
                    ? 'border-primary'
                    : 'border-dark-700 hover:border-dark-500'
                }`}
              >
                {/* Preview Area */}
                <div
                  className="h-24 rounded-lg mb-3 flex items-center justify-center overflow-hidden"
                  style={{
                    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
                  }}
                >
                  <span
                    style={{
                      fontFamily: template.style.fontName,
                      fontSize: `${Math.min(template.style.fontSize / 2, 24)}px`,
                      color: template.style.primaryColor,
                      textShadow: template.style.outlineSize > 0
                        ? `${template.style.outlineSize / 2}px ${template.style.outlineSize / 2}px ${template.style.shadowSize / 2}px ${template.style.outlineColor}`
                        : 'none',
                      textTransform: template.style.uppercase ? 'uppercase' : 'none',
                      padding: template.style.backgroundEnabled ? '4px 8px' : undefined,
                      backgroundColor: template.style.backgroundEnabled
                        ? template.style.backgroundColor
                        : undefined,
                      borderRadius: template.style.backgroundEnabled ? '4px' : undefined,
                    }}
                  >
                    Exemplo{' '}
                    <span style={{ color: template.style.highlightColor }}>texto</span>
                  </span>
                </div>

                {/* Template Info */}
                <div className="text-left">
                  <h3 className="font-medium text-white mb-1">{template.name}</h3>
                  <p className="text-xs text-gray-400 line-clamp-2">{template.description}</p>
                </div>

                {/* Category Badge */}
                <div className="absolute top-2 right-2">
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      template.category === 'trending'
                        ? 'bg-red-500/20 text-red-400'
                        : template.category === 'creative'
                        ? 'bg-purple-500/20 text-purple-400'
                        : template.category === 'minimal'
                        ? 'bg-blue-500/20 text-blue-400'
                        : 'bg-gray-500/20 text-gray-400'
                    }`}
                  >
                    {template.category === 'trending'
                      ? 'Em Alta'
                      : template.category === 'creative'
                      ? 'Criativo'
                      : template.category === 'minimal'
                      ? 'Minimal'
                      : 'Classico'}
                  </span>
                </div>

                {/* Selected Indicator */}
                {hoveredTemplate === template.id && (
                  <div className="absolute inset-0 bg-primary/10 rounded-lg flex items-center justify-center">
                    <div className="bg-primary rounded-full p-2">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
