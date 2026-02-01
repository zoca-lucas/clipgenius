"""
ClipGenius - Video Editor Service
Provides video editing capabilities: trim, subtitle editing, text overlays, filters
"""
import subprocess
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from config import VIDEOS_DIR, CLIPS_DIR


@dataclass
class SubtitleStyle:
    """Subtitle styling options"""
    font_name: str = "Arial"
    font_size: int = 36
    primary_color: str = "&HFFFFFF"  # White (ASS format: &HBBGGRR)
    outline_color: str = "&H000000"  # Black
    highlight_color: str = "&H00FFFF"  # Yellow/Cyan
    outline_width: int = 2
    shadow: int = 1
    margin_v: int = 80
    alignment: int = 2  # Bottom center


@dataclass
class TextOverlay:
    """Text overlay configuration"""
    text: str
    x: int  # Position X (pixels or percentage with %)
    y: int  # Position Y
    font_size: int = 48
    font_color: str = "white"
    font_name: str = "Arial"
    start_time: float = 0
    end_time: Optional[float] = None  # None = until end
    background_color: Optional[str] = None
    background_opacity: float = 0.5


class VideoEditor:
    """Service for editing video clips"""

    # Available filters
    FILTERS = {
        "none": None,
        "grayscale": "colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3",
        "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
        "warm": "colortemperature=temperature=6500",
        "cool": "colortemperature=temperature=10000",
        "vibrant": "eq=saturation=1.5",
        "muted": "eq=saturation=0.7",
        "bright": "eq=brightness=0.1",
        "dark": "eq=brightness=-0.1",
        "contrast": "eq=contrast=1.3",
        "vintage": "curves=vintage",
        "blur": "boxblur=2:1",
        "sharpen": "unsharp=5:5:1.0:5:5:0.0",
    }

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to get video info: {result.stderr}")

        data = json.loads(result.stdout)

        # Extract video stream info
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break

        if not video_stream:
            raise Exception("No video stream found")

        return {
            "duration": float(data['format'].get('duration', 0)),
            "width": video_stream.get('width'),
            "height": video_stream.get('height'),
            "fps": eval(video_stream.get('r_frame_rate', '30/1')),
            "codec": video_stream.get('codec_name'),
            "bitrate": int(data['format'].get('bit_rate', 0)),
        }

    def trim_clip(
        self,
        input_path: str,
        output_name: str,
        start_time: float,
        end_time: float,
        filter_name: str = "none"
    ) -> Dict[str, Any]:
        """
        Trim a clip to new start/end times with optional filter.

        Args:
            input_path: Path to input video
            output_name: Name for output file (without extension)
            start_time: New start time in seconds
            end_time: New end time in seconds
            filter_name: Optional filter to apply

        Returns:
            Dict with output path and metadata
        """
        output_path = CLIPS_DIR / f"{output_name}_edited.mp4"
        duration = end_time - start_time

        # Build filter chain
        filters = []

        # Add color filter if specified
        if filter_name != "none" and filter_name in self.FILTERS:
            filter_value = self.FILTERS[filter_name]
            if filter_value:
                filters.append(filter_value)

        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', input_path,
            '-t', str(duration),
        ]

        if filters:
            cmd.extend(['-vf', ','.join(filters)])

        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            str(output_path)
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg trim failed: {result.stderr}")

        return {
            "video_path": str(output_path),
            "duration": duration,
            "start_time": start_time,
            "end_time": end_time,
            "filter": filter_name
        }

    def apply_filter(
        self,
        input_path: str,
        output_name: str,
        filter_name: str
    ) -> Dict[str, Any]:
        """
        Apply a visual filter to the entire video.

        Args:
            input_path: Path to input video
            output_name: Name for output file
            filter_name: Filter to apply

        Returns:
            Dict with output path
        """
        if filter_name not in self.FILTERS:
            raise ValueError(f"Unknown filter: {filter_name}. Available: {list(self.FILTERS.keys())}")

        output_path = CLIPS_DIR / f"{output_name}_{filter_name}.mp4"

        filter_value = self.FILTERS[filter_name]

        cmd = [
            'ffmpeg',
            '-i', input_path,
        ]

        if filter_value:
            cmd.extend(['-vf', filter_value])

        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            str(output_path)
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg filter failed: {result.stderr}")

        return {
            "video_path": str(output_path),
            "filter": filter_name
        }

    def add_text_overlay(
        self,
        input_path: str,
        output_name: str,
        overlays: List[TextOverlay]
    ) -> Dict[str, Any]:
        """
        Add text overlays to video.

        Args:
            input_path: Path to input video
            output_name: Name for output file
            overlays: List of text overlays to add

        Returns:
            Dict with output path
        """
        output_path = CLIPS_DIR / f"{output_name}_text.mp4"

        # Build drawtext filter for each overlay
        drawtext_filters = []

        for overlay in overlays:
            # Escape special characters in text
            escaped_text = overlay.text.replace("'", "\\'").replace(":", "\\:")

            filter_parts = [
                f"drawtext=text='{escaped_text}'",
                f"fontsize={overlay.font_size}",
                f"fontcolor={overlay.font_color}",
                f"x={overlay.x}",
                f"y={overlay.y}",
            ]

            if overlay.font_name:
                filter_parts.append(f"font='{overlay.font_name}'")

            # Add timing if specified
            if overlay.start_time > 0 or overlay.end_time:
                enable_expr = f"between(t,{overlay.start_time},{overlay.end_time or 9999})"
                filter_parts.append(f"enable='{enable_expr}'")

            # Add background box if specified
            if overlay.background_color:
                filter_parts.append(f"box=1")
                filter_parts.append(f"boxcolor={overlay.background_color}@{overlay.background_opacity}")
                filter_parts.append(f"boxborderw=10")

            drawtext_filters.append(':'.join(filter_parts))

        # Combine all drawtext filters
        vf = ','.join(drawtext_filters)

        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', vf,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg text overlay failed: {result.stderr}")

        return {
            "video_path": str(output_path),
            "overlays_count": len(overlays)
        }

    def update_subtitles(
        self,
        input_path: str,
        output_name: str,
        subtitle_data: List[Dict[str, Any]],
        style: Optional[SubtitleStyle] = None
    ) -> Dict[str, Any]:
        """
        Create new subtitles and burn them into the video.

        Args:
            input_path: Path to input video
            output_name: Name for output file
            subtitle_data: List of subtitle entries with start, end, text
            style: Optional subtitle styling

        Returns:
            Dict with output paths
        """
        if style is None:
            style = SubtitleStyle()

        # Generate ASS subtitle file
        subtitle_path = CLIPS_DIR / f"{output_name}_edited.ass"
        output_path = CLIPS_DIR / f"{output_name}_subtitled.mp4"

        # Create ASS file content
        ass_content = self._generate_ass_file(subtitle_data, style)

        with open(subtitle_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)

        # Burn subtitles into video
        # Escape path for FFmpeg filter
        escaped_subtitle_path = str(subtitle_path).replace('\\', '/').replace(':', '\\:')

        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f"subtitles='{escaped_subtitle_path}'",
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg subtitle burn failed: {result.stderr}")

        return {
            "video_path": str(output_path),
            "subtitle_path": str(subtitle_path),
            "subtitle_count": len(subtitle_data)
        }

    def _generate_ass_file(
        self,
        subtitle_data: List[Dict[str, Any]],
        style: SubtitleStyle
    ) -> str:
        """Generate ASS subtitle file content"""

        # ASS file header
        header = f"""[Script Info]
Title: ClipGenius Edited Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style.font_name},{style.font_size},{style.primary_color},&H000000FF,{style.outline_color},&H00000000,1,0,0,0,100,100,0,0,1,{style.outline_width},{style.shadow},{style.alignment},10,10,{style.margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        # Generate dialogue lines
        dialogues = []
        for entry in subtitle_data:
            start = self._seconds_to_ass_time(entry['start'])
            end = self._seconds_to_ass_time(entry['end'])
            text = entry['text'].replace('\n', '\\N')

            dialogues.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

        return header + '\n'.join(dialogues)

    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"

    def apply_edits(
        self,
        input_path: str,
        output_name: str,
        trim_start: Optional[float] = None,
        trim_end: Optional[float] = None,
        filter_name: str = "none",
        text_overlays: Optional[List[TextOverlay]] = None,
        subtitle_data: Optional[List[Dict[str, Any]]] = None,
        subtitle_style: Optional[SubtitleStyle] = None
    ) -> Dict[str, Any]:
        """
        Apply multiple edits in a single pass for efficiency.

        Args:
            input_path: Path to input video
            output_name: Name for output file
            trim_start: Optional new start time
            trim_end: Optional new end time
            filter_name: Optional visual filter
            text_overlays: Optional text overlays
            subtitle_data: Optional new subtitles
            subtitle_style: Optional subtitle styling

        Returns:
            Dict with output path and applied edits
        """
        output_path = CLIPS_DIR / f"{output_name}_final.mp4"

        # Build complex filter
        filters = []

        # Color filter
        if filter_name != "none" and filter_name in self.FILTERS:
            filter_value = self.FILTERS[filter_name]
            if filter_value:
                filters.append(filter_value)

        # Text overlays
        if text_overlays:
            for overlay in text_overlays:
                escaped_text = overlay.text.replace("'", "\\'").replace(":", "\\:")

                filter_parts = [
                    f"drawtext=text='{escaped_text}'",
                    f"fontsize={overlay.font_size}",
                    f"fontcolor={overlay.font_color}",
                    f"x={overlay.x}",
                    f"y={overlay.y}",
                ]

                if overlay.start_time > 0 or overlay.end_time:
                    enable_expr = f"between(t,{overlay.start_time},{overlay.end_time or 9999})"
                    filter_parts.append(f"enable='{enable_expr}'")

                if overlay.background_color:
                    filter_parts.append(f"box=1")
                    filter_parts.append(f"boxcolor={overlay.background_color}@{overlay.background_opacity}")
                    filter_parts.append(f"boxborderw=10")

                filters.append(':'.join(filter_parts))

        # Build command
        cmd = ['ffmpeg']

        # Add trim start
        if trim_start is not None:
            cmd.extend(['-ss', str(trim_start)])

        cmd.extend(['-i', input_path])

        # Add duration/trim end
        if trim_start is not None and trim_end is not None:
            duration = trim_end - trim_start
            cmd.extend(['-t', str(duration)])
        elif trim_end is not None:
            cmd.extend(['-t', str(trim_end)])

        # Handle subtitles (needs separate pass due to subtitle filter complexity)
        temp_subtitle_path = None
        if subtitle_data:
            style = subtitle_style or SubtitleStyle()
            temp_subtitle_path = CLIPS_DIR / f"{output_name}_temp.ass"
            ass_content = self._generate_ass_file(subtitle_data, style)
            with open(temp_subtitle_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)

            escaped_path = str(temp_subtitle_path).replace('\\', '/').replace(':', '\\:')
            filters.append(f"subtitles='{escaped_path}'")

        # Add filters
        if filters:
            cmd.extend(['-vf', ','.join(filters)])

        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            str(output_path)
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Clean up temp subtitle file
        if temp_subtitle_path and temp_subtitle_path.exists():
            temp_subtitle_path.unlink()

        if result.returncode != 0:
            raise Exception(f"FFmpeg edit failed: {result.stderr}")

        return {
            "video_path": str(output_path),
            "trim": {"start": trim_start, "end": trim_end} if trim_start or trim_end else None,
            "filter": filter_name,
            "text_overlays": len(text_overlays) if text_overlays else 0,
            "subtitles": len(subtitle_data) if subtitle_data else 0
        }

    def generate_preview_frame(
        self,
        video_path: str,
        timestamp: float,
        output_name: str
    ) -> str:
        """
        Generate a preview frame at the specified timestamp.

        Args:
            video_path: Path to video
            timestamp: Time in seconds
            output_name: Name for output image

        Returns:
            Path to generated image
        """
        output_path = CLIPS_DIR / f"{output_name}_preview.jpg"

        cmd = [
            'ffmpeg',
            '-ss', str(timestamp),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg preview failed: {result.stderr}")

        return str(output_path)

    def get_available_filters(self) -> List[Dict[str, str]]:
        """Get list of available filters with descriptions"""
        return [
            {"id": "none", "name": "Original", "description": "No filter applied"},
            {"id": "grayscale", "name": "Preto e Branco", "description": "Converte para escala de cinza"},
            {"id": "sepia", "name": "Sepia", "description": "Tom vintage amarronzado"},
            {"id": "warm", "name": "Quente", "description": "Tons mais quentes e aconchegantes"},
            {"id": "cool", "name": "Frio", "description": "Tons azulados e frios"},
            {"id": "vibrant", "name": "Vibrante", "description": "Cores mais saturadas"},
            {"id": "muted", "name": "Suave", "description": "Cores mais suaves"},
            {"id": "bright", "name": "Claro", "description": "Aumenta o brilho"},
            {"id": "dark", "name": "Escuro", "description": "Diminui o brilho"},
            {"id": "contrast", "name": "Contraste", "description": "Aumenta o contraste"},
            {"id": "vintage", "name": "Vintage", "description": "Efeito retrô"},
            {"id": "blur", "name": "Desfoque", "description": "Aplica desfoque leve"},
            {"id": "sharpen", "name": "Nitidez", "description": "Aumenta a nitidez"},
        ]


# Create singleton instance
video_editor = VideoEditor()
