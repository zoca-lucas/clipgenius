"""
ClipGenius - Subtitle Generator Service
Generates and burns subtitles into video clips
"""
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import (
    CLIPS_DIR,
    SUBTITLE_KARAOKE_ENABLED,
    SUBTITLE_HIGHLIGHT_COLOR,
    SUBTITLE_INACTIVE_COLOR,
    SUBTITLE_SCALE_EFFECT,
    SUBTITLE_SCALE_AMOUNT,
)


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

    # Karaoke style - TikTok/Reels viral effect
    KARAOKE_STYLE = {
        'font_name': 'Arial',
        'font_size': 36,
        'primary_color': SUBTITLE_HIGHLIGHT_COLOR,    # Active word color (yellow)
        'secondary_color': SUBTITLE_INACTIVE_COLOR,   # Inactive words (white)
        'outline_color': '&H00000000',
        'back_color': '&H80000000',
        'bold': True,
        'outline': 4,
        'shadow': 2,
        'alignment': 2,
        'margin_v': 100,
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

    def _generate_karaoke_dialogue(
        self,
        words: List[Dict[str, Any]],
        highlight_color: str = None,
        scale_effect: bool = True,
        scale_amount: int = 110,
        capitalize: bool = True
    ) -> str:
        r"""
        Generate a single ASS dialogue line with karaoke timing tags.

        Each word gets a \k tag for timing, color highlight, and optional scale animation.
        Example output: {\k50\1c&H00FFFF&\t(0,500,\fscx110\fscy110)}Olá {\k40}pessoal

        Args:
            words: List of word dicts with 'word', 'start', 'end' (already offset-adjusted)
            highlight_color: Color for active word (ASS format)
            scale_effect: Whether to add scale pop effect
            scale_amount: Scale percentage (e.g., 110 = 110%)
            capitalize: Apply proper capitalization

        Returns:
            ASS dialogue text with karaoke tags
        """
        if not words:
            return ""

        highlight_color = highlight_color or SUBTITLE_HIGHLIGHT_COLOR
        dialogue_parts = []

        for i, word_dict in enumerate(words):
            word = word_dict.get('word', '').strip()
            if not word:
                continue

            start = word_dict.get('start', 0)
            end = word_dict.get('end', 0)

            # Duration in centiseconds (ASS \k tag unit)
            duration_cs = max(1, int((end - start) * 100))

            # Build the karaoke tag for this word
            # \k<dur> = karaoke timing (duration before highlight)
            # \1c&HCOLOR& = primary color change
            # \t(t1,t2,\fscx\fscy) = animation for scale effect
            tag = f"\\k{duration_cs}"

            # Add color tag
            tag += f"\\1c{highlight_color}"

            # Add scale animation if enabled
            if scale_effect:
                # Animation duration in ms (use word duration)
                anim_duration = int((end - start) * 1000)
                anim_duration = max(100, min(anim_duration, 500))  # Clamp between 100-500ms
                tag += f"\\t(0,{anim_duration},\\fscx{scale_amount}\\fscy{scale_amount})"
                # Reset scale after animation
                tag += f"\\t({anim_duration},{anim_duration + 50},\\fscx100\\fscy100)"

            dialogue_parts.append(f"{{{tag}}}{word}")

        # Join words with spaces
        text = ' '.join(dialogue_parts)

        # Apply capitalization to the visible text (first word only)
        if capitalize and text:
            # Replace the first lowercase letter after tags with uppercase
            def capitalize_first(match):
                return match.group(1) + match.group(2).upper()
            text = re.sub(r'(\{[^}]*\})([a-záàâãéêíóôõúç])', capitalize_first, text, count=1)

        return text

    def generate_ass_karaoke(
        self,
        words: List[Dict[str, Any]],
        output_path: str,
        words_per_line: int = 6,
        offset: float = 0,
        style: Optional[Dict[str, Any]] = None,
        video_width: int = 1080,
        video_height: int = 1920,
        max_chars_per_line: int = 42,
        capitalize: bool = True,
        highlight_color: str = None,
        scale_effect: bool = None,
        scale_amount: int = None
    ) -> str:
        """
        Generate ASS subtitle file with karaoke word-by-word highlighting effect.

        Creates TikTok/Reels style subtitles where each word highlights as it's spoken.

        Args:
            words: List of word dicts with 'word', 'start', 'end'
            output_path: Output path for .ass file
            words_per_line: Max words per subtitle line
            offset: Time offset
            style: Custom style dict (merged with KARAOKE_STYLE)
            video_width: Video width for positioning
            video_height: Video height for positioning
            max_chars_per_line: Maximum characters per line
            capitalize: Apply proper capitalization
            highlight_color: Color for active word (overrides config)
            scale_effect: Whether to add scale pop effect (overrides config)
            scale_amount: Scale percentage (overrides config)

        Returns:
            Path to generated ASS file
        """
        output_path = Path(output_path)

        # Use config defaults if not specified
        highlight_color = highlight_color or SUBTITLE_HIGHLIGHT_COLOR
        scale_effect = scale_effect if scale_effect is not None else SUBTITLE_SCALE_EFFECT
        scale_amount = scale_amount or SUBTITLE_SCALE_AMOUNT

        # Merge styles
        style = {**self.KARAOKE_STYLE, **(style or {})}

        # ASS header with karaoke style
        ass_content = f"""[Script Info]
Title: ClipGenius Karaoke Subtitles
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,{style['font_name']},{style['font_size']},{style['secondary_color']},&H000000FF,{style['outline_color']},{style['back_color']},{-1 if style['bold'] else 0},0,0,0,100,100,0,0,1,{style['outline']},{style['shadow']},{style['alignment']},10,10,{style['margin_v']},1

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

            # Adjust word timings for the chunk (apply offset)
            adjusted_chunk = []
            for word_dict in chunk:
                adjusted_word = word_dict.copy()
                adjusted_word['start'] = max(0, word_dict.get('start', 0) - offset)
                adjusted_word['end'] = max(0, word_dict.get('end', 0) - offset)
                adjusted_chunk.append(adjusted_word)

            # Generate karaoke dialogue with word-by-word timing
            karaoke_text = self._generate_karaoke_dialogue(
                words=adjusted_chunk,
                highlight_color=highlight_color,
                scale_effect=scale_effect,
                scale_amount=scale_amount,
                capitalize=capitalize
            )

            if karaoke_text:
                start_str = self._format_ass_time(start_time)
                end_str = self._format_ass_time(end_time)
                ass_content += f"Dialogue: 0,{start_str},{end_str},Karaoke,,0,0,0,,{karaoke_text}\n"

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
    ) -> Dict[str, Any]:
        """
        Burn subtitles into video using FFmpeg subtitles filter

        Args:
            video_path: Input video path
            srt_path: Path to .srt file
            output_path: Output video path

        Returns:
            Dict with 'path' and 'subtitles_burned' status
        """
        video_path = Path(video_path)
        srt_path = Path(srt_path)
        output_path = Path(output_path)

        # Parse SRT to check if we have subtitles
        subtitles = []
        try:
            subtitles = self._parse_srt(str(srt_path))
        except Exception as e:
            print(f"⚠️  Erro ao ler arquivo SRT: {e}")

        if not subtitles:
            print("⚠️  Nenhuma legenda encontrada - vídeo será copiado sem legendas")
            cmd = [
                'ffmpeg', '-i', str(video_path),
                '-c', 'copy', '-y', str(output_path)
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Erro ao copiar vídeo: {e.stderr.decode() if e.stderr else str(e)}")
            return {'path': str(output_path), 'subtitles_burned': False, 'message': 'Nenhuma legenda encontrada'}

        # Try to burn subtitles using subtitles filter (requires libass)
        sub_path_escaped = str(srt_path).replace('\\', '/').replace(':', r'\:').replace("'", r"\'")

        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-vf', f"subtitles='{sub_path_escaped}'",
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-y', str(output_path)
        ]

        print(f"🎬 Queimando legendas no vídeo: {len(subtitles)} legendas")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
            print("✅ Legendas queimadas com sucesso!")
            return {'path': str(output_path), 'subtitles_burned': True, 'message': 'Legendas queimadas com sucesso'}
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            print(f"⚠️  Não foi possível queimar legendas (libass pode não estar disponível): {error_msg[:200]}")

            # Fallback: copy video without burning subtitles
            print("📄 Criando vídeo sem legendas queimadas (arquivo SRT disponível separadamente)")
            cmd_fallback = [
                'ffmpeg', '-i', str(video_path),
                '-c', 'copy', '-y', str(output_path)
            ]
            try:
                subprocess.run(cmd_fallback, check=True, capture_output=True)
            except subprocess.CalledProcessError as e2:
                raise RuntimeError(f"Erro ao copiar vídeo: {e2.stderr.decode() if e2.stderr else str(e2)}")

            return {
                'path': str(output_path),
                'subtitles_burned': False,
                'message': 'Legendas não queimadas (arquivo SRT disponível separadamente)',
                'srt_path': str(srt_path)
            }

    def _parse_srt(self, srt_path: str) -> List[Dict[str, Any]]:
        """Parse SRT file and return list of subtitle entries"""
        subtitles = []
        srt_file = Path(srt_path)

        if not srt_file.exists():
            print(f"⚠️  Arquivo SRT não encontrado: {srt_path}")
            return subtitles

        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError) as e:
            print(f"⚠️  Erro ao ler arquivo SRT: {e}")
            return subtitles

        if not content.strip():
            print(f"⚠️  Arquivo SRT vazio: {srt_path}")
            return subtitles

        blocks = content.strip().split('\n\n')
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                try:
                    times = lines[1].split(' --> ')
                    if len(times) != 2:
                        continue
                    text = ' '.join(lines[2:])
                    subtitles.append({
                        'start': self._srt_time_to_seconds(times[0]),
                        'end': self._srt_time_to_seconds(times[1]),
                        'text': text
                    })
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Erro ao parsear bloco SRT: {e}")
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
        capitalize: bool = True,
        enable_karaoke: bool = None
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
            enable_karaoke: Enable karaoke word-by-word highlighting (default: from config)

        Returns:
            Dict with paths to subtitle file and subtitled video
        """
        video_path = Path(video_path)

        # Use config default if not specified
        if enable_karaoke is None:
            enable_karaoke = SUBTITLE_KARAOKE_ENABLED

        if enable_karaoke:
            # Generate ASS subtitles with karaoke effect (TikTok/Reels style)
            ass_path = self.clips_dir / f"{output_name}.ass"
            self.generate_ass_karaoke(
                words=words,
                output_path=str(ass_path),
                words_per_line=words_per_line,
                offset=clip_start_time,
                style=style,
                max_chars_per_line=max_chars_per_line,
                capitalize=capitalize
            )
            subtitle_path = ass_path

            # Burn ASS subtitles into video
            output_path = self.clips_dir / f"{output_name}_subtitled.mp4"
            burn_result = self.burn_subtitles(
                video_path=str(video_path),
                subtitle_path=str(ass_path),
                output_path=str(output_path)
            )

            return {
                'subtitle_path': str(ass_path),
                'video_path_with_subtitles': str(burn_result),
                'subtitles_burned': True,
                'subtitle_message': 'Legendas karaoke queimadas com sucesso',
                'karaoke_enabled': True
            }
        else:
            # Generate SRT subtitles with simple formatting (original behavior)
            srt_path = self.clips_dir / f"{output_name}.srt"
            self.generate_srt(
                words=words,
                output_path=str(srt_path),
                words_per_line=words_per_line,
                offset=clip_start_time,
                max_chars_per_line=max_chars_per_line,
                capitalize=capitalize
            )

            # Burn subtitles into video
            output_path = self.clips_dir / f"{output_name}_subtitled.mp4"
            burn_result = self.burn_subtitles_drawtext(
                video_path=str(video_path),
                srt_path=str(srt_path),
                output_path=str(output_path)
            )

            return {
                'subtitle_path': str(srt_path),
                'video_path_with_subtitles': burn_result['path'],
                'subtitles_burned': burn_result.get('subtitles_burned', False),
                'subtitle_message': burn_result.get('message', ''),
                'karaoke_enabled': False
            }


# Quick test
if __name__ == "__main__":
    generator = SubtitleGenerator()
    print("SubtitleGenerator initialized")

    # Test time formatting
    print(f"SRT time: {generator._format_srt_time(65.5)}")
    print(f"ASS time: {generator._format_ass_time(65.5)}")
