'use client';

import { useState } from 'react';
import {
  Palette,
  Plus,
  Check,
  Copy,
  Trash2,
  Download,
  Upload,
  Edit3,
  X,
  ChevronRight,
} from 'lucide-react';
import { useBrandKitStore, BrandKit } from '@/stores/brandKitStore';
import { SubtitleStyle } from '@/lib/editorApi';

interface BrandKitPanelProps {
  currentStyle: SubtitleStyle;
  onApplyStyle: (style: SubtitleStyle) => void;
}

export default function BrandKitPanel({ currentStyle, onApplyStyle }: BrandKitPanelProps) {
  const {
    brandKits,
    activeBrandKitId,
    setActiveBrandKit,
    createBrandKit,
    updateBrandKit,
    deleteBrandKit,
    duplicateBrandKit,
    exportBrandKit,
    importBrandKit,
    applyToSubtitleStyle,
  } = useBrandKitStore();

  const [isCreating, setIsCreating] = useState(false);
  const [newKitName, setNewKitName] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [showImport, setShowImport] = useState(false);
  const [importJson, setImportJson] = useState('');

  const handleCreateKit = () => {
    if (!newKitName.trim()) return;

    const newKit = createBrandKit(newKitName, {
      subtitleStyle: currentStyle,
    });

    setNewKitName('');
    setIsCreating(false);
    setActiveBrandKit(newKit.id);
  };

  const handleApplyKit = (kitId: string) => {
    const style = applyToSubtitleStyle(kitId);
    if (style) {
      onApplyStyle(style);
      setActiveBrandKit(kitId);
    }
  };

  const handleSaveCurrentToKit = (kitId: string) => {
    updateBrandKit(kitId, { subtitleStyle: currentStyle });
  };

  const handleExport = (kitId: string) => {
    const json = exportBrandKit(kitId);
    if (json) {
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `brandkit-${kitId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleImport = () => {
    if (!importJson.trim()) return;

    const imported = importBrandKit(importJson);
    if (imported) {
      setShowImport(false);
      setImportJson('');
      setActiveBrandKit(imported.id);
    }
  };

  const handleStartEdit = (kit: BrandKit) => {
    setEditingId(kit.id);
    setEditName(kit.name);
  };

  const handleSaveEdit = (kitId: string) => {
    if (editName.trim()) {
      updateBrandKit(kitId, { name: editName });
    }
    setEditingId(null);
    setEditName('');
  };

  return (
    <div className="bg-dark-800 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-sm text-gray-300 uppercase tracking-wide flex items-center gap-2">
          <Palette className="w-4 h-4" />
          Brand Kit
        </h3>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowImport(true)}
            className="p-1.5 hover:bg-dark-700 rounded transition-colors"
            title="Importar Kit"
          >
            <Upload className="w-4 h-4 text-gray-400" />
          </button>
          <button
            onClick={() => setIsCreating(true)}
            className="p-1.5 hover:bg-dark-700 rounded transition-colors"
            title="Criar Novo Kit"
          >
            <Plus className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Create New Kit */}
      {isCreating && (
        <div className="flex items-center gap-2 p-2 bg-dark-700 rounded-lg">
          <input
            type="text"
            value={newKitName}
            onChange={(e) => setNewKitName(e.target.value)}
            placeholder="Nome do Kit..."
            className="flex-1 px-2 py-1 bg-dark-600 border border-dark-500 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary"
            autoFocus
            onKeyDown={(e) => e.key === 'Enter' && handleCreateKit()}
          />
          <button
            onClick={handleCreateKit}
            className="p-1.5 bg-primary hover:bg-primary/80 rounded transition-colors"
          >
            <Check className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              setIsCreating(false);
              setNewKitName('');
            }}
            className="p-1.5 hover:bg-dark-600 rounded transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Import Modal */}
      {showImport && (
        <div className="p-3 bg-dark-700 rounded-lg space-y-2">
          <p className="text-xs text-gray-400">Cole o JSON do Brand Kit:</p>
          <textarea
            value={importJson}
            onChange={(e) => setImportJson(e.target.value)}
            className="w-full h-24 px-2 py-1 bg-dark-600 border border-dark-500 rounded text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary resize-none"
            placeholder='{"name": "Meu Kit", ...}'
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={() => {
                setShowImport(false);
                setImportJson('');
              }}
              className="px-3 py-1 text-xs hover:bg-dark-600 rounded transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleImport}
              className="px-3 py-1 text-xs bg-primary hover:bg-primary/80 rounded transition-colors"
            >
              Importar
            </button>
          </div>
        </div>
      )}

      {/* Brand Kit List */}
      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {brandKits.map((kit) => {
          const isActive = activeBrandKitId === kit.id;
          const isEditing = editingId === kit.id;
          const isDefault = kit.id.startsWith('default-');

          return (
            <div
              key={kit.id}
              className={`group p-3 rounded-lg border transition-all cursor-pointer ${
                isActive
                  ? 'border-primary bg-primary/10'
                  : 'border-dark-600 bg-dark-700 hover:border-dark-500'
              }`}
              onClick={() => !isEditing && handleApplyKit(kit.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  {isEditing ? (
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="flex-1 px-2 py-1 bg-dark-600 border border-dark-500 rounded text-sm text-white focus:outline-none focus:border-primary"
                        autoFocus
                        onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit(kit.id)}
                      />
                      <button
                        onClick={() => handleSaveEdit(kit.id)}
                        className="p-1 hover:bg-dark-600 rounded"
                      >
                        <Check className="w-3 h-3 text-green-500" />
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="p-1 hover:bg-dark-600 rounded"
                      >
                        <X className="w-3 h-3 text-gray-400" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-white truncate">
                          {kit.name}
                        </span>
                        {isActive && (
                          <Check className="w-3 h-3 text-primary flex-shrink-0" />
                        )}
                      </div>
                      {kit.description && (
                        <p className="text-xs text-gray-500 mt-0.5 truncate">
                          {kit.description}
                        </p>
                      )}
                    </>
                  )}
                </div>

                {/* Actions */}
                {!isEditing && (
                  <div
                    className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {isActive && (
                      <button
                        onClick={() => handleSaveCurrentToKit(kit.id)}
                        className="p-1 hover:bg-dark-600 rounded"
                        title="Salvar estilo atual"
                      >
                        <Download className="w-3 h-3 text-primary" />
                      </button>
                    )}
                    {!isDefault && (
                      <button
                        onClick={() => handleStartEdit(kit)}
                        className="p-1 hover:bg-dark-600 rounded"
                        title="Editar nome"
                      >
                        <Edit3 className="w-3 h-3 text-gray-400" />
                      </button>
                    )}
                    <button
                      onClick={() => duplicateBrandKit(kit.id, `${kit.name} (copia)`)}
                      className="p-1 hover:bg-dark-600 rounded"
                      title="Duplicar"
                    >
                      <Copy className="w-3 h-3 text-gray-400" />
                    </button>
                    <button
                      onClick={() => handleExport(kit.id)}
                      className="p-1 hover:bg-dark-600 rounded"
                      title="Exportar"
                    >
                      <Upload className="w-3 h-3 text-gray-400" />
                    </button>
                    {!isDefault && (
                      <button
                        onClick={() => deleteBrandKit(kit.id)}
                        className="p-1 hover:bg-dark-600 rounded"
                        title="Excluir"
                      >
                        <Trash2 className="w-3 h-3 text-red-400" />
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Color Preview */}
              <div className="flex items-center gap-1 mt-2">
                <div
                  className="w-4 h-4 rounded border border-dark-500"
                  style={{ backgroundColor: kit.colors.primary }}
                  title="Cor Primaria"
                />
                <div
                  className="w-4 h-4 rounded border border-dark-500"
                  style={{ backgroundColor: kit.colors.secondary }}
                  title="Cor Secundaria"
                />
                <div
                  className="w-4 h-4 rounded border border-dark-500"
                  style={{ backgroundColor: kit.colors.accent }}
                  title="Cor de Destaque"
                />
                <ChevronRight className="w-3 h-3 text-gray-500 ml-auto" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Help Text */}
      <p className="text-xs text-gray-500 text-center">
        Clique em um kit para aplicar o estilo
      </p>
    </div>
  );
}
