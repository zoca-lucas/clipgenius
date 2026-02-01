'use client';

import { Coins, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

interface CreditBalanceProps {
  showLink?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function CreditBalance({ showLink = true, size = 'md' }: CreditBalanceProps) {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return null;
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2',
  };

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  const content = (
    <div className={`flex items-center gap-1.5 bg-dark-700 border border-dark-600 rounded-lg ${sizeClasses[size]}`}>
      <Coins className={`${iconSizes[size]} text-yellow-500`} />
      <span className="font-medium text-white">{user.credits}</span>
      <span className="text-gray-400">creditos</span>
      {showLink && (
        <ChevronRight className={`${iconSizes[size]} text-gray-500`} />
      )}
    </div>
  );

  if (showLink) {
    return (
      <Link href="/pricing" className="hover:opacity-80 transition-opacity">
        {content}
      </Link>
    );
  }

  return content;
}
