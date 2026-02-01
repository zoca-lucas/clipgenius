'use client';

import { useState } from 'react';
import {
  Smartphone,
  Square,
  Monitor,
  RectangleVertical,
  Download,
  Loader2,
  Check,
  AlertCircle
} from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const BASE_URL = API_BASE_URL.replace('/api', '');

interface OutputFormat {
  id: string;
  name: string;
  aspect_ratio: string;
  resolution: [number, number];
  platforms: string[];
  description: string;
}

interface FormatSelectorProps {
  clipId: number;
  onExport?: (formatId: string) => void;
}

const FORMAT_ICONS: Record<string, typeof Smartphone> = {
  vertical: Smartphone,
  square: Square,
  landscape: Monitor,
  portrait: RectangleVertical,
};

const FORMATS: OutputFormat[] = [
  {
    id: 'vertical',
    name: 'Vertical (9:16)',
    aspect_ratio: '9:16',
    resolution: [1080, 1920],
    platforms: ['TikTok', 'Reels', 'Shorts'],
    description: 'Formato vertical para shorts'
  },
  {
    id: 'square',
    name: 'Quadrado (1:1)',
    aspect_ratio: '1:1',
    resolution: [1080, 1080],
    platforms: ['Instagram', 'Facebook'],
    description: 'Formato quadrado para feed'
  },
  {
    id: 'landscape',
    name: 'Horizontal (16:9)',
    aspect_ratio: '16:9',
    resolution: [1920, 1080],
    platforms: ['YouTube', 'LinkedIn'],
    description: 'Formato horizontal tradicional'
  },
  {
    id: 'portrait',
    name: 'Retrato (4:5)',
    aspect_ratio: '4:5',
    resolution: [1080, 1350],
    platforms: ['Instagram Post'],
    description: 'Formato retrato para posts'
  },
];

export default function FormatSelector({ clipId, onExport }: FormatSelectorProps) {
  const [selectedFormat, setSelectedFormat] = useState<string>('vertical');
  const [exporting, setExporting] = useState<string | null>(null);
  const [exported, setExported] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (formatId: string) => {
    setExporting(formatId);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/clips/${clipId}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ format_id: formatId }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Export failed');
      }

      const data = await response.json();
      setExported([...exported, formatId]);

      if (onExport) {
        onExport(formatId);
      }

      // Download the exported file
      if (data.video_path) {
        const filename = data.video_path.split('/').pop();
        window.open(`${BASE_URL}/clips/${filename}`, '_blank');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao exportar';
      setError(message);
      console.error('Export error:', err);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="bg-dark-700 rounded-xl p-4 border border-dark-600">
      <h3 className="text-sm font-semibold text-white mb-3">Exportar em outro formato</h3>

      <div className="grid grid-cols-2 gap-2">
        {FORMATS.map((format) => {
          const Icon = FORMAT_ICONS[format.id] || Square;
          const isExporting = exporting === format.id;
          const isExported = exported.includes(format.id);

          return (
            <button
              key={format.id}
              onClick={() => handleExport(format.id)}
              disabled={isExporting}
              className={`
                flex items-center gap-2 p-3 rounded-lg border transition-all text-left
                ${selectedFormat === format.id
                  ? 'border-primary bg-primary/10'
                  : 'border-dark-500 hover:border-dark-400 bg-dark-600'
                }
                ${isExporting ? 'opacity-50 cursor-wait' : ''}
              `}
            >
              <div className={`p-2 rounded-lg ${
                isExported ? 'bg-green-500/20 text-green-400' : 'bg-dark-500 text-gray-400'
              }`}>
                {isExporting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : isExported ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-white truncate">{format.name}</p>
                <p className="text-[10px] text-gray-500 truncate">
                  {format.platforms.slice(0, 2).join(', ')}
                </p>
              </div>
              <Download className="w-3 h-3 text-gray-500" />
            </button>
          );
        })}
      </div>

      {error && (
        <div className="mt-3 flex items-center gap-2 text-xs text-red-400 bg-red-500/10 p-2 rounded-lg">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <p className="text-[10px] text-gray-600 mt-3 text-center">
        Clique para exportar e baixar
      </p>
    </div>
  );
}
