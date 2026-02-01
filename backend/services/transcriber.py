"""
ClipGenius - Transcription Service
Supports Groq Whisper API (fast) and local Whisper (fallback)
"""
import json
import subprocess
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
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

    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio from video using FFmpeg

        Args:
            video_path: Path to video file
            output_path: Optional output path for audio

        Returns:
            Path to extracted audio file
        """
        video_path = Path(video_path)

        if output_path is None:
            output_path = self.audio_dir / f"{video_path.stem}.wav"
        else:
            output_path = Path(output_path)

        # FFmpeg command to extract audio
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

        print(f"Extracting audio: {video_path} -> {output_path}")
        subprocess.run(cmd, check=True, capture_output=True)

        return str(output_path)

    def _transcribe_with_groq(self, audio_path: str, language: str = "pt") -> Dict[str, Any]:
        """
        Transcribe using Groq Whisper API (50x faster than local)

        Args:
            audio_path: Path to audio file
            language: Language code

        Returns:
            Dict with transcription and word-level timestamps
        """
        print(f"Transcribing with Groq Whisper API: {audio_path}")

        # Check file size (Groq limit is 25MB)
        file_size = Path(audio_path).stat().st_size
        max_size = 25 * 1024 * 1024  # 25MB

        if file_size > max_size:
            print(f"Audio file too large for Groq ({file_size / 1024 / 1024:.1f}MB > 25MB), chunking...")
            return self._transcribe_groq_chunked(audio_path, language)

        with open(audio_path, 'rb') as audio_file:
            files = {
                'file': (Path(audio_path).name, audio_file, 'audio/wav'),
            }
            data = {
                'model': self.GROQ_MODEL,
                'language': language,
                'response_format': 'verbose_json',
                'timestamp_granularities[]': 'word',
            }
            headers = {
                'Authorization': f'Bearer {GROQ_API_KEY}',
            }

            response = httpx.post(
                self.GROQ_API_URL,
                files=files,
                data=data,
                headers=headers,
                timeout=300.0  # 5 minutes timeout
            )

            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.status_code} - {response.text}")

            result = response.json()

        return self._parse_groq_response(result)

    def _transcribe_groq_chunked(self, audio_path: str, language: str = "pt") -> Dict[str, Any]:
        """
        Transcribe large audio files by splitting into chunks
        """
        import tempfile
        import os

        chunk_duration = 600  # 10 minutes per chunk
        audio_path = Path(audio_path)

        # Get audio duration
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        total_duration = float(result.stdout.strip())

        all_segments = []
        all_words = []
        full_text = []

        chunk_num = 0
        current_time = 0

        while current_time < total_duration:
            chunk_num += 1
            chunk_end = min(current_time + chunk_duration, total_duration)

            # Create temp file for chunk
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                chunk_path = tmp.name

            try:
                # Extract chunk
                cmd = [
                    'ffmpeg', '-y',
                    '-ss', str(current_time),
                    '-i', str(audio_path),
                    '-t', str(chunk_duration),
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',
                    '-ac', '1',
                    chunk_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)

                print(f"  Transcribing chunk {chunk_num} ({current_time:.0f}s - {chunk_end:.0f}s)")

                # Transcribe chunk
                with open(chunk_path, 'rb') as audio_file:
                    files = {
                        'file': (f'chunk_{chunk_num}.wav', audio_file, 'audio/wav'),
                    }
                    data = {
                        'model': self.GROQ_MODEL,
                        'language': language,
                        'response_format': 'verbose_json',
                        'timestamp_granularities[]': 'word',
                    }
                    headers = {
                        'Authorization': f'Bearer {GROQ_API_KEY}',
                    }

                    response = httpx.post(
                        self.GROQ_API_URL,
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=300.0
                    )

                    if response.status_code != 200:
                        raise Exception(f"Groq API error: {response.status_code}")

                    chunk_result = response.json()

                # Adjust timestamps and merge
                for segment in chunk_result.get('segments', []):
                    segment['start'] += current_time
                    segment['end'] += current_time
                    all_segments.append(segment)

                for word in chunk_result.get('words', []):
                    word['start'] += current_time
                    word['end'] += current_time
                    all_words.append(word)

                if chunk_result.get('text'):
                    full_text.append(chunk_result['text'].strip())

            finally:
                # Cleanup temp file
                if os.path.exists(chunk_path):
                    os.unlink(chunk_path)

            current_time = chunk_end

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

    def _transcribe_local(self, audio_path: str, language: str = "pt") -> Dict[str, Any]:
        """
        Transcribe audio file using local Whisper

        Args:
            audio_path: Path to audio file
            language: Language code (default: Portuguese)

        Returns:
            Dict with transcription and word-level timestamps
        """
        model = self._load_local_model()

        print(f"Transcribing with local Whisper: {audio_path}")

        # Import config for quality settings
        from config import WHISPER_TEMPERATURE, WHISPER_BEAM_SIZE, WHISPER_BEST_OF

        result = model.transcribe(
            audio_path,
            language=language,
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
            language: Language code (default from config)

        Returns:
            Dict with transcription and word-level timestamps
        """
        language = language or WHISPER_LANGUAGE

        if self.use_groq:
            try:
                return self._transcribe_with_groq(audio_path, language)
            except Exception as e:
                print(f"Groq transcription failed: {e}")
                print("Falling back to local Whisper...")
                return self._transcribe_local(audio_path, language)
        else:
            return self._transcribe_local(audio_path, language)

    def transcribe_video(self, video_path: str, language: str = None) -> Dict[str, Any]:
        """
        Extract audio and transcribe video

        Args:
            video_path: Path to video file
            language: Language code

        Returns:
            Dict with transcription and timestamps
        """
        # Extract audio
        audio_path = self.extract_audio(video_path)

        # Transcribe
        transcription = self.transcribe(audio_path, language)
        transcription['audio_path'] = audio_path

        return transcription

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
