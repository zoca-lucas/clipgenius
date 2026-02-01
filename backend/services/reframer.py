"""
ClipGenius - AI Reframe Service
Intelligent face tracking and auto-reframing for vertical video
Uses MediaPipe for face detection and smooth tracking
"""
import subprocess
import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Try new MediaPipe Tasks API first (0.10.10+)
MEDIAPIPE_AVAILABLE = False
MEDIAPIPE_LEGACY = False

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision
    MEDIAPIPE_AVAILABLE = True
    MEDIAPIPE_LEGACY = False
except ImportError:
    try:
        # Try legacy API (older versions)
        import mediapipe as mp
        if hasattr(mp, 'solutions'):
            MEDIAPIPE_AVAILABLE = True
            MEDIAPIPE_LEGACY = True
    except ImportError:
        pass

if not MEDIAPIPE_AVAILABLE or not CV2_AVAILABLE:
    print("Warning: mediapipe/opencv not available. AI Reframe will use center crop fallback.")

from config import CLIPS_DIR


# Model file for MediaPipe Tasks API
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
MODEL_DIR = Path(__file__).parent.parent / "models_cache"
MODEL_PATH = MODEL_DIR / "blaze_face_short_range.tflite"


def ensure_model_downloaded():
    """Download the face detection model if not present"""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if not MODEL_PATH.exists():
        print(f"Downloading face detection model to {MODEL_PATH}...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded successfully.")
    return str(MODEL_PATH)


@dataclass
class FacePosition:
    """Represents a detected face position in a frame"""
    frame_num: int
    timestamp: float
    center_x: float  # Normalized 0-1
    center_y: float  # Normalized 0-1
    width: float     # Normalized face width
    height: float    # Normalized face height
    confidence: float


class AIReframer:
    """
    AI-powered video reframing service that tracks faces/subjects
    and creates smooth, centered crops for vertical video format.
    """

    def __init__(self):
        self.clips_dir = CLIPS_DIR
        self.face_detector = None

        if MEDIAPIPE_AVAILABLE and CV2_AVAILABLE:
            if not MEDIAPIPE_LEGACY:
                # New MediaPipe Tasks API (0.10.10+)
                try:
                    model_path = ensure_model_downloaded()
                    base_options = mp_tasks.BaseOptions(model_asset_path=model_path)
                    options = vision.FaceDetectorOptions(
                        base_options=base_options,
                        min_detection_confidence=0.5
                    )
                    self.face_detector = vision.FaceDetector.create_from_options(options)
                    print("AI Reframe: Using MediaPipe Tasks API")
                except Exception as e:
                    print(f"Warning: Could not initialize MediaPipe Tasks: {e}")
                    self.face_detector = None
            else:
                # Legacy MediaPipe API
                try:
                    self.mp_face_detection = mp.solutions.face_detection
                    self.face_detector = self.mp_face_detection.FaceDetection(
                        model_selection=1,
                        min_detection_confidence=0.5
                    )
                    print("AI Reframe: Using MediaPipe Legacy API")
                except Exception as e:
                    print(f"Warning: Could not initialize MediaPipe Legacy: {e}")
                    self.face_detector = None

    def _detect_face_in_frame(self, rgb_frame: np.ndarray) -> Optional[Tuple[float, float, float, float, float]]:
        """
        Detect face in a single frame using available MediaPipe API.

        Returns:
            Tuple of (center_x, center_y, width, height, confidence) or None if no face detected
        """
        if self.face_detector is None:
            return None

        if not MEDIAPIPE_LEGACY:
            # New Tasks API
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            results = self.face_detector.detect(mp_image)

            if results.detections:
                best = max(results.detections, key=lambda d: d.categories[0].score)
                bbox = best.bounding_box

                # Convert to normalized coordinates
                h, w = rgb_frame.shape[:2]
                center_x = (bbox.origin_x + bbox.width / 2) / w
                center_y = (bbox.origin_y + bbox.height / 2) / h
                norm_width = bbox.width / w
                norm_height = bbox.height / h
                confidence = best.categories[0].score

                return (center_x, center_y, norm_width, norm_height, confidence)
        else:
            # Legacy API
            results = self.face_detector.process(rgb_frame)

            if results.detections:
                best = max(results.detections, key=lambda d: d.score[0])
                bbox = best.location_data.relative_bounding_box

                center_x = bbox.xmin + bbox.width / 2
                center_y = bbox.ymin + bbox.height / 2

                return (center_x, center_y, bbox.width, bbox.height, best.score[0])

        return None

    def detect_faces_in_video(
        self,
        video_path: str,
        sample_interval: float = 0.5,  # Sample every 0.5 seconds
        start_time: float = 0,
        end_time: Optional[float] = None
    ) -> List[FacePosition]:
        """
        Detect faces throughout the video at regular intervals.

        Args:
            video_path: Path to video file
            sample_interval: Time between samples in seconds
            start_time: Start time for detection
            end_time: End time for detection (None = full video)

        Returns:
            List of FacePosition objects
        """
        if not MEDIAPIPE_AVAILABLE or not CV2_AVAILABLE or self.face_detector is None:
            return []

        cap = None
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            if end_time is None:
                end_time = duration

            face_positions = []
            sample_frames = int(sample_interval * fps)

            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)

            print(f"Detecting faces from {start_time:.1f}s to {end_time:.1f}s (every {sample_interval}s)")

            frame_num = start_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            while frame_num < end_frame:
                ret, frame = cap.read()
                if not ret:
                    break

                # Convert to RGB for MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                timestamp = frame_num / fps

                face_data = self._detect_face_in_frame(rgb_frame)

                if face_data:
                    center_x, center_y, width, height, confidence = face_data
                    face_positions.append(FacePosition(
                        frame_num=frame_num,
                        timestamp=timestamp,
                        center_x=center_x,
                        center_y=center_y,
                        width=width,
                        height=height,
                        confidence=confidence
                    ))

                # Skip to next sample
                frame_num += sample_frames
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

            print(f"Detected {len(face_positions)} face positions")
            return face_positions

        finally:
            # Always release VideoCapture
            if cap is not None:
                cap.release()

    def smooth_positions(
        self,
        positions: List[FacePosition],
        smoothing_window: int = 5
    ) -> List[FacePosition]:
        """
        Apply smoothing to face positions to avoid jerky movements.
        Uses moving average for smooth transitions.
        """
        if len(positions) < 3:
            return positions

        # Extract coordinates
        x_coords = [p.center_x for p in positions]
        y_coords = [p.center_y for p in positions]

        # Apply moving average
        def moving_average(data, window):
            weights = np.ones(window) / window
            # Pad data to handle edges
            padded = np.pad(data, (window//2, window//2), mode='edge')
            smoothed = np.convolve(padded, weights, mode='valid')
            return smoothed[:len(data)]

        smooth_x = moving_average(np.array(x_coords), smoothing_window)
        smooth_y = moving_average(np.array(y_coords), smoothing_window)

        # Create smoothed positions
        smoothed = []
        for i, pos in enumerate(positions):
            smoothed.append(FacePosition(
                frame_num=pos.frame_num,
                timestamp=pos.timestamp,
                center_x=float(smooth_x[i]),
                center_y=float(smooth_y[i]),
                width=pos.width,
                height=pos.height,
                confidence=pos.confidence
            ))

        return smoothed

    def interpolate_positions(
        self,
        positions: List[FacePosition],
        fps: float,
        start_time: float,
        end_time: float
    ) -> List[Tuple[float, float, float]]:
        """
        Interpolate face positions for every frame.

        Returns:
            List of (timestamp, center_x, center_y) for each frame
        """
        if not positions:
            # No faces detected - return center positions
            num_frames = int((end_time - start_time) * fps)
            return [(start_time + i/fps, 0.5, 0.4) for i in range(num_frames)]

        # Create interpolation arrays
        timestamps = np.array([p.timestamp for p in positions])
        x_coords = np.array([p.center_x for p in positions])
        y_coords = np.array([p.center_y for p in positions])

        # Generate frame timestamps
        num_frames = int((end_time - start_time) * fps)
        frame_times = np.linspace(start_time, end_time, num_frames)

        # Interpolate
        interp_x = np.interp(frame_times, timestamps, x_coords)
        interp_y = np.interp(frame_times, timestamps, y_coords)

        return list(zip(frame_times, interp_x, interp_y))

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video dimensions and FPS using ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate',
            '-of', 'json',
            str(video_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        stream = data['streams'][0]

        # Parse frame rate (can be "30/1" or "29.97")
        fps_str = stream['r_frame_rate']
        if '/' in fps_str:
            num, den = map(int, fps_str.split('/'))
            fps = num / den
        else:
            fps = float(fps_str)

        return {
            'width': stream['width'],
            'height': stream['height'],
            'fps': fps
        }

    def calculate_dynamic_crop(
        self,
        source_width: int,
        source_height: int,
        face_x: float,  # Normalized 0-1
        face_y: float,  # Normalized 0-1
        target_ratio: float = 9/16,
        padding: float = 0.15  # Extra padding around face
    ) -> Tuple[int, int, int, int]:
        """
        Calculate crop coordinates to center on face while maintaining aspect ratio.

        Returns:
            (crop_x, crop_y, crop_width, crop_height) in pixels
        """
        source_ratio = source_width / source_height

        if source_ratio > target_ratio:
            # Source is wider - crop width
            crop_height = source_height
            crop_width = int(source_height * target_ratio)
        else:
            # Source is taller - crop height
            crop_width = source_width
            crop_height = int(source_width / target_ratio)

        # Calculate ideal center position based on face
        ideal_x = int(face_x * source_width)
        ideal_y = int(face_y * source_height)

        # Calculate crop position (keeping crop centered on face)
        crop_x = ideal_x - crop_width // 2
        crop_y = ideal_y - crop_height // 2

        # Clamp to video bounds
        crop_x = max(0, min(crop_x, source_width - crop_width))
        crop_y = max(0, min(crop_y, source_height - crop_height))

        return crop_x, crop_y, crop_width, crop_height

    def generate_crop_keyframes(
        self,
        positions: List[Tuple[float, float, float]],
        source_width: int,
        source_height: int,
        fps: float
    ) -> List[Dict[str, Any]]:
        """
        Generate FFmpeg-compatible keyframes for dynamic cropping.
        """
        keyframes = []

        for timestamp, face_x, face_y in positions:
            crop_x, crop_y, crop_w, crop_h = self.calculate_dynamic_crop(
                source_width, source_height, face_x, face_y
            )
            keyframes.append({
                'timestamp': timestamp,
                'x': crop_x,
                'y': crop_y,
                'w': crop_w,
                'h': crop_h
            })

        return keyframes

    def cut_clip_with_tracking(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_name: str,
        target_resolution: Tuple[int, int] = (1080, 1920),
        enable_tracking: bool = True,
        sample_interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Cut a clip with AI face tracking and reframing.

        Args:
            video_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_name: Output filename (without extension)
            target_resolution: Target resolution (width, height)
            enable_tracking: Enable face tracking (False = center crop)
            sample_interval: Face detection sample interval in seconds

        Returns:
            Dict with clip info and output path
        """
        video_path = Path(video_path)
        output_path = self.clips_dir / f"{output_name}.mp4"
        duration = end_time - start_time

        # Get video info
        video_info = self.get_video_info(str(video_path))
        source_width = video_info['width']
        source_height = video_info['height']
        fps = video_info['fps']

        print(f"Source video: {source_width}x{source_height} @ {fps:.2f}fps")

        face_positions = []  # Initialize to empty list

        if enable_tracking and self.face_detector is not None:
            print("AI Reframe: Detecting faces...")

            # Detect faces in the clip segment
            face_positions = self.detect_faces_in_video(
                str(video_path),
                sample_interval=sample_interval,
                start_time=start_time,
                end_time=end_time
            )

            if face_positions:
                # Smooth the positions
                smoothed_positions = self.smooth_positions(face_positions)

                # Use average position for simpler FFmpeg command
                avg_x = sum(p.center_x for p in smoothed_positions) / len(smoothed_positions)
                avg_y = sum(p.center_y for p in smoothed_positions) / len(smoothed_positions)

                print(f"Face tracking: Average position ({avg_x:.2f}, {avg_y:.2f})")

                # Calculate crop based on average face position
                crop_x, crop_y, crop_w, crop_h = self.calculate_dynamic_crop(
                    source_width, source_height, avg_x, avg_y
                )
            else:
                print("No faces detected, using center crop")
                crop_x, crop_y, crop_w, crop_h = self.calculate_dynamic_crop(
                    source_width, source_height, 0.5, 0.4  # Default to upper-center
                )
        else:
            print("Using center crop (tracking disabled or unavailable)")
            crop_x, crop_y, crop_w, crop_h = self.calculate_dynamic_crop(
                source_width, source_height, 0.5, 0.4
            )

        # Build FFmpeg command
        target_w, target_h = target_resolution
        crop_filter = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"
        scale_filter = f"scale={target_w}:{target_h}"
        video_filter = f"{crop_filter},{scale_filter}"

        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', str(video_path),
            '-t', str(duration),
            '-vf', video_filter,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-avoid_negative_ts', 'make_zero',
            '-y',
            str(output_path)
        ]

        print(f"Cutting clip with AI reframe: {start_time:.1f}s - {end_time:.1f}s")
        print(f"Crop: {crop_w}x{crop_h} at ({crop_x}, {crop_y})")

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
            raise RuntimeError(f"Failed to cut clip with tracking: {error_msg}")

        # Verify output file was created
        if not output_path.exists():
            raise RuntimeError(f"FFmpeg completed but output file not found: {output_path}")

        tracking_was_used = enable_tracking and self.face_detector is not None

        return {
            'video_path': str(output_path),
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'tracking_enabled': tracking_was_used,
            'faces_detected': len(face_positions) if tracking_was_used else 0,
            'crop_info': {
                'x': crop_x,
                'y': crop_y,
                'width': crop_w,
                'height': crop_h
            }
        }

    def cut_clip_with_dynamic_tracking(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_name: str,
        target_resolution: Tuple[int, int] = (1080, 1920),
        sample_interval: float = 0.25
    ) -> Dict[str, Any]:
        """
        Advanced: Cut clip with frame-by-frame dynamic tracking.
        Creates smoother following of subject but takes longer to process.

        Uses OpenCV to process frame by frame with interpolated crop positions.
        """
        if not CV2_AVAILABLE or self.face_detector is None:
            return self.cut_clip_with_tracking(
                video_path, start_time, end_time, output_name,
                target_resolution, enable_tracking=False
            )

        video_path = Path(video_path)
        output_path = self.clips_dir / f"{output_name}.mp4"
        temp_video_path = self.clips_dir / f"{output_name}_temp.mp4"

        # Get video info
        video_info = self.get_video_info(str(video_path))
        source_width = video_info['width']
        source_height = video_info['height']
        fps = video_info['fps']

        print(f"Dynamic tracking: Processing {end_time - start_time:.1f}s of video")

        # Detect and smooth face positions
        face_positions = self.detect_faces_in_video(
            str(video_path), sample_interval, start_time, end_time
        )

        if not face_positions:
            print("No faces detected, falling back to static crop")
            return self.cut_clip_with_tracking(
                video_path, start_time, end_time, output_name,
                target_resolution, enable_tracking=False
            )

        smoothed = self.smooth_positions(face_positions, smoothing_window=7)

        # Interpolate for all frames
        interpolated = self.interpolate_positions(smoothed, fps, start_time, end_time)

        # Process video frame by frame
        cap = None
        out = None
        frame_idx = 0

        try:
            cap = cv2.VideoCapture(str(video_path))
            cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

            target_w, target_h = target_resolution
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(temp_video_path), fourcc, fps, (target_w, target_h))

            total_frames = len(interpolated)

            print(f"Processing {total_frames} frames with dynamic crop...")

            while frame_idx < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                # Get interpolated face position for this frame
                _, face_x, face_y = interpolated[frame_idx]

                # Calculate crop for this frame
                crop_x, crop_y, crop_w, crop_h = self.calculate_dynamic_crop(
                    source_width, source_height, face_x, face_y
                )

                # Apply crop
                cropped = frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]

                # Resize to target
                resized = cv2.resize(cropped, (target_w, target_h))

                out.write(resized)
                frame_idx += 1

                if frame_idx % 100 == 0:
                    print(f"  Processed {frame_idx}/{total_frames} frames")

        finally:
            # Always release video resources
            if cap is not None:
                cap.release()
            if out is not None:
                out.release()

        # Add audio using FFmpeg
        print("Adding audio track...")
        cmd = [
            'ffmpeg',
            '-i', str(temp_video_path),
            '-ss', str(start_time),
            '-i', str(video_path),
            '-t', str(end_time - start_time),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-shortest',
            '-y',
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # Clean up files on failure
            for path in [temp_video_path, output_path]:
                if path.exists():
                    try:
                        path.unlink()
                    except Exception:
                        pass
            error_msg = e.stderr.decode() if e.stderr else str(e)
            raise RuntimeError(f"Failed to add audio: {error_msg}")
        finally:
            # Always clean up temp file
            if temp_video_path.exists():
                try:
                    temp_video_path.unlink()
                except Exception:
                    pass

        return {
            'video_path': str(output_path),
            'start_time': start_time,
            'end_time': end_time,
            'duration': end_time - start_time,
            'tracking_enabled': True,
            'tracking_mode': 'dynamic',
            'faces_detected': len(face_positions),
            'frames_processed': frame_idx
        }


# Quick test
if __name__ == "__main__":
    reframer = AIReframer()
    print(f"AIReframer initialized")
    print(f"MediaPipe available: {MEDIAPIPE_AVAILABLE}")

    # Test crop calculation
    crop = reframer.calculate_dynamic_crop(
        1920, 1080,  # Source dimensions
        0.3, 0.4,    # Face position (left side)
        9/16         # Target ratio
    )
    print(f"Dynamic crop for face at (0.3, 0.4): {crop}")

    crop_center = reframer.calculate_dynamic_crop(
        1920, 1080,
        0.5, 0.5,    # Face position (center)
        9/16
    )
    print(f"Dynamic crop for face at (0.5, 0.5): {crop_center}")
