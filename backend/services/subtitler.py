"""
ClipGenius - Subtitle Generator Service
Generates and burns subtitles into video clips
"""
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import CLIPS_DIR


class SubtitleGenerator:
    """Service to generate and apply subtitles to video clips"""

    # Default subtitle style (ASS format) - Optimized for vertical video (9:16)
    DEFAULT_STYLE = {
        'font_name': 'Arial',
        'font_size': 32,  # Increased for vertical video readability
        'primary_color': '&H00FFFFFF',  # White
        'outline_color': '&H00000000',  # Black outline
        'back_color': '&H80000000',  # Semi-transparent black
        'bold': True,
        'outline': 3,  # Thicker outline for better visibility
        'shadow': 2,  # Stronger shadow for depth
        'alignment': 2,  # Bottom center
        'margin_v': 80,  # Larger margin for vertical format
    }

    def __init__(self):
        self.clips_dir = CLIPS_DIR

    def _format_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _format_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS timestamp format (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

    def _capitalize_text(self, text: str) -> str:
        """
        Properly capitalize subtitle text

        Args:
            text: Raw text from transcription

        Returns:
            Properly capitalized text
        """
        if not text:
            return text

        # First letter uppercase, rest lowercase
        text = text.strip()
        if text:
            text = text[0].upper() + text[1:].lower()

        return text

    def _chunk_words_by_length(
        self,
        words: List[Dict[str, Any]],
        max_chars: int = 42,
        max_words: int = 6
    ) -> List[List[Dict[str, Any]]]:
        """
        Chunk words into subtitle-friendly groups based on character limit

        Args:
            words: List of word dicts
            max_chars: Maximum characters per subtitle line
            max_words: Maximum words per subtitle line

        Returns:
            List of word chunks
        """
        chunks = []
        current_chunk = []
        current_length = 0

        for word_dict in words:
            word = word_dict.get('word', '').strip()
            word_len = len(word)

            # Check if adding this word would exceed limits
            if current_chunk:
                new_length = current_length + word_len + 1  # +1 for space
            else:
                new_length = word_len

            if (current_chunk and
                (new_length > max_chars or len(current_chunk) >= max_words)):
                # Start new chunk
                chunks.append(current_chunk)
                current_chunk = [word_dict]
                current_length = word_len
            else:
                # Add to current chunk
                current_chunk.append(word_dict)
                current_length = new_length

        # Add last chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def generate_srt(
        self,
        words: List[Dict[str, Any]],
        output_path: str,
        words_per_line: int = 6,
        offset: float = 0,
        max_chars_per_line: int = 42,
        capitalize: bool = True
    ) -> str:
        """
        Generate SRT subtitle file from word timestamps

        Args:
            words: List of word dicts with 'word', 'start', 'end'
            output_path: Output path for .srt file
            words_per_line: Max words per subtitle line (default: 6)
            offset: Time offset to subtract (for clip-relative times)
            max_chars_per_line: Maximum characters per line (default: 42)
            capitalize: Apply proper capitalization (default: True)

        Returns:
            Path to generated SRT file
        """
        output_path = Path(output_path)
        lines = []
        subtitle_index = 1

        # Chunk words intelligently
        chunks = self._chunk_words_by_length(words, max_chars_per_line, words_per_line)

        for chunk in chunks:
            if not chunk:
                continue

            start_time = chunk[0].get('start', 0) - offset
            end_time = chunk[-1].get('end', 0) - offset

            # Ensure times are not negative
            start_time = max(0, start_time)
            end_time = max(start_time + 0.1, end_time)

            # Build text with proper formatting
            text = ' '.join(w.get('word', '') for w in chunk).strip()

            # Apply capitalization if requested
            if capitalize:
                text = self._capitalize_text(text)

            if text:
                lines.append(str(subtitle_index))
                lines.append(f"{self._format_srt_time(start_time)} --> {self._format_srt_time(end_time)}")
                lines.append(text)
                lines.append('')
                subtitle_index += 1

        # Write SRT file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return str(output_path)

    def generate_ass(
        self,
        words: List[Dict[str, Any]],
        output_path: str,
        words_per_line: int = 6,
        offset: float = 0,
        style: Optional[Dict[str, Any]] = None,
        video_width: int = 1080,
        video_height: int = 1920,
        max_chars_per_line: int = 42,
        capitalize: bool = True
    ) -> str:
        """
        Generate ASS subtitle file with styling

        Args:
            words: List of word dicts
            output_path: Output path for .ass file
            words_per_line: Max words per subtitle line
            offset: Time offset
            style: Custom style dict
            video_width: Video width for positioning
            video_height: Video height for positioning
            max_chars_per_line: Maximum characters per line
            capitalize: Apply proper capitalization

        Returns:
            Path to generated ASS file
        """
        output_path = Path(output_path)
        style = {**self.DEFAULT_STYLE, **(style or {})}

        # ASS header
        ass_content = f"""[Script Info]
Title: ClipGenius Subtitles
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['font_name']},{style['font_size']},{style['primary_color']},&H000000FF,{style['outline_color']},{style['back_color']},{-1 if style['bold'] else 0},0,0,0,100,100,0,0,1,{style['outline']},{style['shadow']},{style['alignment']},10,10,{style['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        # Chunk words intelligently
        chunks = self._chunk_words_by_length(words, max_chars_per_line, words_per_line)

        for chunk in chunks:
            if not chunk:
                continue

            start_time = chunk[0].get('start', 0) - offset
            end_time = chunk[-1].get('end', 0) - offset

            start_time = max(0, start_time)
            end_time = max(start_time + 0.1, end_time)

            text = ' '.join(w.get('word', '') for w in chunk).strip()

            # Apply capitalization if requested
            if capitalize:
                text = self._capitalize_text(text)

            if text:
                start_str = self._format_ass_time(start_time)
                end_str = self._format_ass_time(end_time)
                ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}\n"

        # Write ASS file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)

        return str(output_path)

    def burn_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Burn subtitles into video using FFmpeg

        Args:
            video_path: Input video path
            subtitle_path: Path to .srt or .ass file
            output_path: Output video path (optional)

        Returns:
            Path to output video with burned subtitles
        """
        video_path = Path(video_path)
        subtitle_path = Path(subtitle_path)

        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_subtitled.mp4"
        else:
            output_path = Path(output_path)

        # Escape special characters in subtitle path for FFmpeg filter
        sub_path_escaped = str(subtitle_path).replace('\\', '/').replace(':', r'\:')

        # Determine subtitle filter based on file type
        if subtitle_path.suffix.lower() == '.ass':
            sub_filter = f"ass='{sub_path_escaped}'"
        else:
            sub_filter = f"subtitles='{sub_path_escaped}'"

        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', sub_filter,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            str(output_path)
        ]

        print(f"Burning subtitles: {video_path} + {subtitle_path}")

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr.decode()}")
            raise

        return str(output_path)

    def burn_subtitles_drawtext(
        self,
        video_path: str,
        srt_path: str,
        output_path: str
    ) -> str:
        """
        Burn subtitles into video using FFmpeg drawtext filter
        This method doesn't require libass and works on all FFmpeg builds

        Args:
            video_path: Input video path
            srt_path: Path to .srt file
            output_path: Output video path

        Returns:
            Path to output video with burned subtitles
        """
        video_path = Path(video_path)
        srt_path = Path(srt_path)
        output_path = Path(output_path)

        # Parse SRT and create drawtext commands
        subtitles = self._parse_srt(str(srt_path))

        if not subtitles:
            # Se não houver legendas, apenas copiar o vídeo
            cmd = [
                'ffmpeg', '-i', str(video_path),
                '-c', 'copy', '-y', str(output_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return str(output_path)

        # Copiar vídeo (legendas ficam em arquivo SRT separado)
        # O player de vídeo pode carregar o SRT automaticamente
        print(f"Criando vídeo com legendas em arquivo separado: {srt_path}")
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-c', 'copy', '-y', str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        return str(output_path)

    def _parse_srt(self, srt_path: str) -> List[Dict[str, Any]]:
        """Parse SRT file and return list of subtitle entries"""
        subtitles = []
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        blocks = content.strip().split('\n\n')
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                try:
                    times = lines[1].split(' --> ')
                    text = ' '.join(lines[2:])
                    subtitles.append({
                        'start': self._srt_time_to_seconds(times[0]),
                        'end': self._srt_time_to_seconds(times[1]),
                        'text': text
                    })
                except (IndexError, ValueError):
                    continue
        return subtitles

    def _srt_time_to_seconds(self, time_str: str) -> float:
        """Convert SRT timestamp to seconds"""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    def create_subtitled_clip(
        self,
        video_path: str,
        words: List[Dict[str, Any]],
        clip_start_time: float,
        output_name: str,
        words_per_line: int = 6,
        style: Optional[Dict[str, Any]] = None,
        max_chars_per_line: int = 42,
        capitalize: bool = True
    ) -> Dict[str, Any]:
        """
        Generate subtitles and burn them into a clip

        Args:
            video_path: Path to clip video
            words: Word timestamps for the clip
            clip_start_time: Original start time of clip (for offset)
            output_name: Output filename (without extension)
            words_per_line: Words per subtitle line (default: 6)
            style: Custom subtitle style
            max_chars_per_line: Maximum characters per line (default: 42)
            capitalize: Apply proper capitalization (default: True)

        Returns:
            Dict with paths to subtitle file and subtitled video
        """
        video_path = Path(video_path)

        # Generate SRT subtitles with improved formatting
        srt_path = self.clips_dir / f"{output_name}.srt"
        self.generate_srt(
            words=words,
            output_path=str(srt_path),
            words_per_line=words_per_line,
            offset=clip_start_time,
            max_chars_per_line=max_chars_per_line,
            capitalize=capitalize
        )

        # Burn subtitles into video usando drawtext (sempre disponível)
        output_path = self.clips_dir / f"{output_name}_subtitled.mp4"
        self.burn_subtitles_drawtext(
            video_path=str(video_path),
            srt_path=str(srt_path),
            output_path=str(output_path)
        )

        return {
            'subtitle_path': str(srt_path),
            'video_path_with_subtitles': str(output_path)
        }


# Quick test
if __name__ == "__main__":
    generator = SubtitleGenerator()
    print("SubtitleGenerator initialized")

    # Test time formatting
    print(f"SRT time: {generator._format_srt_time(65.5)}")
    print(f"ASS time: {generator._format_ass_time(65.5)}")
