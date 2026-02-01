'use client';

import { useEffect, useState } from 'react';
import { Scissors, Zap, Brain, Subtitles } from 'lucide-react';
import Header from '@/components/Header';
import URLInput from '@/components/URLInput';
import ProjectCard from '@/components/ProjectCard';
import { getProjects, Project } from '@/lib/api';

export default function Home() {
  const [recentProjects, setRecentProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecentProjects();
  }, []);

  const loadRecentProjects = async () => {
    try {
      const data = await getProjects(1, 4);
      setRecentProjects(data.items);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      icon: Brain,
      title: 'Análise com IA',
      description: 'Claude analisa o conteúdo e identifica os melhores momentos virais',
    },
    {
      icon: Scissors,
      title: '15 Cortes Automáticos',
      description: 'Gera automaticamente 15 cortes otimizados para shorts/reels',
    },
    {
      icon: Zap,
      title: 'Notas de Viralidade',
      description: 'Cada corte recebe uma nota de 0-10 baseada em potencial viral',
    },
    {
      icon: Subtitles,
      title: 'Legendas Automáticas',
      description: 'Legendas sincronizadas geradas com Whisper AI',
    },
  ];

  return (
    <div className="min-h-screen bg-dark-900">
      <Header />

      {/* Hero */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/20 rounded-full text-primary text-sm font-medium mb-6">
            <Zap className="w-4 h-4" />
            Powered by Claude AI & Whisper
          </div>

          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
            Transforme vídeos em{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">
              cortes virais
            </span>
          </h1>

          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
            Cole um link do YouTube e deixe a IA gerar automaticamente 15 cortes
            com notas de viralidade e legendas sincronizadas.
          </p>

          <URLInput />
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 bg-dark-800/50">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <div
                key={index}
                className="p-6 bg-dark-700 rounded-xl border border-dark-600 hover:border-primary/50 transition-all"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Recent Projects */}
      {recentProjects.length > 0 && (
        <section className="py-16 px-4">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-8">Projetos Recentes</h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {recentProjects.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-dark-600">
        <div className="max-w-6xl mx-auto text-center text-gray-500 text-sm">
          <p>ClipGenius - Gerador de Cortes com IA</p>
          <p className="mt-1">Feito com Claude AI, Whisper e FFmpeg</p>
        </div>
      </footer>
    </div>
  );
}
