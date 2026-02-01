'use client';

import { useState } from 'react';
import { Plus, Trash2, Type, AlignCenter, AlignLeft, AlignRight } from 'lucide-react';

export interface TextOverlay {
  id: string;
  text: string;
  x: string;
  y: string;
  fontSize: number;
  fontColor: string;
  startTime: number;
  endTime: number | null;
  backgroundColor: string | null;
  backgroundOpacity: number;
}

interface TextOverlayEditorProps {
  overlays: TextOverlay[];
  duration: number;
  currentTime: number;
  onOverlaysChange: (overlays: TextOverlay[]) => void;
}

const COLORS = [
  { name: 'Branco', value: 'white' },
  { name: 'Preto', value: 'black' },
  { name: 'Amarelo', value: 'yellow' },
  { name: 'Vermelho', value: 'red' },
  { name: 'Verde', value: 'green' },
  { name: 'Azul', value: 'blue' },
  { name: 'Rosa', value: 'pink' },
  { name: 'Laranja', value: 'orange' },
];

const POSITIONS = [
  { name: 'Topo', x: '(w-text_w)/2', y: '50' },
  { name: 'Centro', x: '(w-text_w)/2', y: '(h-text_h)/2' },
  { name: 'Embaixo', x: '(w-text_w)/2', y: 'h-100' },
];

export default function TextOverlayEditor({
  overlays,
  duration,
  currentTime,
  onOverlaysChange,
}: TextOverlayEditorProps) {
  const [editingId, setEditingId] = useState<string | null>(null);

  const addOverlay = () => {
    const newOverlay: TextOverlay = {
      id: `text_${Date.now()}`,
      text: 'Novo texto',
      x: '(w-text_w)/2',
      y: 'h-100',
      fontSize: 48,
      fontColor: 'white',
      startTime: currentTime,
      endTime: null,
      backgroundColor: null,
      backgroundOpacity: 0.5,
    };

    onOverlaysChange([...overlays, newOverlay]);
    setEditingId(newOverlay.id);
  };

  const updateOverlay = (id: string, updates: Partial<TextOverlay>) => {
    onOverlaysChange(
      overlays.map((overlay) =>
        overlay.id === id ? { ...overlay, ...updates } : overlay
      )
    );
  };

  const deleteOverlay = (id: string) => {
    onOverlaysChange(overlays.filter((overlay) => overlay.id !== id));
  };

  const isActive = (overlay: TextOverlay): boolean => {
    const endTime = overlay.endTime ?? duration;
    return currentTime >= overlay.startTime && currentTime <= endTime;
  };

  return (
    <div className="bg-dark-800 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium flex items-center gap-2">
          <Type className="w-5 h-5 text-primary" />
          Textos
        </h3>
        <button
          onClick={addOverlay}
          className="flex items-center gap-1 px-3 py-1.5 bg-primary hover:bg-primary/80 rounded text-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Adicionar
        </button>
      </div>

      {overlays.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Type className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Nenhum texto</p>
          <p className="text-sm">Adicione textos sobre o video</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-80 overflow-y-auto">
          {overlays.map((overlay) => (
            <div
              key={overlay.id}
              className={`p-3 rounded-lg border transition-colors ${
                isActive(overlay)
                  ? 'bg-primary/20 border-primary'
                  : 'bg-dark-700 border-dark-600'
              }`}
            >
              <div className="flex items-start gap-2">
                <div className="flex-1 space-y-3">
                  {/* Text input */}
                  <input
                    type="text"
                    value={overlay.text}
                    onChange={(e) => updateOverlay(overlay.id, { text: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-900 rounded focus:ring-1 focus:ring-primary outline-none"
                    placeholder="Digite o texto..."
                  />

                  {/* Position and style */}
                  <div className="grid grid-cols-2 gap-2">
                    {/* Position */}
                    <div>
                      <label className="text-xs text-gray-500 mb-1 block">Posicao</label>
                      <select
                        value={`${overlay.x}|${overlay.y}`}
                        onChange={(e) => {
                          const [x, y] = e.target.value.split('|');
                          updateOverlay(overlay.id, { x, y });
                        }}
                        className="w-full px-2 py-1.5 bg-dark-900 rounded text-sm focus:ring-1 focus:ring-primary outline-none"
                      >
                        {POSITIONS.map((pos) => (
                          <option key={pos.name} value={`${pos.x}|${pos.y}`}>
                            {pos.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Font size */}
                    <div>
                      <label className="text-xs text-gray-500 mb-1 block">Tamanho</label>
                      <input
                        type="number"
                        value={overlay.fontSize}
                        onChange={(e) =>
                          updateOverlay(overlay.id, {
                            fontSize: Math.max(12, Math.min(200, parseInt(e.target.value) || 48)),
                          })
                        }
                        className="w-full px-2 py-1.5 bg-dark-900 rounded text-sm focus:ring-1 focus:ring-primary outline-none"
                        min={12}
                        max={200}
                      />
                    </div>
                  </div>

                  {/* Colors */}
                  <div className="grid grid-cols-2 gap-2">
                    {/* Font color */}
                    <div>
                      <label className="text-xs text-gray-500 mb-1 block">Cor do texto</label>
                      <select
                        value={overlay.fontColor}
                        onChange={(e) => updateOverlay(overlay.id, { fontColor: e.target.value })}
                        className="w-full px-2 py-1.5 bg-dark-900 rounded text-sm focus:ring-1 focus:ring-primary outline-none"
                      >
                        {COLORS.map((color) => (
                          <option key={color.value} value={color.value}>
                            {color.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Background */}
                    <div>
                      <label className="text-xs text-gray-500 mb-1 block">Fundo</label>
                      <select
                        value={overlay.backgroundColor || 'none'}
                        onChange={(e) =>
                          updateOverlay(overlay.id, {
                            backgroundColor: e.target.value === 'none' ? null : e.target.value,
                          })
                        }
                        className="w-full px-2 py-1.5 bg-dark-900 rounded text-sm focus:ring-1 focus:ring-primary outline-none"
                      >
                        <option value="none">Nenhum</option>
                        {COLORS.map((color) => (
                          <option key={color.value} value={color.value}>
                            {color.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Timing */}
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-gray-500 mb-1 block">Inicio (s)</label>
                      <input
                        type="number"
                        value={overlay.startTime}
                        onChange={(e) =>
                          updateOverlay(overlay.id, {
                            startTime: Math.max(0, parseFloat(e.target.value) || 0),
                          })
                        }
                        className="w-full px-2 py-1.5 bg-dark-900 rounded text-sm focus:ring-1 focus:ring-primary outline-none"
                        min={0}
                        step={0.1}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500 mb-1 block">Fim (s)</label>
                      <input
                        type="number"
                        value={overlay.endTime ?? ''}
                        onChange={(e) =>
                          updateOverlay(overlay.id, {
                            endTime: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        }
                        placeholder="Ate o fim"
                        className="w-full px-2 py-1.5 bg-dark-900 rounded text-sm focus:ring-1 focus:ring-primary outline-none"
                        min={overlay.startTime}
                        step={0.1}
                      />
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => deleteOverlay(overlay.id)}
                  className="p-1 hover:bg-red-500/20 hover:text-red-500 rounded transition-colors"
                  title="Excluir texto"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
