/**
 * ClipGenius - Editor Store (Zustand)
 * Centralized state management for the video editor
 */
import { create } from 'zustand';
import { SubtitleEntry, SubtitleStyle, getDefaultSubtitleStyle } from '@/lib/editorApi';

// ============ Types ============

export type EditorMode = 'edit' | 'preview' | 'export';
export type ToolType = 'select' | 'trim' | 'text' | 'subtitle';
export type PanelType = 'style' | 'effects' | 'brandkit' | 'export' | null;

export interface TextOverlay {
  id: string;
  text: string;
  x: number;
  y: number;
  style: Partial<SubtitleStyle>;
  startTime: number;
  endTime: number;
}

export interface VideoFilter {
  id: string;
  name: string;
  cssFilter: string;
  enabled: boolean;
}

export interface AudioSettings {
  volume: number;
  muted: boolean;
  fadeIn: number;
  fadeOut: number;
}

export interface EditorState {
  // Video state
  videoUrl: string | null;
  videoPath: string | null;
  duration: number;
  currentTime: number;
  isPlaying: boolean;
  playbackRate: number;

  // Trim state
  trimStart: number;
  trimEnd: number;

  // Subtitles
  subtitles: SubtitleEntry[];
  selectedSubtitleId: string | null;
  subtitleStyle: SubtitleStyle;

  // Text overlays
  textOverlays: TextOverlay[];
  selectedTextId: string | null;

  // Filters & effects
  filters: VideoFilter[];
  brightness: number;
  contrast: number;
  saturation: number;

  // Audio
  audio: AudioSettings;

  // UI State
  mode: EditorMode;
  activeTool: ToolType;
  activePanel: PanelType;
  zoom: number;

  // History for undo/redo
  history: EditorHistoryEntry[];
  historyIndex: number;

  // Flags
  hasChanges: boolean;
  isLoading: boolean;
  isSaving: boolean;
  isExporting: boolean;
}

export interface EditorHistoryEntry {
  subtitles: SubtitleEntry[];
  textOverlays: TextOverlay[];
  trimStart: number;
  trimEnd: number;
  timestamp: number;
}

export interface EditorActions {
  // Video actions
  setVideoUrl: (url: string) => void;
  setVideoPath: (path: string) => void;
  setDuration: (duration: number) => void;
  setCurrentTime: (time: number) => void;
  setIsPlaying: (playing: boolean) => void;
  setPlaybackRate: (rate: number) => void;
  play: () => void;
  pause: () => void;
  seek: (time: number) => void;

  // Trim actions
  setTrimStart: (time: number) => void;
  setTrimEnd: (time: number) => void;
  setTrim: (start: number, end: number) => void;

  // Subtitle actions
  setSubtitles: (subtitles: SubtitleEntry[]) => void;
  addSubtitle: (subtitle: SubtitleEntry) => void;
  updateSubtitle: (id: string, updates: Partial<SubtitleEntry>) => void;
  removeSubtitle: (id: string) => void;
  selectSubtitle: (id: string | null) => void;
  setSubtitleStyle: (style: SubtitleStyle) => void;
  updateSubtitleStyle: (updates: Partial<SubtitleStyle>) => void;

  // Text overlay actions
  addTextOverlay: (overlay: TextOverlay) => void;
  updateTextOverlay: (id: string, updates: Partial<TextOverlay>) => void;
  removeTextOverlay: (id: string) => void;
  selectText: (id: string | null) => void;

  // Filter actions
  setFilter: (id: string, enabled: boolean) => void;
  setBrightness: (value: number) => void;
  setContrast: (value: number) => void;
  setSaturation: (value: number) => void;

  // Audio actions
  setVolume: (volume: number) => void;
  setMuted: (muted: boolean) => void;
  setAudioFade: (fadeIn: number, fadeOut: number) => void;

  // UI actions
  setMode: (mode: EditorMode) => void;
  setActiveTool: (tool: ToolType) => void;
  setActivePanel: (panel: PanelType) => void;
  togglePanel: (panel: PanelType) => void;
  setZoom: (zoom: number) => void;

  // History actions
  undo: () => void;
  redo: () => void;
  saveToHistory: () => void;

  // Loading states
  setIsLoading: (loading: boolean) => void;
  setIsSaving: (saving: boolean) => void;
  setIsExporting: (exporting: boolean) => void;
  setHasChanges: (hasChanges: boolean) => void;

  // Reset
  reset: () => void;
  loadEditorData: (data: {
    videoUrl: string;
    videoPath: string;
    duration: number;
    subtitles: SubtitleEntry[];
    style: SubtitleStyle;
  }) => void;
}

// ============ Initial State ============

const DEFAULT_FILTERS: VideoFilter[] = [
  { id: 'grayscale', name: 'Preto e Branco', cssFilter: 'grayscale(100%)', enabled: false },
  { id: 'sepia', name: 'Sepia', cssFilter: 'sepia(100%)', enabled: false },
  { id: 'vintage', name: 'Vintage', cssFilter: 'sepia(30%) contrast(110%) saturate(130%)', enabled: false },
  { id: 'cool', name: 'Frio', cssFilter: 'saturate(80%) hue-rotate(20deg)', enabled: false },
  { id: 'warm', name: 'Quente', cssFilter: 'saturate(120%) hue-rotate(-10deg)', enabled: false },
  { id: 'dramatic', name: 'Dramatico', cssFilter: 'contrast(130%) saturate(110%)', enabled: false },
];

const initialState: EditorState = {
  videoUrl: null,
  videoPath: null,
  duration: 0,
  currentTime: 0,
  isPlaying: false,
  playbackRate: 1,

  trimStart: 0,
  trimEnd: 0,

  subtitles: [],
  selectedSubtitleId: null,
  subtitleStyle: getDefaultSubtitleStyle(),

  textOverlays: [],
  selectedTextId: null,

  filters: DEFAULT_FILTERS,
  brightness: 100,
  contrast: 100,
  saturation: 100,

  audio: {
    volume: 100,
    muted: false,
    fadeIn: 0,
    fadeOut: 0,
  },

  mode: 'edit',
  activeTool: 'select',
  activePanel: null,
  zoom: 1,

  history: [],
  historyIndex: -1,

  hasChanges: false,
  isLoading: false,
  isSaving: false,
  isExporting: false,
};

// ============ Store ============

export const useEditorStore = create<EditorState & EditorActions>((set, get) => ({
  ...initialState,

  // Video actions
  setVideoUrl: (url) => set({ videoUrl: url }),
  setVideoPath: (path) => set({ videoPath: path }),
  setDuration: (duration) => set({ duration, trimEnd: duration }),
  setCurrentTime: (time) => set({ currentTime: time }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setPlaybackRate: (rate) => set({ playbackRate: rate }),

  play: () => set({ isPlaying: true }),
  pause: () => set({ isPlaying: false }),
  seek: (time) => set({ currentTime: Math.max(0, Math.min(time, get().duration)) }),

  // Trim actions
  setTrimStart: (time) => {
    const { trimEnd, duration } = get();
    set({
      trimStart: Math.max(0, Math.min(time, trimEnd - 0.5)),
      hasChanges: true
    });
  },

  setTrimEnd: (time) => {
    const { trimStart, duration } = get();
    set({
      trimEnd: Math.min(duration, Math.max(time, trimStart + 0.5)),
      hasChanges: true
    });
  },

  setTrim: (start, end) => {
    set({ trimStart: start, trimEnd: end, hasChanges: true });
  },

  // Subtitle actions
  setSubtitles: (subtitles) => set({ subtitles, hasChanges: true }),

  addSubtitle: (subtitle) => {
    const { subtitles } = get();
    set({
      subtitles: [...subtitles, subtitle],
      hasChanges: true
    });
    get().saveToHistory();
  },

  updateSubtitle: (id, updates) => {
    const { subtitles } = get();
    set({
      subtitles: subtitles.map((s) =>
        s.id === id ? { ...s, ...updates } : s
      ),
      hasChanges: true,
    });
  },

  removeSubtitle: (id) => {
    const { subtitles, selectedSubtitleId } = get();
    set({
      subtitles: subtitles.filter((s) => s.id !== id),
      selectedSubtitleId: selectedSubtitleId === id ? null : selectedSubtitleId,
      hasChanges: true,
    });
    get().saveToHistory();
  },

  selectSubtitle: (id) => set({ selectedSubtitleId: id }),

  setSubtitleStyle: (style) => set({ subtitleStyle: style, hasChanges: true }),

  updateSubtitleStyle: (updates) => {
    const { subtitleStyle } = get();
    set({
      subtitleStyle: { ...subtitleStyle, ...updates },
      hasChanges: true
    });
  },

  // Text overlay actions
  addTextOverlay: (overlay) => {
    const { textOverlays } = get();
    set({
      textOverlays: [...textOverlays, overlay],
      hasChanges: true
    });
    get().saveToHistory();
  },

  updateTextOverlay: (id, updates) => {
    const { textOverlays } = get();
    set({
      textOverlays: textOverlays.map((t) =>
        t.id === id ? { ...t, ...updates } : t
      ),
      hasChanges: true,
    });
  },

  removeTextOverlay: (id) => {
    const { textOverlays, selectedTextId } = get();
    set({
      textOverlays: textOverlays.filter((t) => t.id !== id),
      selectedTextId: selectedTextId === id ? null : selectedTextId,
      hasChanges: true,
    });
    get().saveToHistory();
  },

  selectText: (id) => set({ selectedTextId: id }),

  // Filter actions
  setFilter: (id, enabled) => {
    const { filters } = get();
    set({
      filters: filters.map((f) =>
        f.id === id ? { ...f, enabled } : f
      ),
      hasChanges: true,
    });
  },

  setBrightness: (value) => set({ brightness: value, hasChanges: true }),
  setContrast: (value) => set({ contrast: value, hasChanges: true }),
  setSaturation: (value) => set({ saturation: value, hasChanges: true }),

  // Audio actions
  setVolume: (volume) => set({ audio: { ...get().audio, volume } }),
  setMuted: (muted) => set({ audio: { ...get().audio, muted } }),
  setAudioFade: (fadeIn, fadeOut) => set({
    audio: { ...get().audio, fadeIn, fadeOut },
    hasChanges: true
  }),

  // UI actions
  setMode: (mode) => set({ mode }),
  setActiveTool: (tool) => set({ activeTool: tool }),
  setActivePanel: (panel) => set({ activePanel: panel }),
  togglePanel: (panel) => {
    const { activePanel } = get();
    set({ activePanel: activePanel === panel ? null : panel });
  },
  setZoom: (zoom) => set({ zoom: Math.max(0.5, Math.min(4, zoom)) }),

  // History actions
  undo: () => {
    const { history, historyIndex } = get();
    if (historyIndex > 0) {
      const prevState = history[historyIndex - 1];
      set({
        subtitles: prevState.subtitles,
        textOverlays: prevState.textOverlays,
        trimStart: prevState.trimStart,
        trimEnd: prevState.trimEnd,
        historyIndex: historyIndex - 1,
        hasChanges: true,
      });
    }
  },

  redo: () => {
    const { history, historyIndex } = get();
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1];
      set({
        subtitles: nextState.subtitles,
        textOverlays: nextState.textOverlays,
        trimStart: nextState.trimStart,
        trimEnd: nextState.trimEnd,
        historyIndex: historyIndex + 1,
        hasChanges: true,
      });
    }
  },

  saveToHistory: () => {
    const { subtitles, textOverlays, trimStart, trimEnd, history, historyIndex } = get();
    const newEntry: EditorHistoryEntry = {
      subtitles: [...subtitles],
      textOverlays: [...textOverlays],
      trimStart,
      trimEnd,
      timestamp: Date.now(),
    };

    // Remove future history if we're not at the end
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newEntry);

    // Limit history to 50 entries
    if (newHistory.length > 50) {
      newHistory.shift();
    }

    set({
      history: newHistory,
      historyIndex: newHistory.length - 1,
    });
  },

  // Loading states
  setIsLoading: (loading) => set({ isLoading: loading }),
  setIsSaving: (saving) => set({ isSaving: saving }),
  setIsExporting: (exporting) => set({ isExporting: exporting }),
  setHasChanges: (hasChanges) => set({ hasChanges }),

  // Reset
  reset: () => set(initialState),

  loadEditorData: (data) => {
    set({
      videoUrl: data.videoUrl,
      videoPath: data.videoPath,
      duration: data.duration,
      trimStart: 0,
      trimEnd: data.duration,
      subtitles: data.subtitles,
      subtitleStyle: data.style,
      hasChanges: false,
      isLoading: false,
    });
    get().saveToHistory();
  },
}));
