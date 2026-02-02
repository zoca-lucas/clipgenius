'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import WaveSurfer from 'wavesurfer.js';

interface WaveformProps {
  videoUrl: string;
  currentTime: number;
  duration: number;
  onSeek: (time: number) => void;
  height?: number;
  waveColor?: string;
  progressColor?: string;
  backgroundColor?: string;
}

export default function Waveform({
  videoUrl,
  currentTime,
  duration,
  onSeek,
  height = 50,
  waveColor = '#4B5563',
  progressColor = '#8B5CF6',
  backgroundColor = 'transparent',
}: WaveformProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isUserInteracting = useRef(false);

  // Initialize WaveSurfer
  useEffect(() => {
    if (!containerRef.current || !videoUrl) return;

    setIsLoading(true);
    setError(null);

    const wavesurfer = WaveSurfer.create({
      container: containerRef.current,
      waveColor,
      progressColor,
      height,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      cursorWidth: 1,
      cursorColor: '#FFFFFF',
      normalize: true,
      interact: true,
      hideScrollbar: true,
      backend: 'WebAudio',
    });

    wavesurferRef.current = wavesurfer;

    // Load audio from video URL
    wavesurfer.load(videoUrl);

    wavesurfer.on('ready', () => {
      setIsReady(true);
      setIsLoading(false);
    });

    wavesurfer.on('error', (err) => {
      console.error('Waveform error:', err);
      setError('Erro ao carregar forma de onda');
      setIsLoading(false);
    });

    wavesurfer.on('interaction', () => {
      isUserInteracting.current = true;
    });

    wavesurfer.on('seeking', (progress) => {
      if (isUserInteracting.current && wavesurfer.getDuration()) {
        const seekTime = progress * wavesurfer.getDuration();
        onSeek(seekTime);
      }
    });

    wavesurfer.on('click', () => {
      setTimeout(() => {
        isUserInteracting.current = false;
      }, 100);
    });

    return () => {
      wavesurfer.destroy();
      wavesurferRef.current = null;
    };
  }, [videoUrl, height, waveColor, progressColor]);

  // Sync playback position
  useEffect(() => {
    if (!wavesurferRef.current || !isReady || isUserInteracting.current) return;

    const waveDuration = wavesurferRef.current.getDuration();
    if (waveDuration > 0 && duration > 0) {
      const progress = currentTime / duration;
      wavesurferRef.current.seekTo(Math.min(Math.max(progress, 0), 1));
    }
  }, [currentTime, duration, isReady]);

  if (error) {
    return (
      <div
        className="flex items-center justify-center text-xs text-gray-500"
        style={{ height }}
      >
        {error}
      </div>
    );
  }

  return (
    <div className="relative w-full" style={{ backgroundColor }}>
      {isLoading && (
        <div
          className="absolute inset-0 flex items-center justify-center bg-dark-800/50"
          style={{ height }}
        >
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            Carregando waveform...
          </div>
        </div>
      )}
      <div
        ref={containerRef}
        className="w-full"
        style={{ height, opacity: isLoading ? 0 : 1 }}
      />
    </div>
  );
}

// Simplified waveform component that shows a visual representation
// without requiring the actual audio data (faster loading)
export function WaveformPlaceholder({
  duration,
  currentTime,
  onSeek,
  height = 50,
  waveColor = '#4B5563',
  progressColor = '#8B5CF6',
}: Omit<WaveformProps, 'videoUrl'>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [bars, setBars] = useState<number[]>([]);

  // Generate random bars on mount
  useEffect(() => {
    const numBars = Math.floor(duration * 10); // 10 bars per second
    const newBars = Array.from({ length: Math.max(numBars, 50) }, () =>
      0.2 + Math.random() * 0.8
    );
    setBars(newBars);
  }, [duration]);

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const progress = clickX / rect.width;
      onSeek(progress * duration);
    },
    [duration, onSeek]
  );

  const progress = duration > 0 ? currentTime / duration : 0;

  return (
    <div
      ref={containerRef}
      className="relative w-full cursor-pointer flex items-center justify-center gap-[1px]"
      style={{ height }}
      onClick={handleClick}
    >
      {bars.map((barHeight, index) => {
        const barProgress = index / bars.length;
        const isPlayed = barProgress <= progress;

        return (
          <div
            key={index}
            className="w-[2px] rounded-full transition-colors duration-100"
            style={{
              height: `${barHeight * height * 0.8}px`,
              backgroundColor: isPlayed ? progressColor : waveColor,
            }}
          />
        );
      })}

      {/* Playhead */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-white pointer-events-none z-10"
        style={{ left: `${progress * 100}%` }}
      />
    </div>
  );
}
