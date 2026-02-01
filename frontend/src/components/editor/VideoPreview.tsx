'use client';

import { useRef, useEffect, useState, forwardRef, useImperativeHandle, useMemo } from 'react';
import { SubtitleEntry, SubtitleStyle, Layer } from '@/lib/editorApi';
import {
  generateAnimationCSS,
  getAnimationStyle,
  getAnimationDuration,
} from '@/lib/textAnimations';

interface VideoPreviewProps {
  videoUrl: string;
  subtitles: SubtitleEntry[];
  subtitleStyle: SubtitleStyle;
  layers: Layer[];
  onTimeUpdate?: (time: number) => void;
  onDurationChange?: (duration: number) => void;
  onPlay?: () => void;
  onPause?: () => void;
}

export interface VideoPreviewRef {
  play: () => void;
  pause: () => void;
  seek: (time: number) => void;
  getCurrentTime: () => number;
  getDuration: () => number;
  isPlaying: () => boolean;
  getVideoElement: () => HTMLVideoElement | null;
}

const VideoPreview = forwardRef<VideoPreviewRef, VideoPreviewProps>(
  (
    {
      videoUrl,
      subtitles,
      subtitleStyle,
      layers,
      onTimeUpdate,
      onDurationChange,
      onPlay,
      onPause,
    },
    ref
  ) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [currentSubtitle, setCurrentSubtitle] = useState<SubtitleEntry | null>(null);
    const [currentWordIndex, setCurrentWordIndex] = useState(-1);
    const [isPlaying, setIsPlaying] = useState(false);
    const [animationPhase, setAnimationPhase] = useState<'in' | 'visible' | 'out'>('visible');
    const [subtitleKey, setSubtitleKey] = useState(0);
    const prevSubtitleRef = useRef<SubtitleEntry | null>(null);

    // Generate animation CSS
    const animationCSS = useMemo(() => generateAnimationCSS(), []);

    // Expose video controls via ref
    useImperativeHandle(ref, () => ({
      play: () => videoRef.current?.play(),
      pause: () => videoRef.current?.pause(),
      seek: (time: number) => {
        if (videoRef.current) {
          videoRef.current.currentTime = time;
        }
      },
      getCurrentTime: () => videoRef.current?.currentTime || 0,
      getDuration: () => videoRef.current?.duration || 0,
      isPlaying: () => isPlaying,
      getVideoElement: () => videoRef.current,
    }));

    // Find current subtitle based on time and manage animation phases
    useEffect(() => {
      const subtitle = subtitles.find(
        (s) => currentTime >= s.start && currentTime <= s.end
      );

      // Detect subtitle change for animation restart
      if (subtitle?.id !== prevSubtitleRef.current?.id) {
        prevSubtitleRef.current = subtitle || null;
        if (subtitle) {
          setSubtitleKey((k) => k + 1);
          setAnimationPhase('in');
        }
      }

      setCurrentSubtitle(subtitle || null);

      // Calculate animation phase based on timing
      if (subtitle && subtitleStyle.animationIn !== 'none') {
        const animInDuration = getAnimationDuration(subtitleStyle.animationIn) / 1000;
        const animOutDuration = getAnimationDuration(subtitleStyle.animationOut) / 1000;
        const timeInSubtitle = currentTime - subtitle.start;
        const timeToEnd = subtitle.end - currentTime;

        if (timeInSubtitle < animInDuration) {
          setAnimationPhase('in');
        } else if (timeToEnd < animOutDuration && subtitleStyle.animationOut !== 'none') {
          setAnimationPhase('out');
        } else {
          setAnimationPhase('visible');
        }
      }

      // Find current word for karaoke effect
      if (subtitle && subtitle.words && subtitleStyle.karaokeEnabled) {
        const wordIndex = subtitle.words.findIndex(
          (w) => currentTime >= w.start && currentTime <= w.end
        );
        setCurrentWordIndex(wordIndex);
      } else {
        setCurrentWordIndex(-1);
      }
    }, [currentTime, subtitles, subtitleStyle.karaokeEnabled, subtitleStyle.animationIn, subtitleStyle.animationOut]);

    // Handle time update
    const handleTimeUpdate = () => {
      if (videoRef.current) {
        const time = videoRef.current.currentTime;
        setCurrentTime(time);
        onTimeUpdate?.(time);
      }
    };

    // Handle duration change
    const handleDurationChange = () => {
      if (videoRef.current) {
        onDurationChange?.(videoRef.current.duration);
      }
    };

    // Check if subtitle layer is visible
    const isSubtitleVisible = layers.find((l) => l.id === 'subtitle')?.visible ?? true;
    const isVideoVisible = layers.find((l) => l.id === 'video')?.visible ?? true;

    // Render subtitle text with karaoke highlighting
    const renderSubtitleText = () => {
      if (!currentSubtitle) return null;

      if (subtitleStyle.karaokeEnabled && currentSubtitle.words && currentSubtitle.words.length > 0) {
        // Karaoke mode: highlight word by word
        return (
          <span>
            {currentSubtitle.words.map((word, index) => {
              const isActive = index <= currentWordIndex;
              const isCurrent = index === currentWordIndex;
              return (
                <span
                  key={`${currentSubtitle.id}-word-${index}`}
                  style={{
                    color: isActive ? subtitleStyle.highlightColor : subtitleStyle.primaryColor,
                    transform: isCurrent && subtitleStyle.scaleEffect ? 'scale(1.1)' : 'scale(1)',
                    display: 'inline-block',
                    transition: 'transform 0.1s ease-out, color 0.05s ease-out',
                  }}
                >
                  {word.word}
                  {index < currentSubtitle.words!.length - 1 ? ' ' : ''}
                </span>
              );
            })}
          </span>
        );
      }

      // Simple mode: show full text
      return <span style={{ color: subtitleStyle.primaryColor }}>{currentSubtitle.text}</span>;
    };

    // Get animation styles
    const animationStyles = getAnimationStyle(
      subtitleStyle.animationIn,
      subtitleStyle.animationOut,
      subtitleStyle.animationLoop,
      animationPhase
    );

    return (
      <div className="relative w-full h-full bg-black rounded-lg overflow-hidden">
        {/* Inject animation keyframes */}
        <style dangerouslySetInnerHTML={{ __html: animationCSS }} />

        {/* Video Layer */}
        <video
          ref={videoRef}
          src={videoUrl}
          className={`w-full h-full object-contain ${!isVideoVisible ? 'opacity-0' : ''}`}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleDurationChange}
          onPlay={() => {
            setIsPlaying(true);
            onPlay?.();
          }}
          onPause={() => {
            setIsPlaying(false);
            onPause?.();
          }}
          playsInline
        />

        {/* Subtitle Overlay Layer */}
        {isSubtitleVisible && currentSubtitle && (
          <div
            className="absolute left-0 right-0 flex justify-center pointer-events-none"
            style={{
              bottom: `${subtitleStyle.marginV}px`,
              padding: '0 20px',
            }}
          >
            <div
              key={subtitleKey}
              style={{
                fontFamily: subtitleStyle.fontName,
                fontSize: `${subtitleStyle.fontSize}px`,
                fontWeight: 'bold',
                textAlign: 'center',
                textTransform: subtitleStyle.uppercase ? 'uppercase' : 'none',
                textShadow: `
                  ${subtitleStyle.outlineSize}px ${subtitleStyle.outlineSize}px ${subtitleStyle.shadowSize}px ${subtitleStyle.outlineColor},
                  -${subtitleStyle.outlineSize}px ${subtitleStyle.outlineSize}px ${subtitleStyle.shadowSize}px ${subtitleStyle.outlineColor},
                  ${subtitleStyle.outlineSize}px -${subtitleStyle.outlineSize}px ${subtitleStyle.shadowSize}px ${subtitleStyle.outlineColor},
                  -${subtitleStyle.outlineSize}px -${subtitleStyle.outlineSize}px ${subtitleStyle.shadowSize}px ${subtitleStyle.outlineColor}
                `,
                maxWidth: '90%',
                wordWrap: 'break-word',
                padding: subtitleStyle.backgroundEnabled ? '8px 16px' : undefined,
                backgroundColor: subtitleStyle.backgroundEnabled ? subtitleStyle.backgroundColor : undefined,
                borderRadius: subtitleStyle.backgroundEnabled ? '8px' : undefined,
                ...animationStyles,
              }}
            >
              {renderSubtitleText()}
            </div>
          </div>
        )}

        {/* Hidden Layer Indicator */}
        {!isVideoVisible && (
          <div className="absolute inset-0 flex items-center justify-center bg-dark-900/80">
            <span className="text-gray-400 text-sm">Camada de video oculta</span>
          </div>
        )}
      </div>
    );
  }
);

VideoPreview.displayName = 'VideoPreview';

export default VideoPreview;
