'use client';

import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import { ReactNode } from 'react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  color?: 'blue' | 'green' | 'yellow' | 'orange' | 'purple' | 'pink';
  link?: string;
  linkText?: string;
  change?: {
    value: number;
    label: string;
  };
}

const colorClasses = {
  blue: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    iconBg: 'bg-blue-500/20',
  },
  green: {
    bg: 'bg-green-500/10',
    text: 'text-green-400',
    iconBg: 'bg-green-500/20',
  },
  yellow: {
    bg: 'bg-yellow-500/10',
    text: 'text-yellow-400',
    iconBg: 'bg-yellow-500/20',
  },
  orange: {
    bg: 'bg-orange-500/10',
    text: 'text-orange-400',
    iconBg: 'bg-orange-500/20',
  },
  purple: {
    bg: 'bg-purple-500/10',
    text: 'text-purple-400',
    iconBg: 'bg-purple-500/20',
  },
  pink: {
    bg: 'bg-pink-500/10',
    text: 'text-pink-400',
    iconBg: 'bg-pink-500/20',
  },
};

export default function StatsCard({
  title,
  value,
  icon,
  color = 'blue',
  link,
  linkText,
  change,
}: StatsCardProps) {
  const colors = colorClasses[color];

  const content = (
    <div className={`bg-dark-800 border border-dark-600 rounded-xl p-5 ${link ? 'hover:border-dark-500 transition-colors' : ''}`}>
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-lg ${colors.iconBg} flex items-center justify-center ${colors.text}`}>
          {icon}
        </div>
        {link && (
          <ChevronRight className="w-4 h-4 text-gray-500" />
        )}
      </div>

      <div>
        <p className="text-2xl font-bold text-white mb-1">{value}</p>
        <p className="text-sm text-gray-400">{title}</p>
      </div>

      {change && (
        <div className="mt-3 flex items-center gap-1">
          <span className={change.value >= 0 ? 'text-green-400' : 'text-red-400'}>
            {change.value >= 0 ? '+' : ''}{change.value}%
          </span>
          <span className="text-xs text-gray-500">{change.label}</span>
        </div>
      )}

      {linkText && (
        <p className={`mt-3 text-sm ${colors.text}`}>{linkText}</p>
      )}
    </div>
  );

  if (link) {
    return <Link href={link}>{content}</Link>;
  }

  return content;
}
