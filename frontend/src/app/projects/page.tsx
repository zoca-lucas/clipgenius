'use client';

import { useEffect, useState } from 'react';
import { FolderOpen, Plus, Loader2 } from 'lucide-react';
import Link from 'next/link';
import Header from '@/components/Header';
import ProjectCard from '@/components/ProjectCard';
import { getProjects, Project } from '@/lib/api';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 12;

  useEffect(() => {
    loadProjects();
  }, [page]);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await getProjects(page, perPage);
      setProjects(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="min-h-screen bg-dark-900">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
              <FolderOpen className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Meus Projetos</h1>
              <p className="text-sm text-gray-400">
                {total} {total === 1 ? 'projeto' : 'projetos'} no total
              </p>
            </div>
          </div>

          <Link
            href="/"
            className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Novo Projeto
          </Link>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-20">
            <FolderOpen className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">
              Nenhum projeto ainda
            </h2>
            <p className="text-gray-400 mb-6">
              Comece criando seu primeiro projeto com um link do YouTube
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-6 py-3 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-colors"
            >
              <Plus className="w-5 h-5" />
              Criar Primeiro Projeto
            </Link>
          </div>
        ) : (
          <>
            {/* Projects Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {projects.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-dark-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-dark-600 transition-colors"
                >
                  Anterior
                </button>

                <span className="px-4 py-2 text-gray-400">
                  Página {page} de {totalPages}
                </span>

                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-dark-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-dark-600 transition-colors"
                >
                  Próxima
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
