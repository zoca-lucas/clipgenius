"""
ClipGenius - Whisper Transcription Service
Transcribes audio using OpenAI Whisper (local)
"""
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import whisper
from config import AUDIO_DIR, WHISPER_MODEL


class WhisperTranscriber:
    """Service to transcribe audio using Whisper"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or WHISPER_MODEL
        self.model = None
        self.audio_dir = AUDIO_DIR

    def _load_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            print(f"Loading Whisper model: {self.model_name}")
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

    def transcribe(self, audio_path: str, language: str = "pt") -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper

        Args:
            audio_path: Path to audio file
            language: Language code (default: Portuguese)

        Returns:
            Dict with transcription and word-level timestamps
        """
        model = self._load_model()

        print(f"Transcribing: {audio_path}")

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
            condition_on_previous_text=True,  # Better context awareness
            no_speech_threshold=0.6,  # Avoid false detections
            logprob_threshold=-1.0,  # Quality threshold
            compression_ratio_threshold=2.4  # Avoid repetitions
        )

        # Process segments with word timestamps
        segments = []
        for segment in result.get('segments', []):
            segment_data = {
                'id': segment.get('id'),
                'start': segment.get('start'),
                'end': segment.get('end'),
                'text': segment.get('text', '').strip(),
                'words': []
            }

            # Add word-level timestamps if available
            for word in segment.get('words', []):
                segment_data['words'].append({
                    'word': word.get('word', '').strip(),
                    'start': word.get('start'),
                    'end': word.get('end'),
                    'probability': word.get('probability')
                })

            segments.append(segment_data)

        return {
            'text': result.get('text', '').strip(),
            'language': result.get('language'),
            'duration': result.get('segments', [{}])[-1].get('end', 0) if result.get('segments') else 0,
            'segments': segments
        }

    def transcribe_video(self, video_path: str, language: str = "pt") -> Dict[str, Any]:
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
    transcriber = WhisperTranscriber("tiny")  # Use tiny for testing
    print("Whisper transcriber initialized")
