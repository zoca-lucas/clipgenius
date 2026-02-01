'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Video,
  Scissors,
  Coins,
  TrendingUp,
  Clock,
  Plus,
  ChevronRight,
  Gift,
  Flame,
  Calendar
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import Header from '@/components/Header';
import DashboardSidebar from '@/components/DashboardSidebar';
import StatsCard from '@/components/StatsCard';
import { getProjects, Project } from '@/lib/api';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, checkin } = useAuth();
  const [recentProjects, setRecentProjects] = useState<Project[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [checkinLoading, setCheckinLoading] = useState(false);
  const [checkinMessage, setCheckinMessage] = useState<{ type: 'success' | 'info'; text: string } | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    async function loadProjects() {
      try {
        const data = await getProjects(1, 5);
        setRecentProjects(data.items);
      } catch (error) {
        console.error('Failed to load projects:', error);
      } finally {
        setProjectsLoading(false);
      }
    }

    if (isAuthenticated) {
      loadProjects();
    }
  }, [isAuthenticated]);

  const handleCheckin = async () => {
    setCheckinLoading(true);
    setCheckinMessage(null);

    try {
      const result = await checkin();
      if (result.success) {
        setCheckinMessage({
          type: 'success',
          text: `+${result.total_bonus} creditos! Streak: ${result.streak_days} dias`
        });
      } else {
        setCheckinMessage({
          type: 'info',
          text: result.message || 'Voce ja fez check-in hoje'
        });
      }
    } catch (error) {
      setCheckinMessage({
        type: 'info',
        text: 'Erro ao fazer check-in'
      });
    } finally {
      setCheckinLoading(false);
    }
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <>
      <Header />
      <div className="flex">
        <DashboardSidebar />
        <main className="flex-1 p-8">
          <div className="max-w-6xl mx-auto">
            {/* Welcome */}
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-white mb-2">
                Ola, {user?.name || user?.email?.split('@')[0]}!
              </h1>
              <p className="text-gray-400">
                Bem-vindo ao seu dashboard. Crie cortes virais com IA.
              </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatsCard
                title="Creditos"
                value={user?.credits || 0}
                icon={<Coins className="w-5 h-5" />}
                color="yellow"
                link="/pricing"
                linkText="Comprar mais"
              />
              <StatsCard
                title="Videos Processados"
                value={user?.total_videos_processed || 0}
                icon={<Video className="w-5 h-5" />}
                color="blue"
              />
              <StatsCard
                title="Cortes Gerados"
                value={user?.total_clips_generated || 0}
                icon={<Scissors className="w-5 h-5" />}
                color="green"
              />
              <StatsCard
                title="Streak"
                value={`${user?.streak_days || 0} dias`}
                icon={<Flame className="w-5 h-5" />}
                color="orange"
              />
            </div>

            {/* Daily Check-in */}
            <div className="bg-dark-800 border border-dark-600 rounded-xl p-6 mb-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                    <Gift className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">Check-in Diario</h3>
                    <p className="text-sm text-gray-400">
                      Ganhe +4 creditos todo dia. Bonus de streak aos 7 e 30 dias!
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {checkinMessage && (
                    <span className={`text-sm ${checkinMessage.type === 'success' ? 'text-green-400' : 'text-gray-400'}`}>
                      {checkinMessage.text}
                    </span>
                  )}
                  <button
                    onClick={handleCheckin}
                    disabled={checkinLoading}
                    className="px-4 py-2 bg-primary hover:bg-primary-dark text-white font-medium rounded-lg transition-colors disabled:opacity-50"
                  >
                    {checkinLoading ? 'Carregando...' : 'Fazer Check-in'}
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              <Link
                href="/"
                className="bg-dark-800 border border-dark-600 rounded-xl p-6 hover:border-primary/50 transition-colors group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                    <Plus className="w-6 h-6 text-primary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-white group-hover:text-primary transition-colors">
                      Novo Projeto
                    </h3>
                    <p className="text-sm text-gray-400">Cole uma URL do YouTube para comecar</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-primary transition-colors" />
                </div>
              </Link>

              <Link
                href="/projects"
                className="bg-dark-800 border border-dark-600 rounded-xl p-6 hover:border-primary/50 transition-colors group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center group-hover:bg-blue-500/20 transition-colors">
                    <Video className="w-6 h-6 text-blue-500" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-white group-hover:text-blue-400 transition-colors">
                      Meus Projetos
                    </h3>
                    <p className="text-sm text-gray-400">Ver todos os projetos e cortes</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-blue-400 transition-colors" />
                </div>
              </Link>
            </div>

            {/* Recent Projects */}
            <div className="bg-dark-800 border border-dark-600 rounded-xl">
              <div className="p-6 border-b border-dark-600 flex items-center justify-between">
                <h2 className="font-semibold text-white">Projetos Recentes</h2>
                <Link href="/projects" className="text-sm text-primary hover:underline">
                  Ver todos
                </Link>
              </div>

              {projectsLoading ? (
                <div className="p-6 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary mx-auto"></div>
                </div>
              ) : recentProjects.length === 0 ? (
                <div className="p-6 text-center">
                  <Video className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-400 mb-4">Nenhum projeto ainda</p>
                  <Link
                    href="/"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-lg transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    Criar primeiro projeto
                  </Link>
                </div>
              ) : (
                <div className="divide-y divide-dark-600">
                  {recentProjects.map((project) => (
                    <Link
                      key={project.id}
                      href={`/projects/${project.id}`}
                      className="flex items-center gap-4 p-4 hover:bg-dark-700 transition-colors"
                    >
                      {project.thumbnail_url ? (
                        <img
                          src={project.thumbnail_url}
                          alt={project.title || ''}
                          className="w-16 h-10 object-cover rounded"
                        />
                      ) : (
                        <div className="w-16 h-10 bg-dark-600 rounded flex items-center justify-center">
                          <Video className="w-5 h-5 text-gray-500" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-white truncate">
                          {project.title || 'Sem titulo'}
                        </h3>
                        <p className="text-xs text-gray-400">
                          {project.clips_count} cortes
                        </p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded ${
                        project.status === 'completed'
                          ? 'bg-green-500/10 text-green-400'
                          : project.status === 'error'
                          ? 'bg-red-500/10 text-red-400'
                          : 'bg-yellow-500/10 text-yellow-400'
                      }`}>
                        {project.status === 'completed' ? 'Concluido' :
                         project.status === 'error' ? 'Erro' : 'Processando'}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
