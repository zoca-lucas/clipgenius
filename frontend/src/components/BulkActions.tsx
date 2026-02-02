'use client';

import { useState } from 'react';
import {
  CheckSquare,
  Square,
  Download,
  Trash2,
  Palette,
  X,
  Loader2,
  CheckCheck,
  MinusSquare,
} from 'lucide-react';
import { useBrandKitStore } from '@/stores/brandKitStore';

interface ClipItem {
  id: number;
  title?: string;
  duration?: number;
  thumbnail_url?: string;
  viral_score?: number;
}

interface BulkActionsProps {
  clips: ClipItem[];
  selectedIds: Set<number>;
  onSelectionChange: (ids: Set<number>) => void;
  onBulkExport: (ids: number[], options: BulkExportOptions) => Promise<void>;
  onBulkDelete: (ids: number[]) => Promise<void>;
  onBulkApplyBrandKit: (ids: number[], brandKitId: string) => Promise<void>;
}

export interface BulkExportOptions {
  format: 'vertical' | 'square' | 'landscape';
  includeSubtitles: boolean;
  brandKitId?: string;
}

export default function BulkActions({
  clips,
  selectedIds,
  onSelectionChange,
  onBulkExport,
  onBulkDelete,
  onBulkApplyBrandKit,
}: BulkActionsProps) {
  const { brandKits } = useBrandKitStore();
  const [isProcessing, setIsProcessing] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showBrandKitModal, setShowBrandKitModal] = useState(false);
  const [exportOptions, setExportOptions] = useState<BulkExportOptions>({
    format: 'vertical',
    includeSubtitles: true,
  });

  const selectedCount = selectedIds.size;
  const isAllSelected = selectedCount === clips.length && clips.length > 0;
  const isSomeSelected = selectedCount > 0 && selectedCount < clips.length;

  const handleSelectAll = () => {
    if (isAllSelected) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(clips.map((c) => c.id)));
    }
  };

  const handleClearSelection = () => {
    onSelectionChange(new Set());
  };

  const handleExport = async () => {
    if (selectedCount === 0) return;

    setIsProcessing(true);
    try {
      await onBulkExport(Array.from(selectedIds), exportOptions);
      setShowExportModal(false);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async () => {
    if (selectedCount === 0) return;

    const confirmed = window.confirm(
      `Tem certeza que deseja excluir ${selectedCount} clip(s)? Esta acao nao pode ser desfeita.`
    );

    if (!confirmed) return;

    setIsProcessing(true);
    try {
      await onBulkDelete(Array.from(selectedIds));
      onSelectionChange(new Set());
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApplyBrandKit = async (brandKitId: string) => {
    if (selectedCount === 0) return;

    setIsProcessing(true);
    try {
      await onBulkApplyBrandKit(Array.from(selectedIds), brandKitId);
      setShowBrandKitModal(false);
    } finally {
      setIsProcessing(false);
    }
  };

  if (clips.length === 0) return null;

  return (
    <>
      {/* Bulk Actions Bar */}
      <div className="bg-dark-800 border border-dark-700 rounded-lg p-3">
        <div className="flex items-center justify-between">
          {/* Selection Controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleSelectAll}
              className="flex items-center gap-2 px-3 py-1.5 hover:bg-dark-700 rounded transition-colors"
            >
              {isAllSelected ? (
                <CheckSquare className="w-4 h-4 text-primary" />
              ) : isSomeSelected ? (
                <MinusSquare className="w-4 h-4 text-primary" />
              ) : (
                <Square className="w-4 h-4 text-gray-400" />
              )}
              <span className="text-sm text-gray-300">
                {isAllSelected ? 'Desmarcar todos' : 'Selecionar todos'}
              </span>
            </button>

            {selectedCount > 0 && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 rounded">
                <CheckCheck className="w-4 h-4 text-primary" />
                <span className="text-sm text-primary font-medium">
                  {selectedCount} selecionado(s)
                </span>
                <button
                  onClick={handleClearSelection}
                  className="ml-1 p-0.5 hover:bg-primary/20 rounded"
                >
                  <X className="w-3 h-3 text-primary" />
                </button>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          {selectedCount > 0 && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowBrandKitModal(true)}
                disabled={isProcessing}
                className="flex items-center gap-2 px-3 py-1.5 bg-dark-700 hover:bg-dark-600 rounded transition-colors disabled:opacity-50"
              >
                <Palette className="w-4 h-4 text-purple-400" />
                <span className="text-sm">Aplicar Brand Kit</span>
              </button>

              <button
                onClick={() => setShowExportModal(true)}
                disabled={isProcessing}
                className="flex items-center gap-2 px-3 py-1.5 bg-primary hover:bg-primary/80 rounded transition-colors disabled:opacity-50"
              >
                {isProcessing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                <span className="text-sm">Exportar</span>
              </button>

              <button
                onClick={handleDelete}
                disabled={isProcessing}
                className="flex items-center gap-2 px-3 py-1.5 bg-red-600 hover:bg-red-500 rounded transition-colors disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
                <span className="text-sm">Excluir</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="bg-dark-800 rounded-xl p-6 w-full max-w-md border border-dark-600">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">
                Exportar {selectedCount} clip(s)
              </h2>
              <button
                onClick={() => setShowExportModal(false)}
                className="p-1 hover:bg-dark-700 rounded transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Format Selection */}
              <div className="space-y-2">
                <label className="text-sm text-gray-300">Formato</label>
                <select
                  value={exportOptions.format}
                  onChange={(e) =>
                    setExportOptions({
                      ...exportOptions,
                      format: e.target.value as BulkExportOptions['format'],
                    })
                  }
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-1 focus:ring-primary outline-none"
                >
                  <option value="vertical">Vertical (9:16) - TikTok/Reels</option>
                  <option value="square">Quadrado (1:1) - Instagram</option>
                  <option value="landscape">Paisagem (16:9) - YouTube</option>
                </select>
              </div>

              {/* Include Subtitles */}
              <div className="flex items-center justify-between py-2">
                <label className="text-sm text-gray-300">Incluir Legendas</label>
                <button
                  onClick={() =>
                    setExportOptions({
                      ...exportOptions,
                      includeSubtitles: !exportOptions.includeSubtitles,
                    })
                  }
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    exportOptions.includeSubtitles ? 'bg-primary' : 'bg-dark-600'
                  }`}
                >
                  <span
                    className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      exportOptions.includeSubtitles ? 'left-7' : 'left-1'
                    }`}
                  />
                </button>
              </div>

              {/* Brand Kit Selection */}
              <div className="space-y-2">
                <label className="text-sm text-gray-300">Brand Kit (opcional)</label>
                <select
                  value={exportOptions.brandKitId || ''}
                  onChange={(e) =>
                    setExportOptions({
                      ...exportOptions,
                      brandKitId: e.target.value || undefined,
                    })
                  }
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-1 focus:ring-primary outline-none"
                >
                  <option value="">Nenhum (usar estilo atual)</option>
                  {brandKits.map((kit) => (
                    <option key={kit.id} value={kit.id}>
                      {kit.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowExportModal(false)}
                className="flex-1 px-4 py-2 bg-dark-700 hover:bg-dark-600 rounded-lg transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleExport}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 bg-primary hover:bg-primary/80 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Exportando...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    Exportar
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Brand Kit Modal */}
      {showBrandKitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="bg-dark-800 rounded-xl p-6 w-full max-w-md border border-dark-600">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">
                Aplicar Brand Kit
              </h2>
              <button
                onClick={() => setShowBrandKitModal(false)}
                className="p-1 hover:bg-dark-700 rounded transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-sm text-gray-400 mb-4">
              Selecione um Brand Kit para aplicar a {selectedCount} clip(s):
            </p>

            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {brandKits.map((kit) => (
                <button
                  key={kit.id}
                  onClick={() => handleApplyBrandKit(kit.id)}
                  disabled={isProcessing}
                  className="w-full p-3 bg-dark-700 hover:bg-dark-600 rounded-lg text-left transition-colors disabled:opacity-50"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-medium text-white">{kit.name}</span>
                      {kit.description && (
                        <p className="text-xs text-gray-500 mt-0.5">
                          {kit.description}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <div
                        className="w-3 h-3 rounded"
                        style={{ backgroundColor: kit.colors.primary }}
                      />
                      <div
                        className="w-3 h-3 rounded"
                        style={{ backgroundColor: kit.colors.secondary }}
                      />
                      <div
                        className="w-3 h-3 rounded"
                        style={{ backgroundColor: kit.colors.accent }}
                      />
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <button
              onClick={() => setShowBrandKitModal(false)}
              className="w-full mt-4 px-4 py-2 bg-dark-700 hover:bg-dark-600 rounded-lg transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </>
  );
}

// Clip Selection Card component
export function ClipSelectionCard({
  clip,
  isSelected,
  onToggle,
}: {
  clip: ClipItem;
  isSelected: boolean;
  onToggle: () => void;
}) {
  return (
    <div
      className={`relative cursor-pointer transition-all ${
        isSelected ? 'ring-2 ring-primary' : ''
      }`}
      onClick={onToggle}
    >
      {/* Selection Checkbox */}
      <div
        className={`absolute top-2 left-2 z-10 w-6 h-6 rounded flex items-center justify-center transition-colors ${
          isSelected ? 'bg-primary' : 'bg-dark-800/80 hover:bg-dark-700'
        }`}
      >
        {isSelected ? (
          <CheckSquare className="w-4 h-4 text-white" />
        ) : (
          <Square className="w-4 h-4 text-gray-400" />
        )}
      </div>

      {/* Clip Content */}
      <div className="bg-dark-800 rounded-lg overflow-hidden border border-dark-700">
        {clip.thumbnail_url ? (
          <div className="aspect-[9/16] bg-dark-900">
            <img
              src={clip.thumbnail_url}
              alt={clip.title || 'Clip'}
              className="w-full h-full object-cover"
            />
          </div>
        ) : (
          <div className="aspect-[9/16] bg-dark-900 flex items-center justify-center">
            <span className="text-gray-600 text-4xl">📹</span>
          </div>
        )}
        <div className="p-3">
          <p className="text-sm font-medium text-white truncate">
            {clip.title || `Clip #${clip.id}`}
          </p>
          {clip.duration && (
            <p className="text-xs text-gray-500 mt-1">
              {Math.floor(clip.duration / 60)}:{String(Math.floor(clip.duration % 60)).padStart(2, '0')}
            </p>
          )}
          {clip.viral_score !== undefined && (
            <div className="flex items-center gap-1 mt-1">
              <span className="text-xs text-primary">🔥</span>
              <span className="text-xs text-gray-400">
                {Math.round(clip.viral_score * 100)}%
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
