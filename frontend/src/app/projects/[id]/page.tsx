'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import {
  ArrowLeft,
  Clock,
  Film,
  Loader2,
  RefreshCw,
  Trash2,
  ExternalLink,
} from 'lucide-react';
import Header from '@/components/Header';
import ClipCard from '@/components/ClipCard';
import ProgressBar from '@/components/ProgressBar';
import {
  getProject,
  getProjectStatus,
  deleteProject,
  deleteClip,
  ProjectDetail,
  ProcessingStatus,
  formatDuration,
  getStatusColor,
  getStatusLabel,
} from '@/lib/api';

export default function ProjectPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = Number(params.id);

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [status, setStatus] = useState<ProcessingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const loadProject = useCallback(async () => {
    try {
      const data = await getProject(projectId);
      setProject(data);

      // If still processing, also fetch status
      if (!['completed', 'error'].includes(data.status)) {
        const statusData = await getProjectStatus(projectId);
        setStatus(statusData);
      } else {
        setStatus(null);
      }
    } catch (err) {
      setError('Projeto não encontrado');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  // Poll for status updates while processing
  useEffect(() => {
    // Clear any existing interval first
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    if (project && !['completed', 'error'].includes(project.status)) {
      pollingIntervalRef.current = setInterval(loadProject, 3000);
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [project?.status, loadProject]);

  const handleDeleteProject = async () => {
    if (!confirm('Tem certeza que deseja deletar este projeto e todos os cortes?')) {
      return;
    }

    try {
      await deleteProject(projectId);
      router.push('/');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao deletar projeto';
      setError(message);
    }
  };

  const handleDeleteClip = async (clipId: number) => {
    try {
      await deleteClip(clipId);
      loadProject();
    } catch (err) {
      console.error('Failed to delete clip:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-900">
        <Header />
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-dark-900">
        <Header />
        <div className="max-w-4xl mx-auto px-4 py-20 text-center">
          <p className="text-red-400 mb-4">{error || 'Projeto não encontrado'}</p>
          <Link href="/" className="text-primary hover:underline">
            Voltar para o início
          </Link>
        </div>
      </div>
    );
  }

  const isProcessing = !['completed', 'error'].includes(project.status);

  return (
    <div className="min-h-screen bg-dark-900">
      <Header />

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Back button */}
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar
        </Link>

        {/* Project Header */}
        <div className="bg-dark-700 rounded-xl border border-dark-600 overflow-hidden mb-8">
          <div className="flex flex-col md:flex-row gap-6 p-6">
            {/* Thumbnail */}
            <div className="relative w-full md:w-80 aspect-video bg-dark-800 rounded-lg overflow-hidden flex-shrink-0">
              {project.thumbnail_url ? (
                <Image
                  src={project.thumbnail_url}
                  alt={project.title || 'Video thumbnail'}
                  fill
                  className="object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Film className="w-12 h-12 text-gray-600" />
                </div>
              )}
            </div>

            {/* Info */}
            <div className="flex-1">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-white mb-2">
                    {project.title || 'Carregando...'}
                  </h1>

                  <div className="flex items-center gap-4 text-sm text-gray-400 mb-4">
                    {project.duration && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatDuration(project.duration)}
                      </span>
                    )}
                    <span>{project.clips_count} cortes</span>
                    <span className={getStatusColor(project.status)}>
                      {isProcessing && (
                        <Loader2 className="w-3 h-3 animate-spin inline mr-1" />
                      )}
                      {getStatusLabel(project.status)}
                    </span>
                  </div>

                  {/* Processing status with progress bar */}
                  {status && isProcessing && (
                    <div className="mb-4">
                      <ProgressBar
                        progress={status.progress}
                        status={status.status}
                        message={status.message}
                        stepProgress={status.step_progress}
                        etaSeconds={status.eta_seconds}
                      />
                    </div>
                  )}

                  {/* YouTube link */}
                  <a
                    href={project.youtube_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
                  >
                    Abrir no YouTube
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={loadProject}
                    className="p-2 bg-dark-600 hover:bg-dark-500 rounded-lg text-gray-400 hover:text-white transition-colors"
                    title="Atualizar"
                  >
                    <RefreshCw className="w-5 h-5" />
                  </button>
                  <button
                    onClick={handleDeleteProject}
                    disabled={isProcessing}
                    className={`p-2 rounded-lg transition-colors ${
                      isProcessing
                        ? 'bg-gray-500/20 text-gray-500 cursor-not-allowed'
                        : 'bg-red-500/20 hover:bg-red-500/30 text-red-400'
                    }`}
                    title={isProcessing ? 'Aguarde o processamento terminar' : 'Deletar projeto'}
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Clips Grid */}
        {project.status === 'completed' && project.clips.length > 0 ? (
          <div>
            <h2 className="text-xl font-bold text-white mb-6">
              Cortes Gerados ({project.clips.length})
            </h2>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {project.clips
                .sort((a, b) => (b.viral_score || 0) - (a.viral_score || 0))
                .map((clip) => (
                  <ClipCard
                    key={clip.id}
                    clip={clip}
                    onDelete={handleDeleteClip}
                  />
                ))}
            </div>
          </div>
        ) : project.status === 'error' ? (
          <div className="text-center py-12">
            <p className="text-red-400 mb-2">Erro no processamento</p>
            <p className="text-gray-500 text-sm">{project.error_message}</p>
          </div>
        ) : (
          <div className="py-8">
            <h2 className="text-xl font-bold text-white mb-6">
              Processando Vídeo
            </h2>
            {status ? (
              <ProgressBar
                progress={status.progress}
                status={status.status}
                message={status.message}
                stepProgress={status.step_progress}
                etaSeconds={status.eta_seconds}
              />
            ) : (
              <div className="text-center py-12">
                <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
                <p className="text-gray-400">Iniciando processamento...</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
