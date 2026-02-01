"""
ClipGenius - Transcription Service
Supports Groq Whisper API (fast) and local Whisper (fallback)
Optimized for speed: MP3 compression, parallel chunks, smart retries
"""
import json
import subprocess
import httpx
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import (
    AUDIO_DIR,
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    GROQ_API_KEY
)


class WhisperTranscriber:
    """
    Service to transcribe audio using Whisper.
    Uses Groq API (50x faster) if available, falls back to local Whisper.
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
    GROQ_MODEL = "whisper-large-v3-turbo"  # Fastest model with word timestamps

    def __init__(self, model_name: str = None):
        self.model_name = model_name or WHISPER_MODEL
        self.model = None  # Lazy load for local whisper
        self.audio_dir = AUDIO_DIR
        self.use_groq = bool(GROQ_API_KEY)

        if self.use_groq:
            print("Transcriber: Using Groq Whisper API (fast mode)")
        else:
            print("Transcriber: Using local Whisper (set GROQ_API_KEY for faster transcription)")

    def _load_local_model(self):
        """Lazy load local Whisper model"""
        if self.model is None:
            import whisper
            print(f"Loading local Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
        return self.model

    def unload_model(self):
        """
        Unload Whisper model from memory to free GPU/CPU resources.
        Call this after transcription is complete.
        """
        if self.model is not None:
            import gc
            import torch
            print("Unloading Whisper model from memory...")
            del self.model
            self.model = None
            gc.collect()
            # Clear CUDA cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("Whisper model unloaded")

    def extract_audio(self, video_path: str, output_path: Optional[str] = None, for_groq: bool = None) -> str:
        """
        Extract audio from video using FFmpeg
        Uses MP3 64kbps for Groq (85% smaller, 3-7x faster upload)
        Uses WAV for local Whisper (better compatibility)

        Args:
            video_path: Path to video file
            output_path: Optional output path for audio
            for_groq: Force format (True=MP3, False=WAV, None=auto)

        Returns:
            Path to extracted audio file
        """
        video_path = Path(video_path)

        # Auto-detect format based on transcription method
        use_mp3 = for_groq if for_groq is not None else self.use_groq
        ext = ".mp3" if use_mp3 else ".wav"

        if output_path is None:
            output_path = self.audio_dir / f"{video_path.stem}{ext}"
        else:
            output_path = Path(output_path)

        # FFmpeg command - MP3 for Groq (smaller/faster), WAV for local
        if use_mp3:
            # MP3 64kbps mono - optimal for speech, ~8MB for 30 min
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-b:a', '64k',  # 64kbps bitrate
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                str(output_path)
            ]
        else:
            # WAV PCM for local Whisper
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM format
                '-ar', '16000',  # 16kHz sample rate (Whisper default)
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                str(output_path)
            ]

        format_info = "MP3 64kbps" if use_mp3 else "WAV PCM"
        print(f"Extracting audio ({format_info}): {video_path} -> {output_path}")

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # Clean up partial file on failure
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception:
                    pass
            print(f"FFmpeg audio extraction failed: {e.stderr.decode() if e.stderr else str(e)}")
            raise

        # Log file size for debugging
        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"Audio extracted: {file_size:.1f}MB")

        return str(output_path)

    def _get_audio_mime_type(self, audio_path: str) -> str:
        """Get MIME type based on audio file extension"""
        ext = Path(audio_path).suffix.lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
        }
        return mime_types.get(ext, 'audio/wav')

    def _groq_request_with_retry(self, audio_path: str, language: str = None, chunk_name: str = None) -> Dict[str, Any]:
        """
        Make Groq API request with exponential backoff retry
        Timeout: 120s, Retries: 3 (1s, 2s, 4s delays)

        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detect)
            chunk_name: Optional name for chunk
        """
        max_retries = 3
        base_delay = 1.0
        timeout = 120.0  # Reduced from 300s

        mime_type = self._get_audio_mime_type(audio_path)
        filename = chunk_name or Path(audio_path).name

        for attempt in range(max_retries + 1):
            try:
                with open(audio_path, 'rb') as audio_file:
                    files = {
                        'file': (filename, audio_file, mime_type),
                    }
                    data = {
                        'model': self.GROQ_MODEL,
                        'response_format': 'verbose_json',
                        'timestamp_granularities[]': 'word',
                    }
                    # Only add language if specified (None = auto-detect)
                    if language is not None:
                        data['language'] = language
                    headers = {
                        'Authorization': f'Bearer {GROQ_API_KEY}',
                    }

                    response = httpx.post(
                        self.GROQ_API_URL,
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=timeout
                    )

                    if response.status_code == 200:
                        return response.json()

                    # Rate limit - wait and retry
                    if response.status_code == 429:
                        if attempt < max_retries:
                            delay = base_delay * (2 ** attempt)
                            print(f"  Rate limited, retrying in {delay}s...")
                            time.sleep(delay)
                            continue

                    raise Exception(f"Groq API error: {response.status_code} - {response.text}")

            except httpx.TimeoutException:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    print(f"  Timeout, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise Exception(f"Groq API timeout after {max_retries + 1} attempts")

            except httpx.RequestError as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    print(f"  Request error, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise Exception(f"Groq API request failed: {e}")

        raise Exception("Groq API failed after all retries")

    def _transcribe_with_groq(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcribe using Groq Whisper API (50x faster than local)

        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detect)

        Returns:
            Dict with transcription and word-level timestamps
        """
        lang_info = f" (language: {language})" if language else " (auto-detect)"
        print(f"Transcribing with Groq Whisper API{lang_info}: {audio_path}")

        # Check file size (Groq limit is 25MB)
        file_size = Path(audio_path).stat().st_size
        max_size = 25 * 1024 * 1024  # 25MB

        if file_size > max_size:
            print(f"Audio file too large for Groq ({file_size / 1024 / 1024:.1f}MB > 25MB), chunking...")
            return self._transcribe_groq_chunked(audio_path, language)

        result = self._groq_request_with_retry(audio_path, language)
        return self._parse_groq_response(result)

    def _transcribe_groq_chunked(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcribe large audio files by splitting into chunks
        OPTIMIZED: Processes up to 3 chunks in parallel for 3x speedup

        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detect)
        """
        import tempfile
        import os

        chunk_duration = 600  # 10 minutes per chunk
        max_parallel = 3  # Process up to 3 chunks simultaneously
        audio_path = Path(audio_path)

        # Detect if source is MP3 for chunk extraction
        is_mp3 = audio_path.suffix.lower() == '.mp3'

        # Get audio duration
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        total_duration = float(result.stdout.strip())

        # Calculate chunks
        chunks = []
        current_time = 0
        chunk_num = 0
        while current_time < total_duration:
            chunk_num += 1
            chunk_end = min(current_time + chunk_duration, total_duration)
            chunks.append({
                'num': chunk_num,
                'start': current_time,
                'end': chunk_end,
                'duration': chunk_end - current_time
            })
            current_time = chunk_end

        print(f"  Splitting into {len(chunks)} chunks, processing {min(len(chunks), max_parallel)} in parallel")

        def extract_and_transcribe_chunk(chunk_info: Dict) -> Dict:
            """Extract and transcribe a single chunk"""
            chunk_num = chunk_info['num']
            start_time = chunk_info['start']
            duration = chunk_info['duration']

            # Use MP3 for chunks too (smaller, faster upload)
            suffix = '.mp3' if is_mp3 else '.mp3'  # Always use MP3 for chunks
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                chunk_path = tmp.name

            try:
                # Extract chunk as MP3 for faster upload
                cmd = [
                    'ffmpeg', '-y',
                    '-ss', str(start_time),
                    '-i', str(audio_path),
                    '-t', str(duration),
                    '-acodec', 'libmp3lame',
                    '-b:a', '64k',
                    '-ar', '16000',
                    '-ac', '1',
                    chunk_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)

                print(f"  Transcribing chunk {chunk_num}/{len(chunks)} ({start_time:.0f}s - {chunk_info['end']:.0f}s)")

                # Transcribe chunk with retry
                chunk_result = self._groq_request_with_retry(
                    chunk_path,
                    language,
                    chunk_name=f'chunk_{chunk_num}.mp3'
                )

                return {
                    'num': chunk_num,
                    'start_offset': start_time,
                    'result': chunk_result
                }

            finally:
                # Cleanup temp file
                if os.path.exists(chunk_path):
                    os.unlink(chunk_path)

        # Process chunks in parallel
        results_by_num = {}
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            futures = {executor.submit(extract_and_transcribe_chunk, chunk): chunk for chunk in chunks}

            for future in as_completed(futures):
                chunk_result = future.result()
                results_by_num[chunk_result['num']] = chunk_result

        # Combine results in order
        all_segments = []
        all_words = []
        full_text = []

        for chunk_num in sorted(results_by_num.keys()):
            chunk_data = results_by_num[chunk_num]
            start_offset = chunk_data['start_offset']
            chunk_result = chunk_data['result']

            # Adjust timestamps and merge
            for segment in chunk_result.get('segments', []):
                segment['start'] += start_offset
                segment['end'] += start_offset
                all_segments.append(segment)

            for word in chunk_result.get('words', []):
                word['start'] += start_offset
                word['end'] += start_offset
                all_words.append(word)

            if chunk_result.get('text'):
                full_text.append(chunk_result['text'].strip())

        # Combine results
        return self._format_transcription({
            'text': ' '.join(full_text),
            'segments': all_segments,
            'words': all_words,
            'language': language,
            'duration': total_duration
        })

    def _parse_groq_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Groq API response into our format"""
        segments = []

        for segment in result.get('segments', []):
            segment_data = {
                'id': segment.get('id'),
                'start': segment.get('start'),
                'end': segment.get('end'),
                'text': segment.get('text', '').strip(),
                'words': []
            }
            segments.append(segment_data)

        # Process word-level timestamps
        words_list = result.get('words', [])
        all_words = []

        for word_data in words_list:
            word = {
                'word': word_data.get('word', '').strip(),
                'start': word_data.get('start'),
                'end': word_data.get('end'),
                'probability': 1.0  # Groq doesn't return probability
            }
            all_words.append(word)

        # Assign words to segments
        for segment in segments:
            segment_start = segment['start']
            segment_end = segment['end']
            segment['words'] = [
                w for w in all_words
                if w['start'] >= segment_start and w['end'] <= segment_end
            ]

        return {
            'text': result.get('text', '').strip(),
            'language': result.get('language', 'pt'),
            'duration': segments[-1]['end'] if segments else 0,
            'segments': segments,
            'words': all_words
        }

    def _format_transcription(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format transcription result into consistent structure"""
        segments = []

        for segment in result.get('segments', []):
            segment_data = {
                'id': segment.get('id'),
                'start': segment.get('start'),
                'end': segment.get('end'),
                'text': segment.get('text', '').strip(),
                'words': segment.get('words', [])
            }
            segments.append(segment_data)

        return {
            'text': result.get('text', '').strip(),
            'language': result.get('language', 'pt'),
            'duration': result.get('duration', 0),
            'segments': segments,
            'words': result.get('words', [])
        }

    def _transcribe_local(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcribe audio file using local Whisper

        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detect)

        Returns:
            Dict with transcription and word-level timestamps
        """
        model = self._load_local_model()

        lang_info = f" (language: {language})" if language else " (auto-detect)"
        print(f"Transcribing with local Whisper{lang_info}: {audio_path}")

        # Import config for quality settings
        from config import WHISPER_TEMPERATURE, WHISPER_BEAM_SIZE, WHISPER_BEST_OF

        result = model.transcribe(
            audio_path,
            language=language,  # None = auto-detect
            word_timestamps=True,
            verbose=False,
            temperature=WHISPER_TEMPERATURE,
            beam_size=WHISPER_BEAM_SIZE,
            best_of=WHISPER_BEST_OF,
            condition_on_previous_text=True,
            no_speech_threshold=0.6,
            logprob_threshold=-1.0,
            compression_ratio_threshold=2.4
        )

        # Process segments with word timestamps
        segments = []
        all_words = []

        for segment in result.get('segments', []):
            segment_data = {
                'id': segment.get('id'),
                'start': segment.get('start'),
                'end': segment.get('end'),
                'text': segment.get('text', '').strip(),
                'words': []
            }

            for word in segment.get('words', []):
                word_data = {
                    'word': word.get('word', '').strip(),
                    'start': word.get('start'),
                    'end': word.get('end'),
                    'probability': word.get('probability')
                }
                segment_data['words'].append(word_data)
                all_words.append(word_data)

            segments.append(segment_data)

        return {
            'text': result.get('text', '').strip(),
            'language': result.get('language'),
            'duration': segments[-1]['end'] if segments else 0,
            'segments': segments,
            'words': all_words
        }

    def transcribe(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        Transcribe audio file (auto-selects best method)

        Args:
            audio_path: Path to audio file
            language: Language code (None or "auto" for auto-detect, default from config)

        Returns:
            Dict with transcription and word-level timestamps
        """
        # Handle language parameter: "auto" means auto-detect (None for Whisper)
        if language == "auto":
            language = None
        elif language is None:
            language = WHISPER_LANGUAGE

        if self.use_groq:
            try:
                return self._transcribe_with_groq(audio_path, language)
            except Exception as e:
                print(f"Groq transcription failed: {e}")
                print("Falling back to local Whisper...")
                return self._transcribe_local(audio_path, language)
        else:
            return self._transcribe_local(audio_path, language)

    def transcribe_video(self, video_path: str, language: str = None, unload_after: bool = True) -> Dict[str, Any]:
        """
        Extract audio and transcribe video

        Args:
            video_path: Path to video file
            language: Language code
            unload_after: Unload model after transcription to free memory (default: True)

        Returns:
            Dict with transcription and timestamps
        """
        audio_path = None
        try:
            # Extract audio
            audio_path = self.extract_audio(video_path)

            # Transcribe
            transcription = self.transcribe(audio_path, language)
            transcription['audio_path'] = audio_path

            return transcription
        except Exception as e:
            # Clean up audio file on failure
            if audio_path and Path(audio_path).exists():
                try:
                    Path(audio_path).unlink()
                except Exception:
                    pass
            raise
        finally:
            # Unload model to free memory (only for local Whisper)
            if unload_after and not self.use_groq:
                self.unload_model()

    def get_text_for_timerange(
        self,
        transcription: Dict[str, Any],
        start_time: float,
        end_time: float
    ) -> Dict[str, Any]:
        """
        Get transcription text for a specific time range

        Args:
            transcription: Full transcription dict
            start_time: Start time in seconds
            end_time: End time in seconds

        Returns:
            Dict with text and word timestamps for the range
        """
        segments = []
        words = []
        text_parts = []

        for segment in transcription.get('segments', []):
            seg_start = segment.get('start', 0)
            seg_end = segment.get('end', 0)

            # Check if segment overlaps with our range
            if seg_end >= start_time and seg_start <= end_time:
                # Filter words within range
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


# Quick test
if __name__ == "__main__":
    transcriber = WhisperTranscriber()
    print(f"Transcriber initialized")
    print(f"Using Groq: {transcriber.use_groq}")
