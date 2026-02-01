'use client';

import { useState, useEffect } from 'react';
import { Sparkles, Check } from 'lucide-react';

interface Filter {
  id: string;
  name: string;
  description: string;
}

interface FilterSelectorProps {
  selectedFilter: string;
  onFilterChange: (filterId: string) => void;
}

const DEFAULT_FILTERS: Filter[] = [
  { id: 'none', name: 'Original', description: 'Sem filtro aplicado' },
  { id: 'grayscale', name: 'Preto e Branco', description: 'Converte para escala de cinza' },
  { id: 'sepia', name: 'Sepia', description: 'Tom vintage amarronzado' },
  { id: 'warm', name: 'Quente', description: 'Tons mais quentes e aconchegantes' },
  { id: 'cool', name: 'Frio', description: 'Tons azulados e frios' },
  { id: 'vibrant', name: 'Vibrante', description: 'Cores mais saturadas' },
  { id: 'muted', name: 'Suave', description: 'Cores mais suaves' },
  { id: 'bright', name: 'Claro', description: 'Aumenta o brilho' },
  { id: 'dark', name: 'Escuro', description: 'Diminui o brilho' },
  { id: 'contrast', name: 'Contraste', description: 'Aumenta o contraste' },
  { id: 'vintage', name: 'Vintage', description: 'Efeito retro' },
  { id: 'sharpen', name: 'Nitidez', description: 'Aumenta a nitidez' },
];

export default function FilterSelector({
  selectedFilter,
  onFilterChange,
}: FilterSelectorProps) {
  const [filters, setFilters] = useState<Filter[]>(DEFAULT_FILTERS);

  useEffect(() => {
    // Fetch filters from API
    const fetchFilters = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
        const response = await fetch(`${baseUrl}/editor/filters`);
        if (response.ok) {
          const data = await response.json();
          setFilters(data);
        }
      } catch (error) {
        console.error('Failed to fetch filters:', error);
        // Keep default filters
      }
    };

    fetchFilters();
  }, []);

  return (
    <div className="bg-dark-800 rounded-lg p-4 space-y-4">
      <h3 className="font-medium flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-primary" />
        Filtros
      </h3>

      <div className="grid grid-cols-3 gap-2">
        {filters.map((filter) => (
          <button
            key={filter.id}
            onClick={() => onFilterChange(filter.id)}
            className={`relative p-3 rounded-lg border transition-all text-left ${
              selectedFilter === filter.id
                ? 'bg-primary/20 border-primary'
                : 'bg-dark-700 border-dark-600 hover:border-dark-500'
            }`}
          >
            {selectedFilter === filter.id && (
              <div className="absolute top-2 right-2">
                <Check className="w-4 h-4 text-primary" />
              </div>
            )}
            <p className="font-medium text-sm">{filter.name}</p>
            <p className="text-xs text-gray-500 mt-1 line-clamp-1">
              {filter.description}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
