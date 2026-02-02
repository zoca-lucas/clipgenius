"""
ClipGenius - Transcription Service V2
Suporta múltiplos backends para timestamps precisos:
- WhisperX: Forced alignment com wav2vec2 (RECOMENDADO)
- stable-ts: Timestamps estabilizados
- faster-whisper: Rápido com timestamps nativos
- Groq API: Cloud API (fallback)
"""
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    AUDIO_DIR,
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    GROQ_API_KEY
)

# Importar novas API keys (com fallback para evitar erro se não existirem)
try:
    from config import DEEPGRAM_API_KEY, ASSEMBLYAI_API_KEY
except ImportError:
    DEEPGRAM_API_KEY = ""
    ASSEMBLYAI_API_KEY = ""


# Tipos de backend suportados
TranscriptionBackend = Literal["deepgram", "assemblyai", "whisperx", "stable-ts", "faster-whisper", "groq", "auto"]


class TranscriberV2:
    """
    Transcriber V2 com suporte a múltiplos backends para timestamps precisos.

    Backends disponíveis:
    - whisperx: Melhor precisão de timestamps (forced alignment wav2vec2)
    - stable-ts: Timestamps estabilizados, bom equilíbrio
    - faster-whisper: Rápido, timestamps nativos
    - groq: API cloud, rápido mas menos preciso
    - auto: Seleciona automaticamente o melhor disponível

    Ordem de prioridade (auto): whisperx > stable-ts > faster-whisper > groq
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
    GROQ_MODEL = "whisper-large-v3-turbo"

    def __init__(
        self,
        backend: TranscriptionBackend = "auto",
        model_size: str = None,
        device: str = "auto",
        compute_type: str = "auto"
    ):
        """
        Inicializa o transcriber.

        Args:
            backend: Backend a usar (whisperx, stable-ts, faster-whisper, groq, auto)
            model_size: Tamanho do modelo (tiny, base, small, medium, large-v2, large-v3)
            device: Dispositivo (cuda, cpu, auto)
            compute_type: Tipo de computação (float16, int8, auto)
        """
        self.model_size = model_size or WHISPER_MODEL
        self.device = device
        self.compute_type = compute_type
        self.audio_dir = AUDIO_DIR

        # Detectar backend disponível
        self.backend = self._resolve_backend(backend)
        self._model = None
        self._whisperx_model = None
        self._align_model = None

        print(f"TranscriberV2: Usando backend '{self.backend}' com modelo '{self.model_size}'")

    def _resolve_backend(self, backend: TranscriptionBackend) -> str:
        """Resolve o backend a usar baseado na disponibilidade."""
        if backend != "auto":
            # Verificar se o backend solicitado está disponível
            if self._check_backend_available(backend):
                return backend
            print(f"Backend '{backend}' não disponível, usando auto...")

        # Auto: tentar na ordem de prioridade
        # Deepgram/AssemblyAI primeiro (melhor qualidade), depois locais, depois Groq
        priority = ["deepgram", "assemblyai", "whisperx", "stable-ts", "faster-whisper", "groq"]

        for b in priority:
            if self._check_backend_available(b):
                return b

        raise RuntimeError("Nenhum backend de transcrição disponível!")

    def _check_backend_available(self, backend: str) -> bool:
        """Verifica se um backend está disponível."""
        try:
            if backend == "deepgram":
                return bool(DEEPGRAM_API_KEY)
            elif backend == "assemblyai":
                return bool(ASSEMBLYAI_API_KEY)
            elif backend == "whisperx":
                import whisperx
                # Testar import completo
                _ = whisperx.load_model
                return True
            elif backend == "stable-ts":
                import stable_whisper
                # Testar import completo
                _ = stable_whisper.load_model
                return True
            elif backend == "faster-whisper":
                from faster_whisper import WhisperModel
                return True
            elif backend == "groq":
                return bool(GROQ_API_KEY)
            elif backend == "groq-enhanced":
                # Groq com pós-processamento de timestamps
                return bool(GROQ_API_KEY)
        except (ImportError, AttributeError, Exception):
            pass
        return False

    def _get_device(self) -> str:
        """Detecta o dispositivo a usar."""
        if self.device != "auto":
            return self.device

        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    def _get_compute_type(self, device: str) -> str:
        """Detecta o tipo de computação ideal."""
        if self.compute_type != "auto":
            return self.compute_type

        if device == "cuda":
            return "float16"
        return "int8"

    # =========================================================================
    # WhisperX Backend - Melhor precisão de timestamps
    # =========================================================================

    def _load_whisperx(self):
        """Carrega modelo WhisperX."""
        if self._whisperx_model is None:
            import whisperx

            device = self._get_device()
            compute_type = self._get_compute_type(device)

            print(f"Carregando WhisperX ({self.model_size}) em {device}...")
            self._whisperx_model = whisperx.load_model(
                self.model_size,
                device=device,
                compute_type=compute_type
            )
        return self._whisperx_model

    def _load_whisperx_align_model(self, language: str):
        """Carrega modelo de alinhamento do WhisperX."""
        import whisperx

        device = self._get_device()

        # Carregar modelo de alinhamento para o idioma
        print(f"Carregando modelo de alinhamento para '{language}'...")
        model_a, metadata = whisperx.load_align_model(
            language_code=language,
            device=device
        )
        return model_a, metadata

    def _transcribe_whisperx(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcreve usando WhisperX com forced alignment.

        WhisperX usa wav2vec2 para alinhar timestamps ao nível de palavra,
        resultando em precisão muito superior ao Whisper padrão.
        """
        import whisperx

        device = self._get_device()

        # Carregar áudio
        audio = whisperx.load_audio(audio_path)

        # Transcrever
        model = self._load_whisperx()

        transcribe_options = {"language": language} if language else {}
        result = model.transcribe(audio, batch_size=16, **transcribe_options)

        # Detectar idioma se não especificado
        detected_language = result.get("language", language or "pt")

        # Alinhar timestamps ao nível de palavra
        try:
            model_a, metadata = self._load_whisperx_align_model(detected_language)
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                device,
                return_char_alignments=False
            )
        except Exception as e:
            print(f"Aviso: Alinhamento falhou ({e}), usando timestamps originais")

        # Formatar resultado
        return self._format_whisperx_result(result, detected_language)

    def _format_whisperx_result(self, result: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Formata resultado do WhisperX para o formato padrão."""
        segments = []
        all_words = []
        full_text = []

        for segment in result.get("segments", []):
            segment_data = {
                "id": len(segments),
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": segment.get("text", "").strip(),
                "words": []
            }

            # Processar palavras com timestamps
            for word in segment.get("words", []):
                word_data = {
                    "word": word.get("word", "").strip(),
                    "start": word.get("start", segment_data["start"]),
                    "end": word.get("end", segment_data["end"]),
                    "probability": word.get("score", 1.0)
                }
                segment_data["words"].append(word_data)
                all_words.append(word_data)

            segments.append(segment_data)
            full_text.append(segment_data["text"])

        return {
            "text": " ".join(full_text),
            "language": language,
            "duration": segments[-1]["end"] if segments else 0,
            "segments": segments,
            "words": all_words,
            "backend": "whisperx"
        }

    # =========================================================================
    # stable-ts Backend - Timestamps estabilizados
    # =========================================================================

    def _load_stable_ts(self):
        """Carrega modelo stable-ts."""
        if self._model is None:
            import stable_whisper

            print(f"Carregando stable-ts ({self.model_size})...")
            self._model = stable_whisper.load_model(self.model_size)
        return self._model

    def _transcribe_stable_ts(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcreve usando stable-ts com timestamps estabilizados.

        stable-ts modifica o Whisper para produzir timestamps mais confiáveis
        através de ajuste de gaps e supressão de silêncio.
        """
        model = self._load_stable_ts()

        # Transcrever com opções otimizadas
        result = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            vad=True,  # Voice Activity Detection
            regroup=True  # Reagrupar palavras para melhor segmentação
        )

        # Formatar resultado
        return self._format_stable_ts_result(result, language or "pt")

    def _format_stable_ts_result(self, result, language: str) -> Dict[str, Any]:
        """Formata resultado do stable-ts para o formato padrão."""
        segments = []
        all_words = []
        full_text = []

        for i, segment in enumerate(result.segments):
            segment_data = {
                "id": i,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "words": []
            }

            # Processar palavras
            for word in segment.words:
                word_data = {
                    "word": word.word.strip(),
                    "start": word.start,
                    "end": word.end,
                    "probability": getattr(word, "probability", 1.0)
                }
                segment_data["words"].append(word_data)
                all_words.append(word_data)

            segments.append(segment_data)
            full_text.append(segment_data["text"])

        return {
            "text": " ".join(full_text),
            "language": language,
            "duration": segments[-1]["end"] if segments else 0,
            "segments": segments,
            "words": all_words,
            "backend": "stable-ts"
        }

    # =========================================================================
    # faster-whisper Backend - Rápido com timestamps nativos
    # =========================================================================

    def _load_faster_whisper(self):
        """Carrega modelo faster-whisper."""
        if self._model is None:
            from faster_whisper import WhisperModel

            device = self._get_device()
            compute_type = self._get_compute_type(device)

            print(f"Carregando faster-whisper ({self.model_size}) em {device}...")
            self._model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type
            )
        return self._model

    def _transcribe_faster_whisper(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcreve usando faster-whisper com timestamps nativos.

        faster-whisper é 4x mais rápido que o Whisper original e usa menos memória.
        """
        model = self._load_faster_whisper()

        # Transcrever com word timestamps
        segments_gen, info = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=400
            )
        )

        # Formatar resultado
        return self._format_faster_whisper_result(segments_gen, info)

    def _format_faster_whisper_result(self, segments_gen, info) -> Dict[str, Any]:
        """Formata resultado do faster-whisper para o formato padrão."""
        segments = []
        all_words = []
        full_text = []

        for i, segment in enumerate(segments_gen):
            segment_data = {
                "id": i,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "words": []
            }

            # Processar palavras
            if segment.words:
                for word in segment.words:
                    word_data = {
                        "word": word.word.strip(),
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability
                    }
                    segment_data["words"].append(word_data)
                    all_words.append(word_data)

            segments.append(segment_data)
            full_text.append(segment_data["text"])

        return {
            "text": " ".join(full_text),
            "language": info.language,
            "duration": segments[-1]["end"] if segments else 0,
            "segments": segments,
            "words": all_words,
            "backend": "faster-whisper"
        }

    # =========================================================================
    # Groq API Backend - Cloud API (fallback)
    # =========================================================================

    def _transcribe_groq(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcreve usando Groq API (cloud).

        Rápido mas com timestamps menos precisos que backends locais.
        """
        import httpx

        # Verificar tamanho do arquivo
        file_size = Path(audio_path).stat().st_size
        max_size = 25 * 1024 * 1024  # 25MB

        if file_size > max_size:
            return self._transcribe_groq_chunked(audio_path, language)

        return self._groq_request(audio_path, language)

    def _groq_request_raw(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """Faz request para Groq API e retorna JSON raw."""
        import httpx

        mime_type = self._get_audio_mime_type(audio_path)

        with open(audio_path, 'rb') as audio_file:
            files = {'file': (Path(audio_path).name, audio_file, mime_type)}
            data = {
                'model': self.GROQ_MODEL,
                'response_format': 'verbose_json',
                'timestamp_granularities[]': 'word',
            }
            if language:
                data['language'] = language

            response = httpx.post(
                self.GROQ_API_URL,
                files=files,
                data=data,
                headers={'Authorization': f'Bearer {GROQ_API_KEY}'},
                timeout=120.0
            )

            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.status_code} - {response.text}")

            return response.json()

    def _groq_request(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """Faz request para Groq API e retorna resultado formatado."""
        raw_result = self._groq_request_raw(audio_path, language)
        return self._format_groq_result(raw_result)

    def _transcribe_groq_chunked(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcreve arquivo grande em chunks via Groq.

        Divide o áudio em chunks de 10 minutos, transcreve cada um,
        e combina os resultados ajustando os timestamps.
        """
        import tempfile
        import os

        chunk_duration = 600  # 10 min
        audio_path = Path(audio_path)

        # Obter duração total
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        total_duration = float(result.stdout.strip())

        print(f"  Áudio total: {total_duration:.1f}s, dividindo em chunks de {chunk_duration}s")

        # Processar chunks e coletar resultados RAW
        all_segments = []
        all_words = []
        full_text = []
        detected_language = language

        current_time = 0
        chunk_num = 0

        while current_time < total_duration:
            chunk_num += 1
            chunk_end = min(current_time + chunk_duration, total_duration)

            # Extrair chunk como MP3
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                chunk_path = tmp.name

            try:
                cmd = [
                    'ffmpeg', '-y',
                    '-ss', str(current_time),
                    '-i', str(audio_path),
                    '-t', str(chunk_end - current_time),
                    '-acodec', 'libmp3lame',
                    '-b:a', '64k',
                    '-ar', '16000',
                    '-ac', '1',
                    chunk_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)

                print(f"  Transcrevendo chunk {chunk_num} ({current_time:.0f}s - {chunk_end:.0f}s)...")

                # Transcrever chunk - pegar resultado RAW
                raw_result = self._groq_request_raw(chunk_path, language)

                # Detectar idioma do primeiro chunk
                if detected_language is None and raw_result.get('language'):
                    detected_language = raw_result.get('language')

                # Processar palavras com offset primeiro
                chunk_words = []
                for word in (raw_result.get('words') or []):
                    adjusted_word = {
                        'word': (word.get('word') or '').strip(),
                        'start': (word.get('start') or 0) + current_time,
                        'end': (word.get('end') or 0) + current_time,
                        'probability': 1.0
                    }
                    chunk_words.append(adjusted_word)
                    all_words.append(adjusted_word)

                # Processar segmentos com offset (se existirem)
                raw_segments = raw_result.get('segments') or []
                if raw_segments:
                    for segment in raw_segments:
                        adjusted_segment = {
                            'id': len(all_segments),
                            'start': (segment.get('start') or 0) + current_time,
                            'end': (segment.get('end') or 0) + current_time,
                            'text': (segment.get('text') or '').strip(),
                            'words': []
                        }
                        all_segments.append(adjusted_segment)
                else:
                    # Groq não retornou segmentos - criar a partir das palavras
                    chunk_segments = self._create_segments_from_words(chunk_words)
                    for seg in chunk_segments:
                        seg['id'] = len(all_segments)
                        all_segments.append(seg)

                # Adicionar texto
                if raw_result.get('text'):
                    full_text.append(raw_result.get('text').strip())

            except Exception as e:
                print(f"  Erro no chunk {chunk_num}: {e}")
                # Continuar com próximo chunk
            finally:
                if os.path.exists(chunk_path):
                    os.unlink(chunk_path)

            current_time = chunk_end

        # Associar palavras aos segmentos
        for segment in all_segments:
            seg_start = segment['start']
            seg_end = segment['end']
            segment['words'] = [
                w for w in all_words
                if w['start'] >= seg_start - 0.1 and w['end'] <= seg_end + 0.1
            ]

        print(f"  Transcrição combinada: {len(all_segments)} segmentos, {len(all_words)} palavras")

        return {
            'text': ' '.join(full_text),
            'language': detected_language or 'pt',
            'duration': total_duration,
            'segments': all_segments,
            'words': all_words,
            'backend': 'groq'
        }

    def _create_segments_from_words(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cria segmentos a partir de palavras quando a API não retorna segmentos.

        Agrupa palavras em segmentos baseado em:
        - Pausas longas (> 0.8s)
        - Máximo de 15 palavras por segmento
        - Máximo de 10 segundos por segmento
        """
        if not words:
            return []

        segments = []
        current_segment_words = []
        current_segment_start = words[0]['start']

        pause_threshold = 0.8  # Pausa de 0.8s indica novo segmento
        max_words = 15
        max_duration = 10.0

        for i, word in enumerate(words):
            # Verificar se devemos iniciar novo segmento
            should_split = False

            if current_segment_words:
                last_word = current_segment_words[-1]
                pause = word['start'] - last_word['end']
                duration = word['end'] - current_segment_start

                # Condições para dividir
                if pause > pause_threshold:
                    should_split = True
                elif len(current_segment_words) >= max_words:
                    should_split = True
                elif duration > max_duration:
                    should_split = True

            if should_split and current_segment_words:
                # Finalizar segmento atual
                segment_text = ' '.join(w['word'] for w in current_segment_words)
                segments.append({
                    'id': len(segments),
                    'start': current_segment_start,
                    'end': current_segment_words[-1]['end'],
                    'text': segment_text,
                    'words': current_segment_words.copy()
                })
                current_segment_words = []
                current_segment_start = word['start']

            current_segment_words.append(word)

        # Adicionar último segmento
        if current_segment_words:
            segment_text = ' '.join(w['word'] for w in current_segment_words)
            segments.append({
                'id': len(segments),
                'start': current_segment_start,
                'end': current_segment_words[-1]['end'],
                'text': segment_text,
                'words': current_segment_words.copy()
            })

        return segments

    def _format_groq_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Formata resultado do Groq para o formato padrão."""
        # Verificar se result é válido
        if result is None:
            print("Aviso: Groq retornou resultado vazio")
            return {
                'text': '',
                'language': 'pt',
                'duration': 0,
                'segments': [],
                'words': [],
                'backend': 'groq'
            }

        segments = []
        all_words = []

        # Processar palavras primeiro
        for word_data in (result.get('words') or []):
            word = {
                'word': word_data.get('word', '').strip(),
                'start': word_data.get('start'),
                'end': word_data.get('end'),
                'probability': 1.0
            }
            all_words.append(word)

        # Processar segmentos (se existirem)
        raw_segments = result.get('segments') or []
        if raw_segments:
            for segment in raw_segments:
                segment_data = {
                    'id': segment.get('id'),
                    'start': segment.get('start'),
                    'end': segment.get('end'),
                    'text': segment.get('text', '').strip(),
                    'words': []
                }
                segments.append(segment_data)

            # Associar palavras aos segmentos
            for segment in segments:
                segment['words'] = [
                    w for w in all_words
                    if w['start'] >= segment['start'] - 0.1 and w['end'] <= segment['end'] + 0.1
                ]
        else:
            # Groq não retornou segmentos - criar a partir das palavras
            segments = self._create_segments_from_words(all_words)
            print(f"  Criados {len(segments)} segmentos a partir de {len(all_words)} palavras")

        return {
            'text': result.get('text', '').strip(),
            'language': result.get('language', 'pt'),
            'duration': segments[-1]['end'] if segments else (all_words[-1]['end'] if all_words else 0),
            'segments': segments,
            'words': all_words,
            'backend': 'groq'
        }

    # =========================================================================
    # Deepgram Backend - Alta qualidade com word-level timestamps
    # =========================================================================

    def _transcribe_deepgram(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcreve usando Deepgram API.

        Deepgram oferece alta precisão e word-level timestamps confiáveis.
        Modelo Nova-3 é o mais preciso disponível.
        """
        import httpx

        # Mapear código de idioma
        lang_map = {"pt": "pt-BR", "en": "en-US", "es": "es"}
        dg_language = lang_map.get(language, language) if language else "pt-BR"

        # Ler arquivo de áudio
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        # Detectar MIME type
        mime_type = self._get_audio_mime_type(audio_path)

        # Configurar request
        url = "https://api.deepgram.com/v1/listen"
        params = {
            "model": "nova-2",  # Modelo mais preciso
            "language": dg_language,
            "punctuate": "true",
            "diarize": "false",
            "smart_format": "true",
            "utterances": "true",
            "words": "true",  # Word-level timestamps
        }

        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": mime_type,
        }

        print(f"  Enviando para Deepgram ({dg_language})...")

        response = httpx.post(
            url,
            params=params,
            headers=headers,
            content=audio_data,
            timeout=300.0
        )

        if response.status_code != 200:
            raise Exception(f"Deepgram API error: {response.status_code} - {response.text}")

        result = response.json()
        return self._format_deepgram_result(result, language or "pt")

    def _format_deepgram_result(self, result: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Formata resultado do Deepgram para o formato padrão."""
        segments = []
        all_words = []
        full_text = []

        # Deepgram retorna em results.channels[0].alternatives[0]
        try:
            channel = result["results"]["channels"][0]
            alternative = channel["alternatives"][0]
        except (KeyError, IndexError):
            print("Aviso: Deepgram retornou resultado vazio ou malformado")
            return {
                'text': '',
                'language': language,
                'duration': 0,
                'segments': [],
                'words': [],
                'backend': 'deepgram'
            }

        # Processar palavras
        for word_data in alternative.get("words", []):
            word = {
                'word': word_data.get('word', '').strip(),
                'start': word_data.get('start', 0),
                'end': word_data.get('end', 0),
                'probability': word_data.get('confidence', 1.0)
            }
            all_words.append(word)

        # Usar utterances como segmentos (se disponíveis)
        utterances = result.get("results", {}).get("utterances", [])
        if utterances:
            for i, utt in enumerate(utterances):
                segment = {
                    'id': i,
                    'start': utt.get('start', 0),
                    'end': utt.get('end', 0),
                    'text': utt.get('transcript', '').strip(),
                    'words': []
                }
                # Associar palavras ao segmento
                segment['words'] = [
                    w for w in all_words
                    if w['start'] >= segment['start'] - 0.1 and w['end'] <= segment['end'] + 0.1
                ]
                segments.append(segment)
                full_text.append(segment['text'])
        else:
            # Criar segmentos a partir das palavras
            segments = self._create_segments_from_words(all_words)
            full_text = [s['text'] for s in segments]

        return {
            'text': alternative.get('transcript', ' '.join(full_text)).strip(),
            'language': language,
            'duration': all_words[-1]['end'] if all_words else 0,
            'segments': segments,
            'words': all_words,
            'backend': 'deepgram'
        }

    # =========================================================================
    # AssemblyAI Backend - Alta qualidade alternativa
    # =========================================================================

    def _transcribe_assemblyai(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcreve usando AssemblyAI API.

        AssemblyAI oferece alta precisão e word-level timestamps.
        """
        import httpx
        import time as time_module

        # Mapear código de idioma
        lang_map = {"pt": "pt", "en": "en", "es": "es"}
        aai_language = lang_map.get(language, language) if language else "pt"

        headers = {
            "Authorization": ASSEMBLYAI_API_KEY,
            "Content-Type": "application/json",
        }

        # Passo 1: Upload do arquivo
        print(f"  Fazendo upload para AssemblyAI...")
        with open(audio_path, 'rb') as audio_file:
            upload_response = httpx.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"Authorization": ASSEMBLYAI_API_KEY},
                content=audio_file.read(),
                timeout=300.0
            )

        if upload_response.status_code != 200:
            raise Exception(f"AssemblyAI upload error: {upload_response.status_code}")

        upload_url = upload_response.json()["upload_url"]

        # Passo 2: Criar transcrição
        print(f"  Iniciando transcrição ({aai_language})...")
        transcript_request = {
            "audio_url": upload_url,
            "language_code": aai_language,
            "punctuate": True,
            "format_text": True,
        }

        transcript_response = httpx.post(
            "https://api.assemblyai.com/v2/transcript",
            headers=headers,
            json=transcript_request,
            timeout=60.0
        )

        if transcript_response.status_code != 200:
            raise Exception(f"AssemblyAI transcript error: {transcript_response.status_code}")

        transcript_id = transcript_response.json()["id"]

        # Passo 3: Aguardar conclusão
        print(f"  Aguardando processamento...")
        while True:
            status_response = httpx.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers=headers,
                timeout=60.0
            )

            status = status_response.json()

            if status["status"] == "completed":
                return self._format_assemblyai_result(status, language or "pt")
            elif status["status"] == "error":
                raise Exception(f"AssemblyAI error: {status.get('error', 'Unknown error')}")

            time_module.sleep(3)  # Aguardar 3 segundos antes de verificar novamente

    def _format_assemblyai_result(self, result: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Formata resultado do AssemblyAI para o formato padrão."""
        segments = []
        all_words = []

        # Processar palavras
        for word_data in result.get("words", []):
            word = {
                'word': word_data.get('text', '').strip(),
                'start': word_data.get('start', 0) / 1000.0,  # Converter ms para segundos
                'end': word_data.get('end', 0) / 1000.0,
                'probability': word_data.get('confidence', 1.0)
            }
            all_words.append(word)

        # Criar segmentos a partir das palavras
        segments = self._create_segments_from_words(all_words)

        return {
            'text': result.get('text', '').strip(),
            'language': language,
            'duration': all_words[-1]['end'] if all_words else 0,
            'segments': segments,
            'words': all_words,
            'backend': 'assemblyai'
        }

    # =========================================================================
    # Pós-processamento de timestamps
    # =========================================================================

    def _enhance_timestamps(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Melhora timestamps usando heurísticas.

        Técnicas aplicadas:
        1. Suavização de gaps muito pequenos
        2. Ajuste de sobreposições
        3. Extensão mínima de duração de palavras
        4. Preenchimento de silêncios
        """
        words = result.get('words', [])
        if not words:
            return result

        enhanced_words = []
        min_word_duration = 0.08  # Duração mínima de 80ms
        max_gap = 0.15  # Gap máximo antes de considerar pausa

        for i, word in enumerate(words):
            w = word.copy()

            # Garantir duração mínima
            duration = w['end'] - w['start']
            if duration < min_word_duration:
                # Estender a palavra
                center = (w['start'] + w['end']) / 2
                w['start'] = center - min_word_duration / 2
                w['end'] = center + min_word_duration / 2

            # Ajustar início para não sobrepor palavra anterior
            if enhanced_words:
                prev = enhanced_words[-1]
                if w['start'] < prev['end']:
                    # Ajustar para meio do overlap
                    mid = (w['start'] + prev['end']) / 2
                    prev['end'] = mid - 0.01
                    w['start'] = mid + 0.01
                elif w['start'] - prev['end'] < max_gap:
                    # Preencher pequenos gaps
                    gap = w['start'] - prev['end']
                    prev['end'] += gap * 0.3
                    w['start'] -= gap * 0.3

            enhanced_words.append(w)

        # Atualizar resultado
        result['words'] = enhanced_words

        # Atualizar palavras nos segmentos também
        for segment in result.get('segments', []):
            seg_start = segment['start']
            seg_end = segment['end']
            segment['words'] = [
                w for w in enhanced_words
                if w['start'] >= seg_start - 0.1 and w['end'] <= seg_end + 0.1
            ]

        result['backend'] = result.get('backend', 'unknown') + '-enhanced'
        return result

    # =========================================================================
    # Métodos auxiliares
    # =========================================================================

    def _get_audio_mime_type(self, audio_path: str) -> str:
        """Retorna MIME type baseado na extensão."""
        ext = Path(audio_path).suffix.lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
        }
        return mime_types.get(ext, 'audio/wav')

    def extract_audio(self, video_path: str, output_path: str = None) -> str:
        """
        Extrai áudio do vídeo.

        Args:
            video_path: Caminho do vídeo
            output_path: Caminho de saída (opcional)

        Returns:
            Caminho do arquivo de áudio
        """
        video_path = Path(video_path)

        if output_path is None:
            output_path = self.audio_dir / f"{video_path.stem}.wav"
        else:
            output_path = Path(output_path)

        # Extrair como WAV 16kHz mono (melhor para Whisper)
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',
            str(output_path)
        ]

        print(f"Extraindo áudio: {video_path} -> {output_path}")
        subprocess.run(cmd, check=True, capture_output=True)

        return str(output_path)

    # =========================================================================
    # Interface principal
    # =========================================================================

    def transcribe(
        self,
        audio_path: str,
        language: str = None,
        enhance_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        Transcreve áudio usando o backend configurado.

        Args:
            audio_path: Caminho do arquivo de áudio
            language: Código do idioma (None para auto-detectar)
            enhance_timestamps: Aplicar pós-processamento de timestamps

        Returns:
            Dict com transcrição e timestamps palavra-por-palavra
        """
        if language == "auto":
            language = None
        elif language is None:
            language = WHISPER_LANGUAGE

        print(f"Transcrevendo com {self.backend}: {audio_path}")

        if self.backend == "deepgram":
            result = self._transcribe_deepgram(audio_path, language)
        elif self.backend == "assemblyai":
            result = self._transcribe_assemblyai(audio_path, language)
        elif self.backend == "whisperx":
            result = self._transcribe_whisperx(audio_path, language)
        elif self.backend == "stable-ts":
            result = self._transcribe_stable_ts(audio_path, language)
        elif self.backend == "faster-whisper":
            result = self._transcribe_faster_whisper(audio_path, language)
        elif self.backend == "groq":
            result = self._transcribe_groq(audio_path, language)
        else:
            raise ValueError(f"Backend desconhecido: {self.backend}")

        # Aplicar pós-processamento de timestamps
        if enhance_timestamps:
            result = self._enhance_timestamps(result)
            print(f"  Timestamps aprimorados aplicados")

        return result

    def transcribe_video(self, video_path: str, language: str = None) -> Dict[str, Any]:
        """
        Extrai áudio e transcreve vídeo.

        Args:
            video_path: Caminho do vídeo
            language: Código do idioma

        Returns:
            Dict com transcrição e timestamps
        """
        # Extrair áudio
        audio_path = self.extract_audio(video_path)

        try:
            # Transcrever
            result = self.transcribe(audio_path, language)
            result['audio_path'] = audio_path
            return result
        except Exception as e:
            # Limpar em caso de erro
            if Path(audio_path).exists():
                Path(audio_path).unlink()
            raise

    def get_text_for_timerange(
        self,
        transcription: Dict[str, Any],
        start_time: float,
        end_time: float
    ) -> Dict[str, Any]:
        """
        Obtém texto e palavras para um intervalo de tempo.

        Args:
            transcription: Resultado da transcrição
            start_time: Tempo inicial em segundos
            end_time: Tempo final em segundos

        Returns:
            Dict com texto e palavras do intervalo
        """
        segments = []
        words = []
        text_parts = []

        for segment in transcription.get('segments', []):
            seg_start = segment.get('start', 0)
            seg_end = segment.get('end', 0)

            if seg_end >= start_time and seg_start <= end_time:
                segment_words = []
                for word in segment.get('words', []):
                    word_start = word.get('start', 0)
                    word_end = word.get('end', 0)

                    if word_end >= start_time and word_start <= end_time:
                        segment_words.append(word)
                        words.append(word)

                if segment_words:
                    text_parts.append(' '.join(w['word'] for w in segment_words))
                    segments.append({
                        'start': max(seg_start, start_time),
                        'end': min(seg_end, end_time),
                        'text': ' '.join(w['word'] for w in segment_words),
                        'words': segment_words
                    })

        return {
            'text': ' '.join(text_parts),
            'segments': segments,
            'words': words,
            'start_time': start_time,
            'end_time': end_time
        }

    def unload_model(self):
        """Libera memória do modelo."""
        import gc

        if self._model is not None:
            del self._model
            self._model = None

        if self._whisperx_model is not None:
            del self._whisperx_model
            self._whisperx_model = None

        if self._align_model is not None:
            del self._align_model
            self._align_model = None

        gc.collect()

        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

        print("Modelo de transcrição liberado da memória")


# Factory function para criar transcriber
def create_transcriber(
    backend: TranscriptionBackend = "auto",
    model_size: str = None
) -> TranscriberV2:
    """
    Cria um transcriber com o backend especificado.

    Args:
        backend: Backend a usar (whisperx, stable-ts, faster-whisper, groq, auto)
        model_size: Tamanho do modelo

    Returns:
        Instância do TranscriberV2
    """
    return TranscriberV2(backend=backend, model_size=model_size)


# Teste rápido
if __name__ == "__main__":
    print("TranscriberV2 - Verificando backends disponíveis...")

    backends = ["whisperx", "stable-ts", "faster-whisper", "groq"]
    transcriber = TranscriberV2(backend="auto")

    for b in backends:
        available = transcriber._check_backend_available(b)
        status = "✅" if available else "❌"
        print(f"  {status} {b}")

    print(f"\nBackend selecionado: {transcriber.backend}")
