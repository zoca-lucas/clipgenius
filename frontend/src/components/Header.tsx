'use client';

import Link from 'next/link';
import { Scissors, Github } from 'lucide-react';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-dark-900/80 backdrop-blur-sm border-b border-dark-600">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
              <Scissors className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl text-white group-hover:text-primary transition-colors">
              ClipGenius
            </span>
          </Link>

          {/* Nav */}
          <nav className="flex items-center gap-6">
            <Link
              href="/"
              className="text-gray-400 hover:text-white transition-colors text-sm font-medium"
            >
              Inicio
            </Link>
            <Link
              href="/projects"
              className="text-gray-400 hover:text-white transition-colors text-sm font-medium"
            >
              Meus Projetos
            </Link>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-white transition-colors"
            >
              <Github className="w-5 h-5" />
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
