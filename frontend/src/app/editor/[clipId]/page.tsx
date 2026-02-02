'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Save, Download, Loader2, X, Check, Palette, Undo2, Redo2 } from 'lucide-react';
import {
  getClipEditorData,
  updateSubtitles,
  exportClip,
  getEditorVideoUrl,
  getExportDownloadUrl,
  createDefaultLayers,
  getDefaultSubtitleStyle,
  styleFromBackend,
  ClipEditorData,
  SubtitleEntry,
  SubtitleStyle,
  Layer,
} from '@/lib/editorApi';
import { useEditorStore } from '@/stores/editorStore';
import VideoPreview, { VideoPreviewRef } from '@/components/editor/VideoPreview';
import MultiTrackTimeline from '@/components/editor/MultiTrackTimeline';
import LayerPanel from '@/components/editor/LayerPanel';
import SubtitleStylePanel from '@/components/editor/SubtitleStylePanel';
import BrandKitPanel from '@/components/editor/BrandKitPanel';
import { WaveformPlaceholder } from '@/components/editor/Waveform';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (includeSubtitles: boolean, format: string) => void;
  isExporting: boolean;
}

function ExportModal({ isOpen, onClose, onExport, isExporting }: ExportModalProps) {
  const [includeSubtitles, setIncludeSubtitles] = useState(true);
  const [format, setFormat] = useState('vertical');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-dark-800 rounded-xl p-6 w-full max-w-md border border-dark-600">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Exportar Clip</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-dark-700 rounded transition-colors"
            disabled={isExporting}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Include Subtitles Toggle */}
          <div className="flex items-center justify-between py-2">
            <label className="text-sm text-gray-300">Incluir Legendas</label>
            <button
              onClick={() => setIncludeSubtitles(!includeSubtitles)}
              disabled={isExporting}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                includeSubtitles ? 'bg-primary' : 'bg-dark-600'
              }`}
            >
              <span
                className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  includeSubtitles ? 'left-7' : 'left-1'
                }`}
              />
            </button>
          </div>

          {/* Format Selection */}
          <div className="space-y-2">
            <label className="text-sm text-gray-300">Formato</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              disabled={isExporting}
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-1 focus:ring-primary outline-none"
            >
              <option value="vertical">Vertical (9:16) - TikTok/Reels</option>
              <option value="square">Quadrado (1:1) - Instagram</option>
              <option value="landscape">Paisagem (16:9) - YouTube</option>
            </select>
          </div>

          {/* Info */}
          <div className="p-3 bg-dark-700 rounded-lg text-sm text-gray-400">
            {includeSubtitles ? (
              <p>As legendas serao queimadas no video com o estilo configurado.</p>
            ) : (
              <p>O video sera exportado sem legendas.</p>
            )}
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            disabled={isExporting}
            className="flex-1 px-4 py-2 bg-dark-700 hover:bg-dark-600 rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={() => onExport(includeSubtitles, format)}
            disabled={isExporting}
            className="flex-1 px-4 py-2 bg-primary hover:bg-primary/80 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {isExporting ? (
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
  );
}

export default function EditorPage() {
  const router = useRouter();
  const params = useParams();
  const clipId = parseInt(params.clipId as string);

  const videoPreviewRef = useRef<VideoPreviewRef>(null);
  const videoElementRef = useRef<HTMLVideoElement | null>(null);

  // State
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editorData, setEditorData] = useState<ClipEditorData | null>(null);

  // Editor state
  const [subtitles, setSubtitles] = useState<SubtitleEntry[]>([]);
  const [subtitleStyle, setSubtitleStyle] = useState<SubtitleStyle>(getDefaultSubtitleStyle());
  const [layers, setLayers] = useState<Layer[]>(createDefaultLayers());
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);

  // UI state
  const [showStylePanel, setShowStylePanel] = useState(false);
  const [showBrandKitPanel, setShowBrandKitPanel] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // History for undo/redo
  const [history, setHistory] = useState<{ subtitles: SubtitleEntry[]; style: SubtitleStyle }[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  const saveToHistory = useCallback(() => {
    const newEntry = { subtitles: [...subtitles], style: { ...subtitleStyle } };
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newEntry);
    if (newHistory.length > 30) newHistory.shift();
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [subtitles, subtitleStyle, history, historyIndex]);

  const undo = useCallback(() => {
    if (historyIndex > 0) {
      const prev = history[historyIndex - 1];
      setSubtitles(prev.subtitles);
      setSubtitleStyle(prev.style);
      setHistoryIndex(historyIndex - 1);
      setHasChanges(true);
    }
  }, [history, historyIndex]);

  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const next = history[historyIndex + 1];
      setSubtitles(next.subtitles);
      setSubtitleStyle(next.style);
      setHistoryIndex(historyIndex + 1);
      setHasChanges(true);
    }
  }, [history, historyIndex]);

  // Load editor data
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        const data = await getClipEditorData(clipId);
        setEditorData(data);

        // Initialize subtitles
        setSubtitles(data.subtitle_data || []);

        // Initialize style from backend defaults
        if (data.default_style) {
          setSubtitleStyle(styleFromBackend(data.default_style));
        }

        // Initialize trim to full duration
        setTrimStart(0);
        setTrimEnd(data.duration || 0);
        setDuration(data.duration || 0);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load editor data');
      } finally {
        setLoading(false);
      }
    }

    if (clipId) {
      loadData();
    }
  }, [clipId]);

  // Synchronize videoElementRef with VideoPreview's video element
  useEffect(() => {
    const syncVideoElement = () => {
      const element = videoPreviewRef.current?.getVideoElement();
      if (element && element !== videoElementRef.current) {
        videoElementRef.current = element;
      }
    };

    // Initial sync
    syncVideoElement();

    // Re-sync periodically to catch when video loads
    const interval = setInterval(syncVideoElement, 100);

    // Stop syncing after 5 seconds (video should be loaded by then)
    const timeout = setTimeout(() => clearInterval(interval), 5000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [editorData]);

  // Track changes
  useEffect(() => {
    if (editorData) {
      setHasChanges(true);
    }
  }, [subtitles, subtitleStyle]);

  // Handle subtitle changes
  const handleSubtitlesChange = useCallback((newSubtitles: SubtitleEntry[]) => {
    setSubtitles(newSubtitles);
    setHasChanges(true);
  }, []);

  // Handle layer visibility toggle
  const handleToggleVisibility = useCallback((layerId: string) => {
    setLayers((prev) =>
      prev.map((layer) =>
        layer.id === layerId ? { ...layer, visible: !layer.visible } : layer
      )
    );
  }, []);

  // Handle layer lock toggle
  const handleToggleLock = useCallback((layerId: string) => {
    setLayers((prev) =>
      prev.map((layer) =>
        layer.id === layerId ? { ...layer, locked: !layer.locked } : layer
      )
    );
  }, []);

  // Handle layer settings
  const handleLayerSettings = useCallback((layerId: string) => {
    if (layerId === 'subtitle') {
      setShowStylePanel(!showStylePanel);
    }
  }, [showStylePanel]);

  // Handle seek
  const handleSeek = useCallback((time: number) => {
    videoPreviewRef.current?.seek(time);
    setCurrentTime(time);
  }, []);

  // Handle trim change
  const handleTrimChange = useCallback((start: number, end: number) => {
    setTrimStart(start);
    setTrimEnd(end);
  }, []);

  // Save subtitles
  const handleSave = async () => {
    if (!editorData) return;

    try {
      setSaving(true);
      await updateSubtitles(clipId, subtitles, subtitleStyle);
      setHasChanges(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  // Export clip
  const handleExport = async (includeSubtitles: boolean, format: string) => {
    if (!editorData) return;

    try {
      setIsExporting(true);

      // Save first if there are changes
      if (hasChanges) {
        await updateSubtitles(clipId, subtitles, subtitleStyle);
      }

      const result = await exportClip(clipId, {
        includeSubtitles,
        subtitleStyle: includeSubtitles ? subtitleStyle : undefined,
        formatId: format,
      });

      // Download the file
      const downloadUrl = getExportDownloadUrl(result);
      window.open(downloadUrl, '_blank');

      setShowExportModal(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export');
    } finally {
      setIsExporting(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-gray-400">Carregando editor...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center max-w-md">
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-dark-700 hover:bg-dark-600 rounded-lg transition-colors"
          >
            Voltar
          </button>
        </div>
      </div>
    );
  }

  if (!editorData) {
    return null;
  }

  const videoUrl = getEditorVideoUrl(editorData);

  return (
    <div className="min-h-screen bg-dark-900 text-white">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-dark-800 border-b border-dark-700">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="font-semibold">ClipGenius Editor</h1>
              <p className="text-sm text-gray-400">{editorData.title || `Clip ${clipId}`}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Undo/Redo */}
            <div className="flex items-center gap-1 mr-2">
              <button
                onClick={undo}
                disabled={historyIndex <= 0}
                className="p-2 hover:bg-dark-700 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                title="Desfazer (Ctrl+Z)"
              >
                <Undo2 className="w-4 h-4" />
              </button>
              <button
                onClick={redo}
                disabled={historyIndex >= history.length - 1}
                className="p-2 hover:bg-dark-700 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                title="Refazer (Ctrl+Shift+Z)"
              >
                <Redo2 className="w-4 h-4" />
              </button>
            </div>

            {/* Save Indicator */}
            {saveSuccess && (
              <span className="flex items-center gap-1 text-green-500 text-sm">
                <Check className="w-4 h-4" />
                Salvo
              </span>
            )}

            {/* Save Button */}
            <button
              onClick={handleSave}
              disabled={saving || !hasChanges}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                hasChanges
                  ? 'bg-dark-700 hover:bg-dark-600'
                  : 'bg-dark-800 text-gray-500 cursor-not-allowed'
              }`}
            >
              {saving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Salvar
            </button>

            {/* Export Button */}
            <button
              onClick={() => setShowExportModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/80 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Exportar
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-65px)]">
        {/* Video Preview + Timeline Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Video Preview - centralizado */}
          <div className="flex-1 min-h-0 flex items-center justify-center p-4 overflow-hidden">
            <div className="h-full max-h-[60vh] aspect-[9/16]">
              <VideoPreview
                ref={videoPreviewRef}
                videoUrl={videoUrl}
                subtitles={subtitles}
                subtitleStyle={subtitleStyle}
                layers={layers}
                onTimeUpdate={setCurrentTime}
                onDurationChange={setDuration}
              />
            </div>
          </div>

          {/* Timeline - parte inferior */}
          <div className="flex-shrink-0 border-t border-dark-700">
            <MultiTrackTimeline
              videoRef={videoElementRef}
              duration={duration}
              currentTime={currentTime}
              trimStart={trimStart}
              trimEnd={trimEnd}
              subtitles={subtitles}
              onTrimChange={handleTrimChange}
              onSeek={handleSeek}
              onSubtitlesChange={handleSubtitlesChange}
            />
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-80 bg-dark-850 border-l border-dark-700 p-4 space-y-4 overflow-y-auto">
          {/* Layer Panel */}
          <LayerPanel
            layers={layers}
            onToggleVisibility={handleToggleVisibility}
            onToggleLock={handleToggleLock}
            onLayerSettings={handleLayerSettings}
          />

          {/* Panel Tabs */}
          <div className="flex gap-2">
            <button
              onClick={() => {
                setShowStylePanel(true);
                setShowBrandKitPanel(false);
              }}
              className={`flex-1 py-2 text-sm rounded-lg transition-colors ${
                showStylePanel
                  ? 'bg-primary text-black'
                  : 'bg-dark-700 hover:bg-dark-600'
              }`}
            >
              🎨 Estilo
            </button>
            <button
              onClick={() => {
                setShowBrandKitPanel(true);
                setShowStylePanel(false);
              }}
              className={`flex-1 py-2 text-sm rounded-lg transition-colors ${
                showBrandKitPanel
                  ? 'bg-primary text-black'
                  : 'bg-dark-700 hover:bg-dark-600'
              }`}
            >
              <Palette className="w-4 h-4 inline mr-1" />
              Brand Kit
            </button>
          </div>

          {/* Subtitle Style Panel */}
          {showStylePanel && (
            <SubtitleStylePanel
              style={subtitleStyle}
              onStyleChange={(newStyle) => {
                saveToHistory();
                setSubtitleStyle(newStyle);
                setHasChanges(true);
              }}
            />
          )}

          {/* Brand Kit Panel */}
          {showBrandKitPanel && (
            <BrandKitPanel
              currentStyle={subtitleStyle}
              onApplyStyle={(style) => {
                saveToHistory();
                setSubtitleStyle(style);
                setHasChanges(true);
              }}
            />
          )}

          {/* Show prompt if neither panel is shown */}
          {!showStylePanel && !showBrandKitPanel && (
            <div className="text-center py-8 text-gray-500 text-sm">
              Selecione uma opcao acima para configurar o estilo
            </div>
          )}
        </div>
      </div>

      {/* Export Modal */}
      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        onExport={handleExport}
        isExporting={isExporting}
      />
    </div>
  );
}
