'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Play, Pause, SkipBack, SkipForward, Scissors } from 'lucide-react';

interface VideoTimelineProps {
  videoRef: React.RefObject<HTMLVideoElement>;
  duration: number;
  currentTime: number;
  trimStart: number;
  trimEnd: number;
  onTrimChange: (start: number, end: number) => void;
  onSeek: (time: number) => void;
}

export default function VideoTimeline({
  videoRef,
  duration,
  currentTime,
  trimStart,
  trimEnd,
  onTrimChange,
  onSeek,
}: VideoTimelineProps) {
  const timelineRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState<'start' | 'end' | 'playhead' | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 10);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`;
  };

  const getPositionFromTime = (time: number): number => {
    return (time / duration) * 100;
  };

  const getTimeFromPosition = (clientX: number): number => {
    if (!timelineRef.current) return 0;
    const rect = timelineRef.current.getBoundingClientRect();
    const position = (clientX - rect.left) / rect.width;
    return Math.max(0, Math.min(duration, position * duration));
  };

  const handleMouseDown = (e: React.MouseEvent, type: 'start' | 'end' | 'playhead') => {
    e.preventDefault();
    setIsDragging(type);
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;

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
  }, [isDragging, trimStart, trimEnd, duration, onTrimChange, onSeek]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(null);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

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

  const goToStart = () => {
    onSeek(trimStart);
  };

  const goToEnd = () => {
    onSeek(trimEnd);
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

  return (
    <div className="bg-dark-800 rounded-lg p-4 space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
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
            title="Avançar 5s"
          >
            <SkipForward className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-400">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={goToStart}
            className="px-3 py-1.5 bg-dark-700 hover:bg-dark-600 rounded text-sm transition-colors"
            title="Ir para início do corte"
          >
            Início
          </button>
          <button
            onClick={goToEnd}
            className="px-3 py-1.5 bg-dark-700 hover:bg-dark-600 rounded text-sm transition-colors"
            title="Ir para fim do corte"
          >
            Fim
          </button>
        </div>
      </div>

      {/* Timeline */}
      <div
        ref={timelineRef}
        className="relative h-16 bg-dark-900 rounded-lg cursor-pointer overflow-hidden"
        onClick={(e) => {
          if (!isDragging) {
            const time = getTimeFromPosition(e.clientX);
            onSeek(time);
          }
        }}
      >
        {/* Trim region background */}
        <div
          className="absolute top-0 bottom-0 bg-primary/20"
          style={{
            left: `${getPositionFromTime(trimStart)}%`,
            width: `${getPositionFromTime(trimEnd) - getPositionFromTime(trimStart)}%`,
          }}
        />

        {/* Excluded regions (darker) */}
        <div
          className="absolute top-0 bottom-0 bg-black/50"
          style={{
            left: 0,
            width: `${getPositionFromTime(trimStart)}%`,
          }}
        />
        <div
          className="absolute top-0 bottom-0 bg-black/50"
          style={{
            left: `${getPositionFromTime(trimEnd)}%`,
            right: 0,
          }}
        />

        {/* Trim start handle */}
        <div
          className="absolute top-0 bottom-0 w-3 bg-primary cursor-ew-resize flex items-center justify-center z-10 hover:bg-primary/80"
          style={{ left: `calc(${getPositionFromTime(trimStart)}% - 6px)` }}
          onMouseDown={(e) => handleMouseDown(e, 'start')}
        >
          <div className="w-0.5 h-8 bg-white/50 rounded" />
        </div>

        {/* Trim end handle */}
        <div
          className="absolute top-0 bottom-0 w-3 bg-primary cursor-ew-resize flex items-center justify-center z-10 hover:bg-primary/80"
          style={{ left: `calc(${getPositionFromTime(trimEnd)}% - 6px)` }}
          onMouseDown={(e) => handleMouseDown(e, 'end')}
        >
          <div className="w-0.5 h-8 bg-white/50 rounded" />
        </div>

        {/* Playhead */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white z-20 cursor-ew-resize"
          style={{ left: `${getPositionFromTime(currentTime)}%` }}
          onMouseDown={(e) => handleMouseDown(e, 'playhead')}
        >
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rounded-full" />
        </div>

        {/* Time markers */}
        <div className="absolute bottom-1 left-0 right-0 flex justify-between px-2 text-xs text-gray-500">
          <span>0:00</span>
          <span>{formatTime(duration / 4)}</span>
          <span>{formatTime(duration / 2)}</span>
          <span>{formatTime((duration * 3) / 4)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Trim info */}
      <div className="flex items-center justify-between text-sm">
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
      </div>
    </div>
  );
}
