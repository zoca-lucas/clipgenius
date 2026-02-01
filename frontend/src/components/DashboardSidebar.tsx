'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Video,
  Coins,
  Palette,
  Settings,
  HelpCircle,
  Share2
} from 'lucide-react';

const menuItems = [
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    label: 'Meus Projetos',
    href: '/projects',
    icon: Video,
  },
  {
    label: 'Brand Kit',
    href: '/dashboard/brand-kit',
    icon: Palette,
  },
  {
    label: 'Redes Sociais',
    href: '/dashboard/social',
    icon: Share2,
  },
  {
    label: 'Comprar Creditos',
    href: '/pricing',
    icon: Coins,
  },
  {
    label: 'Configuracoes',
    href: '/dashboard/settings',
    icon: Settings,
  },
];

export default function DashboardSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 min-h-[calc(100vh-4rem)] bg-dark-800 border-r border-dark-600 p-4 hidden lg:block">
      <nav className="space-y-1">
        {menuItems.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/dashboard' && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-gray-400 hover:text-white hover:bg-dark-700'
              }`}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Help section */}
      <div className="mt-8 pt-8 border-t border-dark-600">
        <Link
          href="#"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-dark-700 transition-colors"
        >
          <HelpCircle className="w-5 h-5" />
          Ajuda
        </Link>
      </div>
    </aside>
  );
}
