'use client';

import { useState } from 'react';
import { Plus, Trash2, GripVertical, Type } from 'lucide-react';

export interface SubtitleEntry {
  id: string;
  start: number;
  end: number;
  text: string;
}

interface SubtitleEditorProps {
  subtitles: SubtitleEntry[];
  currentTime: number;
  onSubtitlesChange: (subtitles: SubtitleEntry[]) => void;
  onSeek: (time: number) => void;
}

export default function SubtitleEditor({
  subtitles,
  currentTime,
  onSubtitlesChange,
  onSeek,
}: SubtitleEditorProps) {
  const [editingId, setEditingId] = useState<string | null>(null);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
  };

  const parseTime = (timeStr: string): number => {
    const match = timeStr.match(/^(\d+):(\d{2})\.?(\d{0,2})$/);
    if (!match) return 0;
    const mins = parseInt(match[1], 10);
    const secs = parseInt(match[2], 10);
    const ms = match[3] ? parseInt(match[3].padEnd(2, '0'), 10) : 0;
    return mins * 60 + secs + ms / 100;
  };

  const addSubtitle = () => {
    const newSubtitle: SubtitleEntry = {
      id: `sub_${Date.now()}`,
      start: currentTime,
      end: Math.min(currentTime + 3, subtitles.length > 0 ? Math.max(...subtitles.map(s => s.end)) + 5 : currentTime + 3),
      text: 'Nova legenda',
    };

    const updated = [...subtitles, newSubtitle].sort((a, b) => a.start - b.start);
    onSubtitlesChange(updated);
    setEditingId(newSubtitle.id);
  };

  const updateSubtitle = (id: string, updates: Partial<SubtitleEntry>) => {
    const updated = subtitles.map((sub) =>
      sub.id === id ? { ...sub, ...updates } : sub
    );
    onSubtitlesChange(updated.sort((a, b) => a.start - b.start));
  };

  const deleteSubtitle = (id: string) => {
    onSubtitlesChange(subtitles.filter((sub) => sub.id !== id));
  };

  const isActive = (sub: SubtitleEntry): boolean => {
    return currentTime >= sub.start && currentTime <= sub.end;
  };

  return (
    <div className="bg-dark-800 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium flex items-center gap-2">
          <Type className="w-5 h-5 text-primary" />
          Legendas
        </h3>
        <button
          onClick={addSubtitle}
          className="flex items-center gap-1 px-3 py-1.5 bg-primary hover:bg-primary/80 rounded text-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Adicionar
        </button>
      </div>

      {subtitles.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Type className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Nenhuma legenda</p>
          <p className="text-sm">Clique em "Adicionar" para criar uma legenda</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {subtitles.map((sub) => (
            <div
              key={sub.id}
              className={`p-3 rounded-lg border transition-colors cursor-pointer ${
                isActive(sub)
                  ? 'bg-primary/20 border-primary'
                  : 'bg-dark-700 border-dark-600 hover:border-dark-500'
              }`}
              onClick={() => onSeek(sub.start)}
            >
              <div className="flex items-start gap-2">
                <GripVertical className="w-4 h-4 text-gray-500 mt-1 cursor-move" />

                <div className="flex-1 space-y-2">
                  {/* Time inputs */}
                  <div className="flex items-center gap-2 text-sm">
                    <input
                      type="text"
                      value={formatTime(sub.start)}
                      onChange={(e) => {
                        const time = parseTime(e.target.value);
                        if (!isNaN(time)) {
                          updateSubtitle(sub.id, { start: time });
                        }
                      }}
                      className="w-20 px-2 py-1 bg-dark-900 rounded text-center focus:ring-1 focus:ring-primary outline-none"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <span className="text-gray-500">-</span>
                    <input
                      type="text"
                      value={formatTime(sub.end)}
                      onChange={(e) => {
                        const time = parseTime(e.target.value);
                        if (!isNaN(time)) {
                          updateSubtitle(sub.id, { end: time });
                        }
                      }}
                      className="w-20 px-2 py-1 bg-dark-900 rounded text-center focus:ring-1 focus:ring-primary outline-none"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <span className="text-gray-500 text-xs">
                      ({(sub.end - sub.start).toFixed(1)}s)
                    </span>
                  </div>

                  {/* Text input */}
                  {editingId === sub.id ? (
                    <textarea
                      value={sub.text}
                      onChange={(e) => updateSubtitle(sub.id, { text: e.target.value })}
                      onBlur={() => setEditingId(null)}
                      onKeyDown={(e) => {
                        if (e.key === 'Escape') setEditingId(null);
                      }}
                      autoFocus
                      className="w-full px-2 py-1 bg-dark-900 rounded resize-none focus:ring-1 focus:ring-primary outline-none"
                      rows={2}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <p
                      className="text-sm cursor-text hover:bg-dark-900/50 px-2 py-1 rounded"
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingId(sub.id);
                      }}
                    >
                      {sub.text}
                    </p>
                  )}
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSubtitle(sub.id);
                  }}
                  className="p-1 hover:bg-red-500/20 hover:text-red-500 rounded transition-colors"
                  title="Excluir legenda"
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
