/**
 * ClipGenius - Editor API Client
 * Functions for the layer-based video editor
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// ============ Interfaces ============

export interface SubtitleWord {
  word: string;
  start: number;
  end: number;
}

export interface SubtitleEntry {
  id: string;
  start: number;
  end: number;
  text: string;
  words?: SubtitleWord[];
}

export type AnimationIn = 'none' | 'bounce' | 'zoomIn' | 'slideLeft' | 'slideUp' | 'fadeIn' | 'typewriter';
export type AnimationOut = 'none' | 'bounce' | 'zoomOut' | 'slideRight' | 'fadeOut';
export type AnimationLoop = 'none' | 'pulse' | 'shake' | 'float';

export interface SubtitleStyle {
  fontName: string;
  fontSize: number;
  primaryColor: string;
  highlightColor: string;
  outlineColor: string;
  outlineSize: number;
  shadowSize: number;
  marginV: number;
  karaokeEnabled: boolean;
  scaleEffect: boolean;
  animationIn: AnimationIn;
  animationOut: AnimationOut;
  animationLoop: AnimationLoop;
  uppercase?: boolean;
  backgroundEnabled?: boolean;
  backgroundColor?: string;
}

export interface Track {
  id: string;
  type: 'video' | 'audio' | 'subtitle' | 'text';
  name: string;
  visible: boolean;
  locked: boolean;
  items: TrackItem[];
}

export interface TrackItem {
  id: string;
  start: number;
  end: number;
  data: SubtitleEntry | TextOverlay | AudioClip;
}

export interface TextOverlay {
  type: 'text';
  text: string;
  style: Partial<SubtitleStyle>;
  position: { x: number; y: number };
}

export interface AudioClip {
  type: 'audio';
  name: string;
  volume: number;
}

export interface ClipEditorData {
  clip_id: number;
  video_url: string;
  video_path: string;
  duration: number;
  title: string | null;
  subtitle_data: SubtitleEntry[];
  subtitle_file: string | null;
  has_burned_subtitles: boolean;
  default_style: {
    font_name: string;
    font_size: number;
    primary_color: string;
    highlight_color: string;
    outline_color: string;
    outline_size: number;
    shadow_size: number;
    margin_v: number;
    karaoke_enabled: boolean;
    scale_effect: boolean;
  };
}

export interface Layer {
  id: string;
  name: string;
  type: 'video' | 'subtitle' | 'text';
  visible: boolean;
  locked: boolean;
}

export interface ExportOptions {
  includeSubtitles: boolean;
  subtitleStyle?: SubtitleStyle;
  formatId: string;
}

export interface ExportResult {
  success: boolean;
  video_path: string;
  download_url: string;
  message: string;
  has_subtitles: boolean;
  format_id: string;
}

// ============ Helper Functions ============

/**
 * Convert frontend SubtitleStyle to backend format
 */
function styleToBackend(style: SubtitleStyle) {
  return {
    font_name: style.fontName,
    font_size: style.fontSize,
    primary_color: style.primaryColor,
    highlight_color: style.highlightColor,
    outline_color: style.outlineColor,
    outline_size: style.outlineSize,
    shadow_size: style.shadowSize,
    margin_v: style.marginV,
    karaoke_enabled: style.karaokeEnabled,
    scale_effect: style.scaleEffect,
    animation_in: style.animationIn,
    animation_out: style.animationOut,
    animation_loop: style.animationLoop,
    uppercase: style.uppercase,
    background_enabled: style.backgroundEnabled,
    background_color: style.backgroundColor,
  };
}

/**
 * Convert backend style to frontend SubtitleStyle
 */
export function styleFromBackend(backendStyle: ClipEditorData['default_style']): SubtitleStyle {
  const defaults = getDefaultSubtitleStyle();
  return {
    fontName: backendStyle.font_name,
    fontSize: backendStyle.font_size,
    primaryColor: backendStyle.primary_color,
    highlightColor: backendStyle.highlight_color,
    outlineColor: backendStyle.outline_color,
    outlineSize: backendStyle.outline_size,
    shadowSize: backendStyle.shadow_size,
    marginV: backendStyle.margin_v,
    karaokeEnabled: backendStyle.karaoke_enabled,
    scaleEffect: backendStyle.scale_effect,
    animationIn: (backendStyle as Record<string, unknown>).animation_in as AnimationIn || defaults.animationIn,
    animationOut: (backendStyle as Record<string, unknown>).animation_out as AnimationOut || defaults.animationOut,
    animationLoop: (backendStyle as Record<string, unknown>).animation_loop as AnimationLoop || defaults.animationLoop,
    uppercase: (backendStyle as Record<string, unknown>).uppercase as boolean || defaults.uppercase,
    backgroundEnabled: (backendStyle as Record<string, unknown>).background_enabled as boolean || defaults.backgroundEnabled,
    backgroundColor: (backendStyle as Record<string, unknown>).background_color as string || defaults.backgroundColor,
  };
}

/**
 * Get default subtitle style
 */
export function getDefaultSubtitleStyle(): SubtitleStyle {
  return {
    fontName: 'Arial',
    fontSize: 42,
    primaryColor: '#FFFFFF',
    highlightColor: '#FFFF00',
    outlineColor: '#000000',
    outlineSize: 3,
    shadowSize: 2,
    marginV: 80,
    karaokeEnabled: true,
    scaleEffect: true,
    animationIn: 'none',
    animationOut: 'none',
    animationLoop: 'none',
    uppercase: false,
    backgroundEnabled: false,
    backgroundColor: 'rgba(0,0,0,0.5)',
  };
}

/**
 * Convert ASS color format to hex
 * ASS format: &H00BBGGRR or &HBBGGRR
 */
export function assColorToHex(assColor: string): string {
  // Remove &H prefix
  let color = assColor.replace(/^&H/i, '');

  // Pad to 8 characters if needed
  while (color.length < 6) {
    color = '0' + color;
  }

  // ASS is in BBGGRR format, convert to RRGGBB
  if (color.length >= 6) {
    const bb = color.slice(-6, -4);
    const gg = color.slice(-4, -2);
    const rr = color.slice(-2);
    return `#${rr}${gg}${bb}`.toUpperCase();
  }

  return '#FFFFFF';
}

/**
 * Convert hex color to ASS format
 * Hex format: #RRGGBB
 * ASS format: &H00BBGGRR
 */
export function hexToAssColor(hex: string): string {
  // Remove # prefix
  let color = hex.replace(/^#/, '');

  if (color.length === 3) {
    color = color.split('').map(c => c + c).join('');
  }

  if (color.length === 6) {
    const rr = color.slice(0, 2);
    const gg = color.slice(2, 4);
    const bb = color.slice(4, 6);
    return `&H00${bb}${gg}${rr}`.toUpperCase();
  }

  return '&H00FFFFFF';
}

// ============ API Functions ============

/**
 * Get clip data for the editor (video + subtitles)
 */
export async function getClipEditorData(clipId: number): Promise<ClipEditorData> {
  const response = await fetch(`${API_BASE_URL}/editor/clips/${clipId}/editor-data`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Failed to get editor data: ${response.status}`);
  }

  return response.json();
}

/**
 * Update subtitles from the editor
 */
export async function updateSubtitles(
  clipId: number,
  subtitles: SubtitleEntry[],
  style?: SubtitleStyle
): Promise<{ success: boolean; message: string; subtitle_file: string }> {
  const body: Record<string, unknown> = {
    subtitles: subtitles,
  };

  if (style) {
    body.style = styleToBackend(style);
  }

  const response = await fetch(`${API_BASE_URL}/editor/clips/${clipId}/editor-subtitles`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Failed to update subtitles: ${response.status}`);
  }

  return response.json();
}

/**
 * Export clip with subtitle options
 */
export async function exportClip(
  clipId: number,
  options: ExportOptions
): Promise<ExportResult> {
  const body: Record<string, unknown> = {
    include_subtitles: options.includeSubtitles,
    format_id: options.formatId,
  };

  if (options.subtitleStyle) {
    body.subtitle_style = styleToBackend(options.subtitleStyle);
  }

  const response = await fetch(`${API_BASE_URL}/editor/clips/${clipId}/export-with-subtitles`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Failed to export clip: ${response.status}`);
  }

  return response.json();
}

/**
 * Download the .ass subtitle file
 */
export async function downloadSubtitleFile(clipId: number): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/editor/clips/${clipId}/subtitle-file`);

  if (!response.ok) {
    throw new Error(`Failed to download subtitle file: ${response.status}`);
  }

  return response.blob();
}

/**
 * Get the full video URL for a clip (for editor preview)
 */
export function getEditorVideoUrl(clipEditorData: ClipEditorData): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || 'http://localhost:8000';
  return `${baseUrl}${clipEditorData.video_url}`;
}

/**
 * Get the full download URL for an exported clip
 */
export function getExportDownloadUrl(exportResult: ExportResult): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || 'http://localhost:8000';
  return `${baseUrl}${exportResult.download_url}`;
}

/**
 * Create default layers for the editor
 */
export function createDefaultLayers(): Layer[] {
  return [
    {
      id: 'video',
      name: 'Video',
      type: 'video',
      visible: true,
      locked: false,
    },
    {
      id: 'subtitle',
      name: 'Legendas',
      type: 'subtitle',
      visible: true,
      locked: false,
    },
    {
      id: 'text',
      name: 'Textos',
      type: 'text',
      visible: true,
      locked: false,
    },
  ];
}

// ============ Bulk Operations ============

export interface BulkExportOptions {
  clipIds: number[];
  formatId: string;
  includeSubtitles: boolean;
  subtitleStyle?: SubtitleStyle;
}

export interface BulkOperationResult {
  success: boolean;
  total: number;
  processed: number;
  failed: number;
  results: Array<{
    clip_id: number;
    success: boolean;
    download_url?: string;
    error?: string;
  }>;
  message: string;
}

/**
 * Bulk export multiple clips
 */
export async function bulkExportClips(options: BulkExportOptions): Promise<BulkOperationResult> {
  const body: Record<string, unknown> = {
    clip_ids: options.clipIds,
    format_id: options.formatId,
    include_subtitles: options.includeSubtitles,
  };

  if (options.subtitleStyle) {
    body.subtitle_style = styleToBackend(options.subtitleStyle);
  }

  const response = await fetch(`${API_BASE_URL}/editor/clips/bulk-export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Bulk export failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Bulk delete multiple clips
 */
export async function bulkDeleteClips(clipIds: number[]): Promise<BulkOperationResult> {
  const response = await fetch(`${API_BASE_URL}/editor/clips/bulk-delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clip_ids: clipIds }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Bulk delete failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Bulk apply subtitle style to multiple clips
 */
export async function bulkApplyStyle(
  clipIds: number[],
  style: SubtitleStyle
): Promise<BulkOperationResult> {
  const response = await fetch(`${API_BASE_URL}/editor/clips/bulk-apply-style`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      clip_ids: clipIds,
      subtitle_style: styleToBackend(style),
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Bulk apply style failed: ${response.status}`);
  }

  return response.json();
}
