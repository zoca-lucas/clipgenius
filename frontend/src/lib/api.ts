/**
 * ClipGenius - API Client
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface Project {
  id: number;
  youtube_url: string;
  youtube_id: string;
  title: string | null;
  duration: number | null;
  thumbnail_url: string | null;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  clips_count: number;
}

export interface Clip {
  id: number;
  project_id: number;
  start_time: number;
  end_time: number;
  duration: number | null;
  title: string | null;
  viral_score: number | null;
  score_justification: string | null;
  video_path: string | null;
  video_path_with_subtitles: string | null;
  subtitle_path: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  clips: Clip[];
}

export interface ProcessingStatus {
  project_id: number;
  status: string;
  progress: number;
  current_step: string;
  step_progress: string | null;
  eta_seconds: number | null;
  message: string;
}

// API Functions

export async function createProject(url: string): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create project');
  }

  return response.json();
}

export async function uploadVideo(file: File): Promise<Project> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/projects/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to upload video');
  }

  return response.json();
}

export async function getProjects(page = 1, perPage = 10): Promise<{
  items: Project[];
  total: number;
  page: number;
  per_page: number;
}> {
  const response = await fetch(
    `${API_BASE_URL}/projects?page=${page}&per_page=${perPage}`
  );

  if (!response.ok) {
    throw new Error('Failed to fetch projects');
  }

  return response.json();
}

export async function getProject(projectId: number): Promise<ProjectDetail> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch project');
  }

  return response.json();
}

export async function getProjectStatus(projectId: number): Promise<ProcessingStatus> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/status`);

  if (!response.ok) {
    throw new Error('Failed to fetch project status');
  }

  return response.json();
}

export async function deleteProject(projectId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete project');
  }
}

export async function getClips(projectId: number): Promise<{
  items: Clip[];
  total: number;
}> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/clips`);

  if (!response.ok) {
    throw new Error('Failed to fetch clips');
  }

  return response.json();
}

export async function deleteClip(clipId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/clips/${clipId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete clip');
  }
}

export function getClipDownloadUrl(clipId: number, withSubtitles = true): string {
  return `${API_BASE_URL}/clips/${clipId}/download?with_subtitles=${withSubtitles}`;
}

export function getClipVideoUrl(clip: Clip, withSubtitles = true): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || 'http://localhost:8000';
  const path = withSubtitles && clip.video_path_with_subtitles
    ? clip.video_path_with_subtitles
    : clip.video_path;

  if (!path) return '';

  // Extract filename from path
  const filename = path.split('/').pop();
  return `${baseUrl}/clips/${filename}`;
}

// Utility functions

export function formatDuration(seconds: number | null): string {
  if (!seconds) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function getScoreColor(score: number | null): string {
  if (!score) return 'bg-gray-600';
  if (score >= 8) return 'score-excellent';
  if (score >= 6) return 'score-good';
  if (score >= 4) return 'score-average';
  return 'score-low';
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'text-green-500';
    case 'error':
      return 'text-red-500';
    case 'pending':
      return 'text-gray-500';
    default:
      return 'text-yellow-500';
  }
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: 'Aguardando',
    downloading: 'Baixando',
    transcribing: 'Transcrevendo',
    analyzing: 'Analisando',
    cutting: 'Cortando',
    completed: 'Concluído',
    error: 'Erro',
  };
  return labels[status] || status;
}
