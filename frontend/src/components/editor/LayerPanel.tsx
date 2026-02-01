'use client';

import { Eye, EyeOff, Lock, Unlock, Settings, Film, Type, FileText } from 'lucide-react';
import { Layer } from '@/lib/editorApi';

interface LayerPanelProps {
  layers: Layer[];
  onToggleVisibility: (layerId: string) => void;
  onToggleLock: (layerId: string) => void;
  onLayerSettings: (layerId: string) => void;
  activeLayerId?: string;
  onSelectLayer?: (layerId: string) => void;
}

const layerIcons: Record<Layer['type'], React.ReactNode> = {
  video: <Film className="w-4 h-4" />,
  subtitle: <Type className="w-4 h-4" />,
  text: <FileText className="w-4 h-4" />,
};

export default function LayerPanel({
  layers,
  onToggleVisibility,
  onToggleLock,
  onLayerSettings,
  activeLayerId,
  onSelectLayer,
}: LayerPanelProps) {
  return (
    <div className="bg-dark-800 rounded-lg p-4 space-y-3">
      <h3 className="font-medium text-sm text-gray-300 uppercase tracking-wide flex items-center gap-2">
        <span className="text-lg">📋</span> Camadas
      </h3>

      <div className="space-y-1">
        {layers.map((layer) => (
          <div
            key={layer.id}
            className={`flex items-center gap-2 p-2 rounded-lg transition-colors cursor-pointer ${
              activeLayerId === layer.id
                ? 'bg-primary/20 border border-primary/50'
                : 'bg-dark-700 hover:bg-dark-600 border border-transparent'
            }`}
            onClick={() => onSelectLayer?.(layer.id)}
          >
            {/* Visibility Toggle */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleVisibility(layer.id);
              }}
              className={`p-1 rounded transition-colors ${
                layer.visible
                  ? 'text-primary hover:bg-primary/20'
                  : 'text-gray-500 hover:bg-dark-500'
              }`}
              title={layer.visible ? 'Ocultar camada' : 'Mostrar camada'}
            >
              {layer.visible ? (
                <Eye className="w-4 h-4" />
              ) : (
                <EyeOff className="w-4 h-4" />
              )}
            </button>

            {/* Layer Icon */}
            <span className={`${layer.visible ? 'text-white' : 'text-gray-500'}`}>
              {layerIcons[layer.type]}
            </span>

            {/* Layer Name */}
            <span
              className={`flex-1 text-sm ${
                layer.visible ? 'text-white' : 'text-gray-500'
              }`}
            >
              {layer.name}
            </span>

            {/* Lock Toggle */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleLock(layer.id);
              }}
              className={`p-1 rounded transition-colors ${
                layer.locked
                  ? 'text-yellow-500 hover:bg-yellow-500/20'
                  : 'text-gray-500 hover:bg-dark-500'
              }`}
              title={layer.locked ? 'Desbloquear camada' : 'Bloquear camada'}
            >
              {layer.locked ? (
                <Lock className="w-3 h-3" />
              ) : (
                <Unlock className="w-3 h-3" />
              )}
            </button>

            {/* Settings Button (only for subtitle layer) */}
            {layer.type === 'subtitle' && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onLayerSettings(layer.id);
                }}
                className="p-1 rounded text-gray-400 hover:text-white hover:bg-dark-500 transition-colors"
                title="Configurar estilo"
              >
                <Settings className="w-3 h-3" />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="pt-2 border-t border-dark-600">
        <p className="text-xs text-gray-500">
          Clique no olho para mostrar/ocultar camadas
        </p>
      </div>
    </div>
  );
}
