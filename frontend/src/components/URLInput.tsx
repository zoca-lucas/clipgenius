'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Link2, Loader2, Sparkles, Upload, FileVideo } from 'lucide-react';
import { createProject, uploadVideo } from '@/lib/api';

type InputMode = 'url' | 'upload';

export default function URLInput() {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<InputMode>('url');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (mode === 'url') {
      if (!url.trim()) {
        setError('Por favor, cole um link do YouTube');
        return;
      }

      // Basic YouTube URL validation
      const youtubeRegex = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/;
      if (!youtubeRegex.test(url)) {
        setError('Link do YouTube inválido');
        return;
      }

      setIsLoading(true);

      try {
        const project = await createProject(url);
        router.push(`/projects/${project.id}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro ao criar projeto');
      } finally {
        setIsLoading(false);
      }
    } else {
      // Upload mode
      if (!selectedFile) {
        setError('Por favor, selecione um arquivo de vídeo');
        return;
      }

      setIsLoading(true);
      setUploadProgress(0);

      try {
        const project = await uploadVideo(selectedFile, (progress) => {
          setUploadProgress(progress);
        });
        router.push(`/projects/${project.id}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro ao fazer upload');
      } finally {
        setIsLoading(false);
        setUploadProgress(0);
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm'];
      if (!allowedTypes.includes(file.type)) {
        setError('Tipo de arquivo inválido. Use MP4, MOV, AVI, MKV ou WebM');
        return;
      }

      // Validate file size (500MB)
      if (file.size > 500 * 1024 * 1024) {
        setError('Arquivo muito grande. Máximo: 500MB');
        return;
      }

      setSelectedFile(file);
      setError('');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Mode Toggle */}
      <div className="flex justify-center gap-2 mb-6">
        <button
          type="button"
          onClick={() => { setMode('url'); setError(''); }}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
            mode === 'url'
              ? 'bg-primary text-white'
              : 'bg-dark-700 text-gray-400 hover:text-white'
          }`}
        >
          <Link2 className="w-4 h-4" />
          Link do YouTube
        </button>
        <button
          type="button"
          onClick={() => { setMode('upload'); setError(''); }}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
            mode === 'upload'
              ? 'bg-primary text-white'
              : 'bg-dark-700 text-gray-400 hover:text-white'
          }`}
        >
          <Upload className="w-4 h-4" />
          Upload de Vídeo
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        {mode === 'url' ? (
          /* URL Input */
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Link2 className="w-5 h-5 text-gray-500" />
            </div>

            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Cole o link do YouTube aqui..."
              className="w-full pl-12 pr-40 py-4 bg-dark-700 border border-dark-600 rounded-xl text-white placeholder-gray-500 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
              disabled={isLoading}
            />

            <button
              type="submit"
              disabled={isLoading}
              className="absolute inset-y-2 right-2 px-6 bg-primary hover:bg-primary/80 disabled:bg-primary/50 text-white font-medium rounded-lg flex items-center gap-2 transition-colors"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processando
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Gerar Cortes
                </>
              )}
            </button>
          </div>
        ) : (
          /* File Upload */
          <div className="space-y-4">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska,video/webm"
              className="hidden"
            />

            <div
              onClick={() => !isLoading && fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                selectedFile
                  ? 'border-primary bg-primary/10'
                  : 'border-dark-600 hover:border-primary/50 bg-dark-700'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {selectedFile ? (
                <div className="flex items-center justify-center gap-3">
                  <FileVideo className="w-8 h-8 text-primary" />
                  <div className="text-left">
                    <p className="text-white font-medium">{selectedFile.name}</p>
                    <p className="text-gray-400 text-sm">{formatFileSize(selectedFile.size)}</p>
                  </div>
                </div>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-gray-500 mx-auto mb-3" />
                  <p className="text-white font-medium">Clique para selecionar ou arraste um vídeo</p>
                  <p className="text-gray-500 text-sm mt-1">MP4, MOV, AVI, MKV, WebM (máx. 500MB)</p>
                </>
              )}
            </div>

            {selectedFile && (
              <div className="space-y-2">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-4 bg-primary hover:bg-primary/80 disabled:bg-primary/50 text-white font-medium rounded-xl flex items-center justify-center gap-2 transition-colors"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      {uploadProgress < 100 ? `Enviando... ${uploadProgress}%` : 'Processando...'}
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      Gerar Cortes
                    </>
                  )}
                </button>
                {isLoading && uploadProgress > 0 && uploadProgress < 100 && (
                  <div className="w-full bg-dark-600 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {error && (
          <p className="mt-3 text-red-400 text-sm text-center">{error}</p>
        )}
      </form>

      <p className="text-center text-gray-500 text-sm mt-4">
        {mode === 'url'
          ? 'Cole um link do YouTube e a IA vai gerar automaticamente 15 cortes virais'
          : 'Faça upload de um vídeo local e a IA vai gerar automaticamente 15 cortes virais'}
      </p>
    </div>
  );
}
