'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Play,
  Zap,
  Sparkles,
  TrendingUp,
  Clock,
  Palette,
  Download,
  CheckCircle,
  ArrowRight,
  Star,
  MessageSquare,
  Video,
  Scissors,
  Wand2,
} from 'lucide-react';

// Feature Card Component
function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <div className="p-6 bg-dark-800 rounded-2xl border border-dark-700 hover:border-primary/50 transition-all group">
      <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
        <Icon className="w-6 h-6 text-primary" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
    </div>
  );
}

// Pricing Card Component
function PricingCard({
  name,
  price,
  period,
  description,
  features,
  isPopular,
  ctaText,
}: {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  isPopular?: boolean;
  ctaText: string;
}) {
  return (
    <div
      className={`relative p-6 rounded-2xl border ${
        isPopular
          ? 'bg-gradient-to-b from-primary/10 to-dark-800 border-primary'
          : 'bg-dark-800 border-dark-700'
      }`}
    >
      {isPopular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-black text-xs font-bold rounded-full">
          MAIS POPULAR
        </div>
      )}

      <div className="text-center mb-6">
        <h3 className="text-xl font-bold text-white mb-2">{name}</h3>
        <div className="flex items-baseline justify-center gap-1">
          <span className="text-4xl font-bold text-white">{price}</span>
          <span className="text-gray-400">{period}</span>
        </div>
        <p className="text-gray-500 text-sm mt-2">{description}</p>
      </div>

      <ul className="space-y-3 mb-6">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start gap-2">
            <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
            <span className="text-gray-300 text-sm">{feature}</span>
          </li>
        ))}
      </ul>

      <Link
        href="/"
        className={`block w-full py-3 rounded-xl font-medium text-center transition-all ${
          isPopular
            ? 'bg-primary hover:bg-primary/90 text-black'
            : 'bg-dark-700 hover:bg-dark-600 text-white'
        }`}
      >
        {ctaText}
      </Link>
    </div>
  );
}

// Testimonial Card Component
function TestimonialCard({
  quote,
  author,
  role,
  avatar,
}: {
  quote: string;
  author: string;
  role: string;
  avatar: string;
}) {
  return (
    <div className="p-6 bg-dark-800 rounded-2xl border border-dark-700">
      <div className="flex gap-1 mb-4">
        {[...Array(5)].map((_, i) => (
          <Star key={i} className="w-4 h-4 fill-yellow-500 text-yellow-500" />
        ))}
      </div>
      <p className="text-gray-300 mb-4">&ldquo;{quote}&rdquo;</p>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold">
          {avatar}
        </div>
        <div>
          <p className="text-white font-medium">{author}</p>
          <p className="text-gray-500 text-sm">{role}</p>
        </div>
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-dark-900 text-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-dark-900/80 backdrop-blur-lg border-b border-dark-800">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/landing" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-purple-600 rounded-lg flex items-center justify-center">
                <Scissors className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold">ClipGenius</span>
            </Link>

            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-400 hover:text-white transition-colors">
                Recursos
              </a>
              <a href="#pricing" className="text-gray-400 hover:text-white transition-colors">
                Precos
              </a>
              <a href="#testimonials" className="text-gray-400 hover:text-white transition-colors">
                Depoimentos
              </a>
            </div>

            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="hidden sm:block px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Entrar
              </Link>
              <Link
                href="/"
                className="px-4 py-2 bg-primary hover:bg-primary/90 text-black font-medium rounded-lg transition-colors"
              >
                Comecar Gratis
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 border border-primary/30 rounded-full text-primary text-sm mb-8">
            <Sparkles className="w-4 h-4" />
            IA que detecta momentos virais
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
            Transforme seus videos em{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-purple-500 to-pink-500">
              clips virais
            </span>{' '}
            automaticamente
          </h1>

          {/* Subheadline */}
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            O ClipGenius usa inteligencia artificial para identificar os melhores momentos do seu
            video e criar cortes otimizados para TikTok, Reels e Shorts em segundos.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Link
              href="/"
              className="w-full sm:w-auto px-8 py-4 bg-primary hover:bg-primary/90 text-black font-bold rounded-xl transition-all hover:scale-105 flex items-center justify-center gap-2"
            >
              Comecar Gratis
              <ArrowRight className="w-5 h-5" />
            </Link>
            <a
              href="#demo"
              className="w-full sm:w-auto px-8 py-4 bg-dark-800 hover:bg-dark-700 border border-dark-600 rounded-xl transition-all flex items-center justify-center gap-2"
            >
              <Play className="w-5 h-5" />
              Ver Demo
            </a>
          </div>

          {/* Social Proof */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <div className="flex -space-x-2">
                {['J', 'M', 'A', 'R'].map((letter, i) => (
                  <div
                    key={i}
                    className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/80 to-purple-600/80 border-2 border-dark-900 flex items-center justify-center text-xs font-bold text-white"
                  >
                    {letter}
                  </div>
                ))}
              </div>
              <span>+2.000 criadores usando</span>
            </div>
            <div className="flex items-center gap-1">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-4 h-4 fill-yellow-500 text-yellow-500" />
              ))}
              <span className="ml-1">4.9/5 avaliacao</span>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Video Section */}
      <section id="demo" className="py-20 px-4 bg-dark-850">
        <div className="max-w-6xl mx-auto">
          <div className="relative aspect-video rounded-2xl overflow-hidden bg-dark-800 border border-dark-700">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center mb-4 mx-auto cursor-pointer hover:bg-primary/30 transition-colors">
                  <Play className="w-10 h-10 text-primary ml-1" />
                </div>
                <p className="text-gray-400">Veja como funciona em 60 segundos</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Tudo que voce precisa para criar clips virais
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Ferramentas profissionais alimentadas por IA para maximizar o engajamento dos seus videos
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon={Zap}
              title="Deteccao de Momentos Virais"
              description="Nossa IA analisa seu video e identifica automaticamente os momentos com maior potencial viral."
            />
            <FeatureCard
              icon={MessageSquare}
              title="Legendas Automaticas"
              description="Transcricao precisa com legendas no estilo viral - Hormozi, karaoke e muito mais."
            />
            <FeatureCard
              icon={Video}
              title="Reframe Inteligente"
              description="Conversao automatica de videos horizontais para vertical com tracking de rosto."
            />
            <FeatureCard
              icon={Palette}
              title="Brand Kit"
              description="Salve e aplique seus estilos de marca em todos os clips com um clique."
            />
            <FeatureCard
              icon={TrendingUp}
              title="Score de Viralidade"
              description="Cada clip recebe uma pontuacao baseada em fatores que impulsionam o algoritmo."
            />
            <FeatureCard
              icon={Clock}
              title="Economia de Tempo"
              description="O que levaria horas para editar, fazemos em minutos. Foque no que importa: criar conteudo."
            />
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 px-4 bg-dark-850">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">Como funciona</h2>
            <p className="text-gray-400">De video longo a clips virais em 3 passos simples</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                title: 'Cole o link',
                description: 'Cole o link do YouTube ou faca upload do seu video',
                icon: Video,
              },
              {
                step: '2',
                title: 'IA analisa',
                description: 'Nossa IA identifica os melhores momentos e gera clips otimizados',
                icon: Wand2,
              },
              {
                step: '3',
                title: 'Exporte',
                description: 'Personalize, adicione legendas e exporte para todas as plataformas',
                icon: Download,
              },
            ].map((item, index) => (
              <div key={index} className="text-center relative">
                <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-6 relative">
                  <item.icon className="w-8 h-8 text-primary" />
                  <div className="absolute -top-2 -right-2 w-6 h-6 bg-primary text-black text-sm font-bold rounded-full flex items-center justify-center">
                    {item.step}
                  </div>
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-gray-400">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">Planos simples e transparentes</h2>
            <p className="text-gray-400">Comece gratis, escale quando precisar</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <PricingCard
              name="Free"
              price="R$0"
              period="/mes"
              description="Para quem esta comecando"
              features={[
                '5 videos por mes',
                'Ate 15 minutos por video',
                '5 clips por video',
                'Legendas automaticas',
                'Marca dagua ClipGenius',
              ]}
              ctaText="Comecar Gratis"
            />
            <PricingCard
              name="Pro"
              price="R$47"
              period="/mes"
              description="Para criadores serios"
              features={[
                '30 videos por mes',
                'Ate 2 horas por video',
                '15 clips por video',
                'Sem marca dagua',
                'Brand Kit ilimitado',
                'Exportacao em massa',
                'Suporte prioritario',
              ]}
              isPopular
              ctaText="Comecar Teste Gratis"
            />
            <PricingCard
              name="Business"
              price="R$197"
              period="/mes"
              description="Para equipes e agencias"
              features={[
                'Videos ilimitados',
                'Duracao ilimitada',
                'Clips ilimitados',
                'API access',
                'Multi-usuarios',
                'Gerenciador dedicado',
                'SLA garantido',
              ]}
              ctaText="Falar com Vendas"
            />
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20 px-4 bg-dark-850">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Amado por criadores de conteudo
            </h2>
            <p className="text-gray-400">Veja o que nossos usuarios estao dizendo</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <TestimonialCard
              quote="Economizo mais de 10 horas por semana. A deteccao de momentos virais e absurdamente precisa!"
              author="Lucas Silva"
              role="Criador de Conteudo"
              avatar="L"
            />
            <TestimonialCard
              quote="As legendas no estilo Hormozi fizeram meus Reels bombarem. 3x mais visualizacoes!"
              author="Marina Costa"
              role="Coach Digital"
              avatar="M"
            />
            <TestimonialCard
              quote="Finalmente uma ferramenta que entende o que faz um clip viralizar. Indispensavel!"
              author="Rafael Santos"
              role="Podcaster"
              avatar="R"
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="p-12 bg-gradient-to-br from-primary/20 to-purple-600/20 rounded-3xl border border-primary/30">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Pronto para criar clips virais?
            </h2>
            <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
              Junte-se a mais de 2.000 criadores que ja estao usando o ClipGenius para multiplicar
              seu alcance nas redes sociais.
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-8 py-4 bg-primary hover:bg-primary/90 text-black font-bold rounded-xl transition-all hover:scale-105"
            >
              Comecar Gratis Agora
              <ArrowRight className="w-5 h-5" />
            </Link>
            <p className="text-gray-500 text-sm mt-4">
              Sem cartao de credito necessario
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-dark-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-purple-600 rounded-lg flex items-center justify-center">
                <Scissors className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold">ClipGenius</span>
            </div>

            <div className="flex items-center gap-6 text-sm text-gray-400">
              <a href="#" className="hover:text-white transition-colors">
                Termos de Uso
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Privacidade
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Contato
              </a>
            </div>

            <p className="text-gray-500 text-sm">
              &copy; 2024 ClipGenius. Todos os direitos reservados.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
