'use client';

import { useEffect, useState } from 'react';
import { Loader2, Download, Mic, Brain, Scissors, CheckCircle, AlertCircle } from 'lucide-react';

interface ProgressBarProps {
  progress: number;
  status: string;
  message: string;
  stepProgress?: string | null;
  etaSeconds?: number | null;
}

const STATUS_CONFIG: Record<string, { icon: typeof Loader2; color: string; label: string }> = {
  pending: { icon: Loader2, color: 'text-gray-400', label: 'Aguardando' },
  downloading: { icon: Download, color: 'text-blue-400', label: 'Download' },
  transcribing: { icon: Mic, color: 'text-purple-400', label: 'Transcrição' },
  analyzing: { icon: Brain, color: 'text-yellow-400', label: 'Análise IA' },
  cutting: { icon: Scissors, color: 'text-green-400', label: 'Gerando Cortes' },
  completed: { icon: CheckCircle, color: 'text-green-500', label: 'Concluído' },
  error: { icon: AlertCircle, color: 'text-red-500', label: 'Erro' },
};

function formatETA(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${mins}min ${secs}s` : `${mins}min`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
  }
}

export default function ProgressBar({
  progress,
  status,
  message,
  stepProgress,
  etaSeconds,
}: ProgressBarProps) {
  const [animatedProgress, setAnimatedProgress] = useState(0);

  // Animate progress bar
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedProgress(progress);
    }, 100);
    return () => clearTimeout(timer);
  }, [progress]);

  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const Icon = config.icon;
  const isProcessing = !['completed', 'error'].includes(status);

  return (
    <div className="bg-dark-600 rounded-xl p-6 border border-dark-500">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-dark-700 ${config.color}`}>
            <Icon className={`w-5 h-5 ${isProcessing ? 'animate-pulse' : ''}`} />
          </div>
          <div>
            <p className={`font-semibold ${config.color}`}>{config.label}</p>
            {stepProgress && (
              <p className="text-xs text-gray-500">Etapa {stepProgress}</p>
            )}
          </div>
        </div>

        <div className="text-right">
          <p className="text-2xl font-bold text-white">{progress}%</p>
          {etaSeconds && etaSeconds > 0 && (
            <p className="text-xs text-gray-500">
              ~{formatETA(etaSeconds)} restante
            </p>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="relative h-3 bg-dark-700 rounded-full overflow-hidden mb-3">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-dark-700 via-dark-600 to-dark-700 opacity-50" />

        {/* Progress fill */}
        <div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-primary via-primary to-purple-500 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${animatedProgress}%` }}
        >
          {/* Shine effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
        </div>

        {/* Step markers */}
        <div className="absolute inset-0 flex">
          {[15, 40, 60].map((marker) => (
            <div
              key={marker}
              className="absolute top-0 bottom-0 w-px bg-dark-500"
              style={{ left: `${marker}%` }}
            />
          ))}
        </div>
      </div>

      {/* Message */}
      <div className="flex items-center gap-2">
        {isProcessing && (
          <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
        )}
        <p className="text-sm text-gray-400">{message}</p>
      </div>

      {/* Step labels */}
      <div className="flex justify-between mt-4 text-xs text-gray-600">
        <span className={progress >= 0 ? 'text-gray-400' : ''}>Download</span>
        <span className={progress >= 15 ? 'text-gray-400' : ''}>Transcrição</span>
        <span className={progress >= 40 ? 'text-gray-400' : ''}>Análise</span>
        <span className={progress >= 60 ? 'text-gray-400' : ''}>Cortes</span>
        <span className={progress >= 100 ? 'text-green-400' : ''}>Pronto</span>
      </div>
    </div>
  );
}
