'use client';

import { useState } from 'react';
import { Play, Download, Trash2, Clock, Star } from 'lucide-react';
import { Clip, formatDuration, getScoreColor, getClipDownloadUrl, getClipVideoUrl } from '@/lib/api';

interface ClipCardProps {
  clip: Clip;
  onDelete?: (clipId: number) => void;
}

export default function ClipCard({ clip, onDelete }: ClipCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [showVideo, setShowVideo] = useState(false);

  const handleDownload = () => {
    const url = getClipDownloadUrl(clip.id, true);
    window.open(url, '_blank');
  };

  const handleDelete = () => {
    if (confirm('Tem certeza que deseja deletar este corte?')) {
      onDelete?.(clip.id);
    }
  };

  const videoUrl = getClipVideoUrl(clip, true);

  return (
    <div className="bg-dark-700 rounded-xl overflow-hidden border border-dark-600 hover:border-primary/50 transition-all">
      {/* Video Preview */}
      <div className="relative aspect-[9/16] bg-dark-800">
        {showVideo && videoUrl ? (
          <video
            src={videoUrl}
            className="w-full h-full object-cover"
            controls
            autoPlay
            onEnded={() => setIsPlaying(false)}
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center cursor-pointer group"
            onClick={() => setShowVideo(true)}
          >
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-dark-900/80" />
            <button className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/30 transition-all">
              <Play className="w-8 h-8 text-white ml-1" />
            </button>
          </div>
        )}

        {/* Score Badge */}
        <div className={`absolute top-3 right-3 px-2 py-1 rounded-lg text-sm font-bold text-white ${getScoreColor(clip.viral_score)}`}>
          {clip.viral_score?.toFixed(1)}/10
        </div>
      </div>

      {/* Info */}
      <div className="p-4">
        <h3 className="font-semibold text-white text-sm line-clamp-2 mb-2">
          {clip.title || 'Sem título'}
        </h3>

        <div className="flex items-center gap-4 text-xs text-gray-400 mb-3">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatDuration(clip.duration)}
          </span>
          <span className="flex items-center gap-1">
            <Star className="w-3 h-3" />
            Nota: {clip.viral_score?.toFixed(1) || '?'}
          </span>
        </div>

        {clip.score_justification && (
          <p className="text-xs text-gray-500 line-clamp-2 mb-3">
            {clip.score_justification}
          </p>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={handleDownload}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary hover:bg-primary/80 text-white text-sm rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Baixar
          </button>
          <button
            onClick={handleDelete}
            className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
