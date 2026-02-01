'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Scissors,
  Video,
  Music,
  MessageSquare,
  Type,
  ZoomIn,
  ZoomOut,
  Eye,
  EyeOff,
  Lock,
  Unlock,
} from 'lucide-react';
import { SubtitleEntry } from '@/lib/editorApi';

interface MultiTrackTimelineProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  duration: number;
  currentTime: number;
  trimStart: number;
  trimEnd: number;
  subtitles: SubtitleEntry[];
  onTrimChange: (start: number, end: number) => void;
  onSeek: (time: number) => void;
  onSubtitlesChange?: (subtitles: SubtitleEntry[]) => void;
}

interface TrackConfig {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  visible: boolean;
  locked: boolean;
}

export default function MultiTrackTimeline({
  videoRef,
  duration,
  currentTime,
  trimStart,
  trimEnd,
  subtitles,
  onTrimChange,
  onSeek,
  onSubtitlesChange,
}: MultiTrackTimelineProps) {
  const timelineRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState<'start' | 'end' | 'playhead' | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [scrollLeft, setScrollLeft] = useState(0);
  const [draggedSubtitle, setDraggedSubtitle] = useState<{ id: string; offset: number } | null>(null);
  const [resizingSubtitle, setResizingSubtitle] = useState<{ id: string; edge: 'start' | 'end' } | null>(null);

  // Track configuration
  const [tracks, setTracks] = useState<TrackConfig[]>([
    { id: 'video', name: 'Video', icon: <Video className="w-4 h-4" />, color: '#3B82F6', visible: true, locked: false },
    { id: 'audio', name: 'Audio', icon: <Music className="w-4 h-4" />, color: '#10B981', visible: true, locked: false },
    { id: 'subtitle', name: 'Legendas', icon: <MessageSquare className="w-4 h-4" />, color: '#F59E0B', visible: true, locked: false },
    { id: 'text', name: 'Textos', icon: <Type className="w-4 h-4" />, color: '#EC4899', visible: true, locked: false },
  ]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 10);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`;
  };

  const getPositionFromTime = (time: number): number => {
    return (time / duration) * 100 * zoom;
  };

  const getTimeFromPosition = useCallback((clientX: number): number => {
    if (!timelineRef.current) return 0;
    const rect = timelineRef.current.getBoundingClientRect();
    const scrollOffset = timelineRef.current.scrollLeft;
    const position = (clientX - rect.left + scrollOffset) / (rect.width * zoom);
    return Math.max(0, Math.min(duration, position * duration));
  }, [duration, zoom]);

  const handleMouseDown = (e: React.MouseEvent, type: 'start' | 'end' | 'playhead') => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(type);
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      const time = getTimeFromPosition(e.clientX);

      if (isDragging === 'start') {
        const newStart = Math.min(time, trimEnd - 0.5);
        onTrimChange(Math.max(0, newStart), trimEnd);
      } else if (isDragging === 'end') {
        const newEnd = Math.max(time, trimStart + 0.5);
        onTrimChange(trimStart, Math.min(duration, newEnd));
      } else if (isDragging === 'playhead') {
        onSeek(time);
      }
    }

    if (draggedSubtitle && onSubtitlesChange) {
      const time = getTimeFromPosition(e.clientX);
      const subtitle = subtitles.find((s) => s.id === draggedSubtitle.id);
      if (subtitle) {
        const subtitleDuration = subtitle.end - subtitle.start;
        const newStart = Math.max(0, Math.min(duration - subtitleDuration, time - draggedSubtitle.offset));
        const newEnd = newStart + subtitleDuration;

        onSubtitlesChange(
          subtitles.map((s) =>
            s.id === draggedSubtitle.id ? { ...s, start: newStart, end: newEnd } : s
          )
        );
      }
    }

    if (resizingSubtitle && onSubtitlesChange) {
      const time = getTimeFromPosition(e.clientX);
      const subtitle = subtitles.find((s) => s.id === resizingSubtitle.id);
      if (subtitle) {
        if (resizingSubtitle.edge === 'start') {
          const newStart = Math.max(0, Math.min(subtitle.end - 0.1, time));
          onSubtitlesChange(
            subtitles.map((s) =>
              s.id === resizingSubtitle.id ? { ...s, start: newStart } : s
            )
          );
        } else {
          const newEnd = Math.min(duration, Math.max(subtitle.start + 0.1, time));
          onSubtitlesChange(
            subtitles.map((s) =>
              s.id === resizingSubtitle.id ? { ...s, end: newEnd } : s
            )
          );
        }
      }
    }
  }, [isDragging, draggedSubtitle, resizingSubtitle, trimStart, trimEnd, duration, subtitles, onTrimChange, onSeek, onSubtitlesChange, getTimeFromPosition]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(null);
    setDraggedSubtitle(null);
    setResizingSubtitle(null);
  }, []);

  useEffect(() => {
    if (isDragging || draggedSubtitle || resizingSubtitle) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, draggedSubtitle, resizingSubtitle, handleMouseMove, handleMouseUp]);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const skipBack = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, currentTime - 5);
    }
  };

  const skipForward = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.min(duration, currentTime + 5);
    }
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);

    return () => {
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
    };
  }, [videoRef]);

  const toggleTrackVisibility = (trackId: string) => {
    setTracks((prev) =>
      prev.map((t) => (t.id === trackId ? { ...t, visible: !t.visible } : t))
    );
  };

  const toggleTrackLock = (trackId: string) => {
    setTracks((prev) =>
      prev.map((t) => (t.id === trackId ? { ...t, locked: !t.locked } : t))
    );
  };

  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.5, 4));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.5, 0.5));

  // Generate time markers
  const timeMarkers = useMemo(() => {
    const markers = [];
    const interval = duration > 60 ? 10 : duration > 30 ? 5 : 2;
    for (let t = 0; t <= duration; t += interval) {
      markers.push(t);
    }
    return markers;
  }, [duration]);

  const handleSubtitleDragStart = (e: React.MouseEvent, subtitleId: string) => {
    e.stopPropagation();
    const track = tracks.find((t) => t.id === 'subtitle');
    if (track?.locked) return;

    const subtitle = subtitles.find((s) => s.id === subtitleId);
    if (subtitle) {
      const time = getTimeFromPosition(e.clientX);
      setDraggedSubtitle({ id: subtitleId, offset: time - subtitle.start });
    }
  };

  const handleSubtitleResizeStart = (e: React.MouseEvent, subtitleId: string, edge: 'start' | 'end') => {
    e.stopPropagation();
    const track = tracks.find((t) => t.id === 'subtitle');
    if (track?.locked) return;
    setResizingSubtitle({ id: subtitleId, edge });
  };

  return (
    <div className="bg-dark-800 rounded-lg overflow-hidden">
      {/* Controls Bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-dark-700">
        <div className="flex items-center gap-2">
          <button
            onClick={skipBack}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
            title="Voltar 5s"
          >
            <SkipBack className="w-5 h-5" />
          </button>

          <button
            onClick={togglePlay}
            className="p-3 bg-primary hover:bg-primary/80 rounded-full transition-colors"
          >
            {isPlaying ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5 ml-0.5" />
            )}
          </button>

          <button
            onClick={skipForward}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
            title="Avancar 5s"
          >
            <SkipForward className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-400 font-mono">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
            title="Diminuir zoom"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs text-gray-400 w-12 text-center">{Math.round(zoom * 100)}%</span>
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
            title="Aumentar zoom"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Timeline Container */}
      <div className="flex">
        {/* Track Labels */}
        <div className="w-32 flex-shrink-0 border-r border-dark-700">
          {/* Time ruler label */}
          <div className="h-8 border-b border-dark-700 flex items-center justify-center">
            <span className="text-xs text-gray-500">Tempo</span>
          </div>

          {/* Track labels */}
          {tracks.map((track) => (
            <div
              key={track.id}
              className="h-10 border-b border-dark-700 flex items-center gap-2 px-2"
            >
              <span style={{ color: track.color }}>{track.icon}</span>
              <span className="text-xs text-gray-300 flex-1 truncate">{track.name}</span>
              <button
                onClick={() => toggleTrackVisibility(track.id)}
                className="p-1 hover:bg-dark-700 rounded transition-colors"
              >
                {track.visible ? (
                  <Eye className="w-3 h-3 text-gray-400" />
                ) : (
                  <EyeOff className="w-3 h-3 text-gray-500" />
                )}
              </button>
              <button
                onClick={() => toggleTrackLock(track.id)}
                className="p-1 hover:bg-dark-700 rounded transition-colors"
              >
                {track.locked ? (
                  <Lock className="w-3 h-3 text-yellow-500" />
                ) : (
                  <Unlock className="w-3 h-3 text-gray-400" />
                )}
              </button>
            </div>
          ))}
        </div>

        {/* Scrollable Timeline Area */}
        <div
          ref={timelineRef}
          className="flex-1 overflow-x-auto"
          onScroll={(e) => setScrollLeft(e.currentTarget.scrollLeft)}
          onClick={(e) => {
            if (!isDragging && !draggedSubtitle && !resizingSubtitle) {
              const time = getTimeFromPosition(e.clientX);
              onSeek(time);
            }
          }}
        >
          <div
            className="relative"
            style={{ width: `${100 * zoom}%`, minWidth: '100%' }}
          >
            {/* Time Ruler */}
            <div className="h-8 border-b border-dark-700 relative">
              {timeMarkers.map((time) => (
                <div
                  key={time}
                  className="absolute top-0 bottom-0 flex flex-col items-center"
                  style={{ left: `${getPositionFromTime(time)}%` }}
                >
                  <div className="h-2 w-px bg-dark-500" />
                  <span className="text-[10px] text-gray-500 mt-0.5">
                    {formatTime(time)}
                  </span>
                </div>
              ))}
            </div>

            {/* Tracks */}
            {tracks.map((track) => (
              <div
                key={track.id}
                className="h-10 border-b border-dark-700 relative"
                style={{ opacity: track.visible ? 1 : 0.3 }}
              >
                {/* Track Background */}
                <div className="absolute inset-0 bg-dark-900/50" />

                {/* Trim Region Highlight */}
                <div
                  className="absolute top-0 bottom-0 opacity-20"
                  style={{
                    left: `${getPositionFromTime(trimStart)}%`,
                    width: `${getPositionFromTime(trimEnd) - getPositionFromTime(trimStart)}%`,
                    backgroundColor: track.color,
                  }}
                />

                {/* Video Track - Full clip representation */}
                {track.id === 'video' && (
                  <div
                    className="absolute top-2 bottom-2 rounded"
                    style={{
                      left: `${getPositionFromTime(0)}%`,
                      width: `${getPositionFromTime(duration)}%`,
                      backgroundColor: track.color,
                      opacity: 0.6,
                    }}
                  >
                    <div className="h-full flex items-center justify-center text-xs text-white/80 truncate px-2">
                      Video Principal
                    </div>
                  </div>
                )}

                {/* Audio Track - Waveform placeholder */}
                {track.id === 'audio' && (
                  <div
                    className="absolute top-2 bottom-2 rounded overflow-hidden"
                    style={{
                      left: `${getPositionFromTime(0)}%`,
                      width: `${getPositionFromTime(duration)}%`,
                      backgroundColor: track.color,
                      opacity: 0.4,
                    }}
                  >
                    {/* Fake waveform */}
                    <div className="h-full flex items-center justify-center gap-0.5 px-1">
                      {Array.from({ length: Math.min(50, Math.floor(duration * 2)) }).map((_, i) => (
                        <div
                          key={i}
                          className="w-0.5 bg-white/60 rounded-full"
                          style={{
                            height: `${20 + Math.random() * 60}%`,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Subtitle Track - Individual subtitles */}
                {track.id === 'subtitle' &&
                  subtitles.map((subtitle) => (
                    <div
                      key={subtitle.id}
                      className={`absolute top-2 bottom-2 rounded cursor-move group ${
                        track.locked ? 'cursor-not-allowed' : ''
                      }`}
                      style={{
                        left: `${getPositionFromTime(subtitle.start)}%`,
                        width: `${getPositionFromTime(subtitle.end) - getPositionFromTime(subtitle.start)}%`,
                        backgroundColor: track.color,
                        minWidth: '20px',
                      }}
                      onMouseDown={(e) => handleSubtitleDragStart(e, subtitle.id)}
                    >
                      {/* Resize handles */}
                      {!track.locked && (
                        <>
                          <div
                            className="absolute left-0 top-0 bottom-0 w-2 cursor-ew-resize bg-white/0 hover:bg-white/30 rounded-l"
                            onMouseDown={(e) => handleSubtitleResizeStart(e, subtitle.id, 'start')}
                          />
                          <div
                            className="absolute right-0 top-0 bottom-0 w-2 cursor-ew-resize bg-white/0 hover:bg-white/30 rounded-r"
                            onMouseDown={(e) => handleSubtitleResizeStart(e, subtitle.id, 'end')}
                          />
                        </>
                      )}
                      <div className="h-full flex items-center justify-center text-[10px] text-white truncate px-2">
                        {subtitle.text.substring(0, 20)}
                        {subtitle.text.length > 20 ? '...' : ''}
                      </div>
                    </div>
                  ))}

                {/* Text Track - Empty for now */}
                {track.id === 'text' && (
                  <div className="h-full flex items-center justify-center text-xs text-gray-600">
                    Arraste textos aqui
                  </div>
                )}
              </div>
            ))}

            {/* Trim Handles */}
            <div
              className="absolute top-8 bottom-0 w-1 bg-primary cursor-ew-resize z-10 hover:w-2 transition-all"
              style={{ left: `calc(${getPositionFromTime(trimStart)}% - 2px)` }}
              onMouseDown={(e) => handleMouseDown(e, 'start')}
            >
              <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-primary rounded-sm" />
            </div>

            <div
              className="absolute top-8 bottom-0 w-1 bg-primary cursor-ew-resize z-10 hover:w-2 transition-all"
              style={{ left: `calc(${getPositionFromTime(trimEnd)}% - 2px)` }}
              onMouseDown={(e) => handleMouseDown(e, 'end')}
            >
              <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-primary rounded-sm" />
            </div>

            {/* Playhead */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-white z-20 cursor-ew-resize"
              style={{ left: `${getPositionFromTime(currentTime)}%` }}
              onMouseDown={(e) => handleMouseDown(e, 'playhead')}
            >
              <div className="absolute -top-0 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[8px] border-l-transparent border-r-transparent border-t-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Info Bar */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-dark-700 text-sm">
        <div className="flex items-center gap-2">
          <Scissors className="w-4 h-4 text-primary" />
          <span className="text-gray-400">Corte:</span>
          <span className="text-white font-medium">
            {formatTime(trimStart)} - {formatTime(trimEnd)}
          </span>
          <span className="text-gray-500">
            ({formatTime(trimEnd - trimStart)})
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>{subtitles.length} legendas</span>
        </div>
      </div>
    </div>
  );
}
