'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Play, Download, Trash2, Clock, Star, MoreHorizontal, X, Loader2, Edit, Pencil, Check } from 'lucide-react';
import { Clip, formatDuration, getScoreColor, getClipDownloadUrl, getClipVideoUrl, updateClipTitle } from '@/lib/api';
import FormatSelector from './FormatSelector';

interface ClipCardProps {
  clip: Clip;
  onDelete?: (clipId: number) => void;
  onUpdate?: (clip: Clip) => void;
}

export default function ClipCard({ clip, onDelete, onUpdate }: ClipCardProps) {
  const router = useRouter();
  const [showVideo, setShowVideo] = useState(false);
  const [showFormats, setShowFormats] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState(clip.title || '');
  const [isSavingTitle, setIsSavingTitle] = useState(false);
  const titleInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditingTitle && titleInputRef.current) {
      titleInputRef.current.focus();
      titleInputRef.current.select();
    }
  }, [isEditingTitle]);

  const handleSaveTitle = async () => {
    if (editedTitle.trim() === (clip.title || '').trim()) {
      setIsEditingTitle(false);
      return;
    }

    setIsSavingTitle(true);
    try {
      const updatedClip = await updateClipTitle(clip.id, editedTitle.trim());
      onUpdate?.(updatedClip);
      setIsEditingTitle(false);
    } catch (error) {
      console.error('Failed to update title:', error);
      setEditedTitle(clip.title || '');
    } finally {
      setIsSavingTitle(false);
    }
  };

  const handleTitleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveTitle();
    } else if (e.key === 'Escape') {
      setEditedTitle(clip.title || '');
      setIsEditingTitle(false);
    }
  };

  const handleDownload = () => {
    const url = getClipDownloadUrl(clip.id, true);
    window.open(url, '_blank');
  };

  const handleDelete = async () => {
    if (confirm('Tem certeza que deseja deletar este corte?')) {
      setIsDeleting(true);
      try {
        await onDelete?.(clip.id);
      } finally {
        setIsDeleting(false);
      }
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
        {/* Editable Title */}
        <div className="mb-2">
          {isEditingTitle ? (
            <div className="flex items-center gap-2">
              <input
                ref={titleInputRef}
                type="text"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                onKeyDown={handleTitleKeyDown}
                onBlur={handleSaveTitle}
                disabled={isSavingTitle}
                className="flex-1 bg-dark-600 border border-primary rounded px-2 py-1 text-sm text-white outline-none"
                placeholder="Digite o titulo..."
              />
              {isSavingTitle ? (
                <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
              ) : (
                <button
                  onClick={handleSaveTitle}
                  className="p-1 hover:bg-dark-600 rounded transition-colors text-green-400"
                >
                  <Check className="w-4 h-4" />
                </button>
              )}
            </div>
          ) : (
            <div
              className="group flex items-center gap-2 cursor-pointer"
              onClick={() => setIsEditingTitle(true)}
            >
              <h3 className="font-semibold text-white text-sm line-clamp-2 flex-1">
                {clip.title || 'Clique para adicionar titulo'}
              </h3>
              <Pencil className="w-3 h-3 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          )}
        </div>

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
            onClick={() => router.push(`/editor/${clip.id}`)}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-dark-600 hover:bg-dark-500 text-white text-sm rounded-lg transition-colors"
            title="Editar clip"
          >
            <Edit className="w-4 h-4" />
            Editar
          </button>
          <button
            onClick={handleDownload}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary hover:bg-primary/80 text-white text-sm rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Baixar
          </button>
          <button
            onClick={() => setShowFormats(!showFormats)}
            className="px-3 py-2 bg-dark-600 hover:bg-dark-500 text-gray-400 hover:text-white rounded-lg transition-colors"
            title="Mais formatos"
          >
            <MoreHorizontal className="w-4 h-4" />
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className={`px-3 py-2 rounded-lg transition-colors ${
              isDeleting
                ? 'bg-gray-500/20 text-gray-500 cursor-wait'
                : 'bg-red-500/20 hover:bg-red-500/30 text-red-400'
            }`}
          >
            {isDeleting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Format Selector */}
        {showFormats && (
          <div className="mt-3">
            <FormatSelector clipId={clip.id} />
          </div>
        )}
      </div>
    </div>
  );
}
