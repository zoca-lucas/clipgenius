/**
 * ClipGenius - Brand Kit Store (Zustand)
 * Manages brand templates for consistent video styling
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { SubtitleStyle, getDefaultSubtitleStyle } from '@/lib/editorApi';

// ============ Types ============

export interface BrandKit {
  id: string;
  name: string;
  description?: string;
  createdAt: number;
  updatedAt: number;

  // Visual identity
  logo?: {
    url: string;
    position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
    size: number; // percentage of video width (5-30)
    opacity: number; // 0-100
    margin: number; // pixels from edge
  };

  // Subtitle style
  subtitleStyle: SubtitleStyle;

  // Color palette
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
  };

  // Intro/Outro
  intro?: {
    enabled: boolean;
    duration: number; // seconds
    text?: string;
    backgroundColor?: string;
  };

  outro?: {
    enabled: boolean;
    duration: number;
    text?: string;
    ctaText?: string;
    backgroundColor?: string;
  };

  // Watermark
  watermark?: {
    enabled: boolean;
    text: string;
    position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
    opacity: number;
    fontSize: number;
  };
}

export interface BrandKitState {
  // Brand kits
  brandKits: BrandKit[];
  activeBrandKitId: string | null;

  // UI state
  isEditing: boolean;
  editingKitId: string | null;
}

export interface BrandKitActions {
  // CRUD operations
  createBrandKit: (name: string, baseKit?: Partial<BrandKit>) => BrandKit;
  updateBrandKit: (id: string, updates: Partial<BrandKit>) => void;
  deleteBrandKit: (id: string) => void;
  duplicateBrandKit: (id: string, newName: string) => BrandKit | null;

  // Selection
  setActiveBrandKit: (id: string | null) => void;
  getActiveBrandKit: () => BrandKit | null;

  // UI
  startEditing: (id: string) => void;
  stopEditing: () => void;

  // Import/Export
  exportBrandKit: (id: string) => string | null;
  importBrandKit: (jsonString: string) => BrandKit | null;

  // Apply
  applyToSubtitleStyle: (brandKitId: string) => SubtitleStyle | null;
}

// ============ Default Brand Kits ============

const createDefaultBrandKits = (): BrandKit[] => {
  const now = Date.now();

  return [
    {
      id: 'default-viral',
      name: 'Viral Hormozi',
      description: 'Estilo viral inspirado em Alex Hormozi - alto impacto',
      createdAt: now,
      updatedAt: now,
      subtitleStyle: {
        ...getDefaultSubtitleStyle(),
        fontName: 'Impact',
        fontSize: 48,
        primaryColor: '#FFFFFF',
        highlightColor: '#FFFF00',
        outlineColor: '#000000',
        outlineSize: 4,
        shadowSize: 3,
        marginV: 100,
        karaokeEnabled: true,
        scaleEffect: true,
        uppercase: true,
      },
      colors: {
        primary: '#FFFF00',
        secondary: '#FFFFFF',
        accent: '#FF0000',
        background: '#000000',
      },
    },
    {
      id: 'default-clean',
      name: 'Clean Minimal',
      description: 'Estilo limpo e profissional',
      createdAt: now,
      updatedAt: now,
      subtitleStyle: {
        ...getDefaultSubtitleStyle(),
        fontName: 'Arial',
        fontSize: 36,
        primaryColor: '#FFFFFF',
        highlightColor: '#00FFFF',
        outlineColor: '#000000',
        outlineSize: 2,
        shadowSize: 1,
        marginV: 80,
        karaokeEnabled: false,
        scaleEffect: false,
        uppercase: false,
      },
      colors: {
        primary: '#00FFFF',
        secondary: '#FFFFFF',
        accent: '#0066FF',
        background: '#1A1A2E',
      },
    },
    {
      id: 'default-podcast',
      name: 'Podcast Style',
      description: 'Ideal para cortes de podcast',
      createdAt: now,
      updatedAt: now,
      subtitleStyle: {
        ...getDefaultSubtitleStyle(),
        fontName: 'Georgia',
        fontSize: 40,
        primaryColor: '#FFFFFF',
        highlightColor: '#FFA500',
        outlineColor: '#333333',
        outlineSize: 3,
        shadowSize: 2,
        marginV: 120,
        karaokeEnabled: true,
        scaleEffect: false,
        uppercase: false,
        backgroundEnabled: true,
        backgroundColor: 'rgba(0,0,0,0.6)',
      },
      colors: {
        primary: '#FFA500',
        secondary: '#FFFFFF',
        accent: '#FF6B00',
        background: '#2D2D2D',
      },
    },
    {
      id: 'default-gaming',
      name: 'Gaming',
      description: 'Estilo energetico para gaming',
      createdAt: now,
      updatedAt: now,
      subtitleStyle: {
        ...getDefaultSubtitleStyle(),
        fontName: 'Impact',
        fontSize: 44,
        primaryColor: '#00FF00',
        highlightColor: '#FF00FF',
        outlineColor: '#000000',
        outlineSize: 4,
        shadowSize: 3,
        marginV: 90,
        karaokeEnabled: true,
        scaleEffect: true,
        uppercase: true,
      },
      colors: {
        primary: '#00FF00',
        secondary: '#FF00FF',
        accent: '#00FFFF',
        background: '#0D0D0D',
      },
    },
  ];
};

// ============ Store ============

export const useBrandKitStore = create<BrandKitState & BrandKitActions>()(
  persist(
    (set, get) => ({
      // Initial state
      brandKits: createDefaultBrandKits(),
      activeBrandKitId: null,
      isEditing: false,
      editingKitId: null,

      // CRUD operations
      createBrandKit: (name, baseKit) => {
        const now = Date.now();
        const newKit: BrandKit = {
          id: `kit-${now}`,
          name,
          description: baseKit?.description || '',
          createdAt: now,
          updatedAt: now,
          subtitleStyle: baseKit?.subtitleStyle || getDefaultSubtitleStyle(),
          colors: baseKit?.colors || {
            primary: '#FFFF00',
            secondary: '#FFFFFF',
            accent: '#FF0000',
            background: '#000000',
          },
          logo: baseKit?.logo,
          intro: baseKit?.intro,
          outro: baseKit?.outro,
          watermark: baseKit?.watermark,
        };

        set((state) => ({
          brandKits: [...state.brandKits, newKit],
        }));

        return newKit;
      },

      updateBrandKit: (id, updates) => {
        set((state) => ({
          brandKits: state.brandKits.map((kit) =>
            kit.id === id
              ? { ...kit, ...updates, updatedAt: Date.now() }
              : kit
          ),
        }));
      },

      deleteBrandKit: (id) => {
        // Don't delete default kits
        if (id.startsWith('default-')) return;

        set((state) => ({
          brandKits: state.brandKits.filter((kit) => kit.id !== id),
          activeBrandKitId:
            state.activeBrandKitId === id ? null : state.activeBrandKitId,
          editingKitId: state.editingKitId === id ? null : state.editingKitId,
        }));
      },

      duplicateBrandKit: (id, newName) => {
        const { brandKits } = get();
        const original = brandKits.find((kit) => kit.id === id);
        if (!original) return null;

        const now = Date.now();
        const duplicated: BrandKit = {
          ...original,
          id: `kit-${now}`,
          name: newName,
          createdAt: now,
          updatedAt: now,
        };

        set((state) => ({
          brandKits: [...state.brandKits, duplicated],
        }));

        return duplicated;
      },

      // Selection
      setActiveBrandKit: (id) => set({ activeBrandKitId: id }),

      getActiveBrandKit: () => {
        const { brandKits, activeBrandKitId } = get();
        return brandKits.find((kit) => kit.id === activeBrandKitId) || null;
      },

      // UI
      startEditing: (id) => set({ isEditing: true, editingKitId: id }),
      stopEditing: () => set({ isEditing: false, editingKitId: null }),

      // Import/Export
      exportBrandKit: (id) => {
        const { brandKits } = get();
        const kit = brandKits.find((k) => k.id === id);
        if (!kit) return null;

        // Create export-safe version (without internal ids)
        const exportKit = {
          ...kit,
          id: undefined,
          createdAt: undefined,
          updatedAt: undefined,
        };

        return JSON.stringify(exportKit, null, 2);
      },

      importBrandKit: (jsonString) => {
        try {
          const imported = JSON.parse(jsonString);
          const now = Date.now();

          const newKit: BrandKit = {
            ...imported,
            id: `kit-${now}`,
            name: imported.name || 'Kit Importado',
            createdAt: now,
            updatedAt: now,
            subtitleStyle: imported.subtitleStyle || getDefaultSubtitleStyle(),
            colors: imported.colors || {
              primary: '#FFFF00',
              secondary: '#FFFFFF',
              accent: '#FF0000',
              background: '#000000',
            },
          };

          set((state) => ({
            brandKits: [...state.brandKits, newKit],
          }));

          return newKit;
        } catch {
          console.error('Failed to import brand kit');
          return null;
        }
      },

      // Apply
      applyToSubtitleStyle: (brandKitId) => {
        const { brandKits } = get();
        const kit = brandKits.find((k) => k.id === brandKitId);
        return kit?.subtitleStyle || null;
      },
    }),
    {
      name: 'clipgenius-brandkits',
      partialize: (state) => ({
        brandKits: state.brandKits,
        activeBrandKitId: state.activeBrandKitId,
      }),
    }
  )
);
