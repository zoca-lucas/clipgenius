'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Clock, Film, Loader2 } from 'lucide-react';
import { Project, formatDuration, getStatusColor, getStatusLabel } from '@/lib/api';

interface ProjectCardProps {
  project: Project;
}

export default function ProjectCard({ project }: ProjectCardProps) {
  const isProcessing = !['completed', 'error'].includes(project.status);

  return (
    <Link href={`/projects/${project.id}`}>
      <div className="bg-dark-700 rounded-xl overflow-hidden border border-dark-600 hover:border-primary/50 transition-all cursor-pointer group">
        {/* Thumbnail */}
        <div className="relative aspect-video bg-dark-800">
          {project.thumbnail_url ? (
            <Image
              src={project.thumbnail_url}
              alt={project.title || 'Video thumbnail'}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Film className="w-12 h-12 text-gray-600" />
            </div>
          )}

          {/* Status Badge */}
          <div className={`absolute top-3 right-3 px-2 py-1 rounded-lg text-xs font-medium bg-dark-900/80 backdrop-blur-sm ${getStatusColor(project.status)}`}>
            {isProcessing && <Loader2 className="w-3 h-3 animate-spin inline mr-1" />}
            {getStatusLabel(project.status)}
          </div>

          {/* Clips count */}
          {project.clips_count > 0 && (
            <div className="absolute bottom-3 right-3 px-2 py-1 rounded-lg text-xs font-medium bg-primary text-white">
              {project.clips_count} cortes
            </div>
          )}
        </div>

        {/* Info */}
        <div className="p-4">
          <h3 className="font-semibold text-white text-sm line-clamp-2 mb-2 group-hover:text-primary transition-colors">
            {project.title || 'Carregando...'}
          </h3>

          <div className="flex items-center gap-4 text-xs text-gray-400">
            {project.duration && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatDuration(project.duration)}
              </span>
            )}
            <span>
              {new Date(project.created_at).toLocaleDateString('pt-BR')}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
