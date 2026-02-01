/**
 * ClipGenius - API Client
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Validation helpers
function isValidProject(data: unknown): data is Project {
  if (!data || typeof data !== 'object') return false;
  const obj = data as Record<string, unknown>;
  return (
    typeof obj.id === 'number' &&
    typeof obj.youtube_url === 'string' &&
    typeof obj.youtube_id === 'string' &&
    typeof obj.status === 'string'
  );
}

function isValidClip(data: unknown): data is Clip {
  if (!data || typeof data !== 'object') return false;
  const obj = data as Record<string, unknown>;
  return (
    typeof obj.id === 'number' &&
    typeof obj.project_id === 'number' &&
    typeof obj.start_time === 'number' &&
    typeof obj.end_time === 'number'
    // Note: has_burned_subtitles may be undefined for backwards compatibility
  );
}

function isValidProcessingStatus(data: unknown): data is ProcessingStatus {
  if (!data || typeof data !== 'object') return false;
  const obj = data as Record<string, unknown>;
  return (
    typeof obj.project_id === 'number' &&
    typeof obj.status === 'string' &&
    typeof obj.progress === 'number'
  );
}

async function handleResponse<T>(
  response: Response,
  validator?: (data: unknown) => data is T
): Promise<T> {
  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    try {
      const error = await response.json();
      errorMessage = error.detail || error.message || errorMessage;
    } catch {
      // Response is not JSON, use default message
    }
    throw new Error(errorMessage);
  }

  const data = await response.json();

  if (validator && !validator(data)) {
    console.warn('API response validation failed:', data);
    // Don't throw, just warn - the API might have added new fields
  }

  return data as T;
}

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
  subtitle_data: Array<{
    id: string;
    start: number;
    end: number;
    text: string;
    words?: Array<{ word: string; start: number; end: number }>;
  }> | null;
  subtitle_file: string | null;
  has_burned_subtitles: boolean;
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

  return handleResponse(response, isValidProject);
}

export async function uploadVideo(
  file: File,
  onProgress?: (progress: number) => void
): Promise<Project> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();

    // Track upload progress
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = Math.round((event.loaded / event.total) * 100);
        onProgress(progress);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch {
          reject(new Error('Invalid response from server'));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || 'Failed to upload video'));
        } catch {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Network error during upload'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload was cancelled'));
    });

    xhr.open('POST', `${API_BASE_URL}/projects/upload`);
    xhr.send(formData);
  });
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

  return handleResponse(response);
}

export async function getProject(projectId: number): Promise<ProjectDetail> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);
  return handleResponse(response);
}

export async function getProjectStatus(projectId: number): Promise<ProcessingStatus> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/status`);
  return handleResponse(response, isValidProcessingStatus);
}

export async function deleteProject(projectId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    await handleResponse(response);
  }
}

export async function reprocessProject(projectId: number): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/reprocess`, {
    method: 'POST',
  });

  return handleResponse(response, isValidProject);
}

export async function getClips(projectId: number): Promise<{
  items: Clip[];
  total: number;
}> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/clips`);
  return handleResponse(response);
}

export async function deleteClip(clipId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/clips/${clipId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    await handleResponse(response);
  }
}

export async function updateClipTitle(clipId: number, title: string): Promise<Clip> {
  const response = await fetch(`${API_BASE_URL}/clips/${clipId}/title`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title }),
  });

  return handleResponse(response, isValidClip);
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
    completed: 'Concluido',
    error: 'Erro',
  };
  return labels[status] || status;
}
