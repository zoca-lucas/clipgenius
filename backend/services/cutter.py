"""
ClipGenius - Video Cutter Service
Cuts video clips using FFmpeg
"""
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import CLIPS_DIR, OUTPUT_ASPECT_RATIO


class VideoCutter:
    """Service to cut video clips using FFmpeg"""

    def __init__(self):
        self.clips_dir = CLIPS_DIR

    def get_video_dimensions(self, video_path: str) -> Tuple[int, int]:
        """Get video width and height using ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            str(video_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        width, height = map(int, result.stdout.strip().split(','))
        return width, height

    def calculate_crop_for_vertical(
        self,
        width: int,
        height: int,
        target_ratio: str = "9:16"
    ) -> str:
        """
        Calculate FFmpeg crop filter for vertical video

        Args:
            width: Original video width
            height: Original video height
            target_ratio: Target aspect ratio (default 9:16 for shorts)

        Returns:
            FFmpeg crop filter string
        """
        # Parse target ratio
        ratio_parts = target_ratio.split(':')
        target_w = int(ratio_parts[0])
        target_h = int(ratio_parts[1])

        # Calculate target dimensions
        # We want to maximize the crop area while maintaining aspect ratio
        target_aspect = target_w / target_h
        source_aspect = width / height

        if source_aspect > target_aspect:
            # Source is wider - crop width
            new_width = int(height * target_aspect)
            new_height = height
            x_offset = (width - new_width) // 2
            y_offset = 0
        else:
            # Source is taller - crop height
            new_width = width
            new_height = int(width / target_aspect)
            x_offset = 0
            y_offset = (height - new_height) // 2

        return f"crop={new_width}:{new_height}:{x_offset}:{y_offset}"

    def cut_clip(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_name: str,
        convert_to_vertical: bool = True,
        target_resolution: Tuple[int, int] = (1080, 1920)
    ) -> Dict[str, Any]:
        """
        Cut a clip from video

        Args:
            video_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_name: Output filename (without extension)
            convert_to_vertical: Convert to 9:16 vertical format
            target_resolution: Target resolution (width, height)

        Returns:
            Dict with clip info and output path
        """
        video_path = Path(video_path)
        output_path = self.clips_dir / f"{output_name}.mp4"

        duration = end_time - start_time

        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),  # Seek before input (faster)
            '-i', str(video_path),
            '-t', str(duration),
            '-avoid_negative_ts', 'make_zero',
        ]

        if convert_to_vertical:
            # Get source dimensions
            width, height = self.get_video_dimensions(str(video_path))

            # Calculate crop filter
            crop_filter = self.calculate_crop_for_vertical(width, height)

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

        print(f"Cutting clip: {start_time:.1f}s - {end_time:.1f}s -> {output_path}")

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr.decode()}")
            raise

        return {
            'video_path': str(output_path),
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
        }

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

        subprocess.run(cmd, check=True, capture_output=True)

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

    # Test crop calculation
    crop = cutter.calculate_crop_for_vertical(1920, 1080, "9:16")
    print(f"Crop filter for 1920x1080 -> 9:16: {crop}")
