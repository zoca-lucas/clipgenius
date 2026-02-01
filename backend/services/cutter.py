"""
ClipGenius - Video Cutter Service
Cuts video clips using FFmpeg with multiple output format support
"""
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from config import CLIPS_DIR, OUTPUT_FORMATS, DEFAULT_OUTPUT_FORMAT


class VideoCutter:
    """Service to cut video clips using FFmpeg with multi-format support"""

    def __init__(self):
        self.clips_dir = CLIPS_DIR
        self.formats = OUTPUT_FORMATS

    def get_available_formats(self) -> List[Dict[str, Any]]:
        """Get list of available output formats"""
        return [
            {
                "id": fmt["id"],
                "name": fmt["name"],
                "aspect_ratio": fmt["aspect_ratio"],
                "resolution": fmt["resolution"],
                "platforms": fmt["platforms"],
                "description": fmt["description"]
            }
            for fmt in self.formats.values()
        ]

    def get_format_config(self, format_id: str) -> Dict[str, Any]:
        """Get configuration for a specific format"""
        if format_id not in self.formats:
            format_id = DEFAULT_OUTPUT_FORMAT
        return self.formats[format_id]

    def get_video_dimensions(self, video_path: str) -> Tuple[int, int]:
        """Get video width and height using ffprobe"""
        video_file = Path(video_path)
        if not video_file.exists():
            raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")

        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            str(video_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise RuntimeError(f"Erro ao obter dimensões do vídeo: {error_msg}")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Timeout ao obter dimensões do vídeo: {video_path}")
        except FileNotFoundError:
            raise RuntimeError("ffprobe não encontrado. Instale o FFmpeg.")

        output = result.stdout.strip()
        if not output or ',' not in output:
            raise RuntimeError(f"Saída inválida do ffprobe: {output}")

        try:
            width, height = map(int, output.split(','))
        except ValueError:
            raise RuntimeError(f"Não foi possível parsear dimensões: {output}")

        if width <= 0 or height <= 0:
            raise RuntimeError(f"Dimensões inválidas: {width}x{height}")

        return width, height

    def calculate_crop(
        self,
        width: int,
        height: int,
        target_ratio: str = "9:16"
    ) -> Tuple[int, int, int, int]:
        """
        Calculate crop dimensions for any aspect ratio

        Args:
            width: Original video width
            height: Original video height
            target_ratio: Target aspect ratio (e.g., "9:16", "1:1", "16:9", "4:5")

        Returns:
            Tuple of (crop_width, crop_height, x_offset, y_offset)
        """
        # Parse target ratio
        ratio_parts = target_ratio.split(':')
        target_w = int(ratio_parts[0])
        target_h = int(ratio_parts[1])

        # Calculate target dimensions
        target_aspect = target_w / target_h
        source_aspect = width / height

        if source_aspect > target_aspect:
            # Source is wider - crop width (center horizontally)
            new_width = int(height * target_aspect)
            new_height = height
            x_offset = (width - new_width) // 2
            y_offset = 0
        else:
            # Source is taller - crop height (center vertically)
            new_width = width
            new_height = int(width / target_aspect)
            x_offset = 0
            y_offset = (height - new_height) // 2

        return new_width, new_height, x_offset, y_offset

    def calculate_crop_for_vertical(
        self,
        width: int,
        height: int,
        target_ratio: str = "9:16"
    ) -> str:
        """
        Calculate FFmpeg crop filter string (legacy compatibility)

        Returns:
            FFmpeg crop filter string
        """
        crop_w, crop_h, x_off, y_off = self.calculate_crop(width, height, target_ratio)
        return f"crop={crop_w}:{crop_h}:{x_off}:{y_off}"

    def cut_clip(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_name: str,
        convert_to_vertical: bool = True,
        target_resolution: Tuple[int, int] = (1080, 1920),
        output_format: str = None
    ) -> Dict[str, Any]:
        """
        Cut a clip from video with configurable output format

        Args:
            video_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_name: Output filename (without extension)
            convert_to_vertical: Convert to target format (legacy param, use output_format instead)
            target_resolution: Target resolution (width, height) - overridden by output_format
            output_format: Format ID ("vertical", "square", "landscape", "portrait")

        Returns:
            Dict with clip info and output path
        """
        video_path = Path(video_path)
        duration = end_time - start_time

        # Determine output format
        if output_format:
            fmt_config = self.get_format_config(output_format)
            aspect_ratio = fmt_config["aspect_ratio"]
            target_resolution = fmt_config["resolution"]
            format_name = fmt_config["name"]
        else:
            # Legacy: use default vertical format if convert_to_vertical is True
            if convert_to_vertical:
                fmt_config = self.get_format_config(DEFAULT_OUTPUT_FORMAT)
                aspect_ratio = fmt_config["aspect_ratio"]
                format_name = fmt_config["name"]
            else:
                aspect_ratio = None
                format_name = "Original"

        # Add format suffix to filename
        format_suffix = f"_{output_format}" if output_format else ""
        output_path = self.clips_dir / f"{output_name}{format_suffix}.mp4"

        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),  # Seek before input (faster)
            '-i', str(video_path),
            '-t', str(duration),
            '-avoid_negative_ts', 'make_zero',
        ]

        if aspect_ratio:
            # Get source dimensions
            width, height = self.get_video_dimensions(str(video_path))

            # Calculate crop filter
            crop_w, crop_h, x_off, y_off = self.calculate_crop(width, height, aspect_ratio)
            crop_filter = f"crop={crop_w}:{crop_h}:{x_off}:{y_off}"

            # Scale to target resolution
            target_w, target_h = target_resolution
            scale_filter = f"scale={target_w}:{target_h}"

            # Combine filters
            video_filter = f"{crop_filter},{scale_filter}"

            cmd.extend([
                '-vf', video_filter,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
            ])
        else:
            # Just copy streams (fast, no re-encoding)
            cmd.extend([
                '-c', 'copy',
            ])

        cmd.extend([
            '-y',  # Overwrite
            str(output_path)
        ])

        print(f"Cutting clip ({format_name}): {start_time:.1f}s - {end_time:.1f}s -> {output_path}")

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # Clean up partial file on failure
            if output_path.exists():
                try:
                    output_path.unlink()
                    print(f"Cleaned up partial file: {output_path}")
                except Exception:
                    pass
            error_msg = e.stderr.decode() if e.stderr else str(e)
            print(f"FFmpeg error: {error_msg}")
            raise RuntimeError(f"Failed to cut clip: {error_msg}")

        # Verify output file was created
        if not output_path.exists():
            raise RuntimeError(f"FFmpeg completed but output file not found: {output_path}")

        return {
            'video_path': str(output_path),
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'format': output_format or (DEFAULT_OUTPUT_FORMAT if convert_to_vertical else 'original'),
            'resolution': target_resolution if aspect_ratio else None,
        }

    def cut_clip_multi_format(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_name: str,
        formats: List[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Cut a clip in multiple formats at once

        Args:
            video_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_name: Base output filename (without extension)
            formats: List of format IDs (default: all formats)

        Returns:
            Dict mapping format_id to clip info
        """
        if formats is None:
            formats = list(self.formats.keys())

        results = {}
        for fmt in formats:
            try:
                result = self.cut_clip(
                    video_path=video_path,
                    start_time=start_time,
                    end_time=end_time,
                    output_name=output_name,
                    output_format=fmt
                )
                results[fmt] = result
            except Exception as e:
                print(f"Failed to cut {fmt} format: {e}")
                results[fmt] = {"error": str(e)}

        return results

    def cut_clip_fast(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_name: str
    ) -> Dict[str, Any]:
        """
        Cut clip without re-encoding (very fast, but no format conversion)
        """
        video_path = Path(video_path)
        output_path = self.clips_dir / f"{output_name}.mp4"

        duration = end_time - start_time

        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', str(video_path),
            '-t', str(duration),
            '-c', 'copy',  # No re-encoding
            '-avoid_negative_ts', 'make_zero',
            '-y',
            str(output_path)
        ]

        print(f"Fast cutting clip: {start_time:.1f}s - {end_time:.1f}s")

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # Clean up partial file on failure
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception:
                    pass
            error_msg = e.stderr.decode() if e.stderr else str(e)
            print(f"FFmpeg fast cut error: {error_msg}")
            raise RuntimeError(f"Failed to fast cut clip: {error_msg}")

        return {
            'video_path': str(output_path),
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
        }


# Quick test
if __name__ == "__main__":
    cutter = VideoCutter()
    print("VideoCutter initialized")
    print()

    # Show available formats
    print("Available output formats:")
    for fmt in cutter.get_available_formats():
        print(f"  - {fmt['id']}: {fmt['name']} ({fmt['aspect_ratio']}) -> {fmt['resolution']}")
        print(f"    Platforms: {', '.join(fmt['platforms'])}")
    print()

    # Test crop calculations for different formats
    source_w, source_h = 1920, 1080
    print(f"Crop calculations for {source_w}x{source_h} source:")

    for fmt_id, fmt in OUTPUT_FORMATS.items():
        crop_w, crop_h, x_off, y_off = cutter.calculate_crop(source_w, source_h, fmt['aspect_ratio'])
        print(f"  {fmt['name']}: crop={crop_w}x{crop_h} at ({x_off}, {y_off})")
