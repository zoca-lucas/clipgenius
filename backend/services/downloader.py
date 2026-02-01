"""
ClipGenius - YouTube Downloader Service
Downloads videos from YouTube using yt-dlp
Optimized for long videos with retry, resume, and rate limiting
"""
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import yt_dlp
from config import (
    VIDEOS_DIR,
    MAX_VIDEO_DURATION,
    DOWNLOAD_MAX_RETRIES,
    DOWNLOAD_RETRY_DELAY
)


class YouTubeDownloader:
    """Service to download videos from YouTube with robust error handling"""

    YOUTUBE_REGEX = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})'

    def __init__(self):
        self.videos_dir = VIDEOS_DIR
        self.max_retries = DOWNLOAD_MAX_RETRIES
        self.retry_delay = DOWNLOAD_RETRY_DELAY
        self._progress_callback: Optional[Callable[[Dict], None]] = None

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        match = re.search(self.YOUTUBE_REGEX, url)
        return match.group(1) if match else None

    def validate_url(self, url: str) -> bool:
        """Validate if URL is a valid YouTube URL"""
        return bool(self.extract_video_id(url))

    def set_progress_callback(self, callback: Callable[[Dict], None]):
        """Set a callback function to receive progress updates"""
        self._progress_callback = callback

    def get_video_info(self, url: str) -> Dict[str, Any]:
        """Get video metadata without downloading"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 30,  # Timeout for network operations
        }

        for attempt in range(self.max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                    return {
                        'id': info.get('id'),
                        'title': info.get('title'),
                        'duration': info.get('duration'),
                        'thumbnail': info.get('thumbnail'),
                        'description': info.get('description'),
                        'channel': info.get('channel'),
                        'view_count': info.get('view_count'),
                    }
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"[Attempt {attempt + 1}/{self.max_retries}] Error getting info: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    raise

    def _get_download_options(self, output_path: Path, quality: str = "720") -> Dict[str, Any]:
        """
        Build yt-dlp options optimized for reliability and performance

        Args:
            output_path: Path to save the video
            quality: Max video height (360, 480, 720, 1080). Default 720p is enough for vertical clips.
        """
        # Format selection: limit quality to save time/bandwidth
        # For 9:16 clips at 1080x1920, source 720p is more than enough
        format_str = (
            f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/'
            f'bestvideo[height<={quality}]+bestaudio/'
            f'best[height<={quality}]/'
            'best'
        )

        return {
            # Format and output
            'format': format_str,
            'outtmpl': str(output_path.with_suffix('')),
            'merge_output_format': 'mp4',

            # Logging
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],

            # Duration limit
            'match_filter': yt_dlp.utils.match_filter_func(
                f'duration < {MAX_VIDEO_DURATION}'
            ) if MAX_VIDEO_DURATION else None,

            # === RELIABILITY IMPROVEMENTS ===

            # Network timeouts
            'socket_timeout': 30,

            # Retry settings for fragments (important for long videos)
            'retries': 10,
            'fragment_retries': 10,
            'file_access_retries': 5,

            # Continue partial downloads (RESUME SUPPORT)
            'continuedl': True,

            # Rate limiting to avoid YouTube throttling
            'throttledratelimit': 100000,  # Slow down if throttled below 100KB/s

            # Buffer and chunk settings for stability
            'buffersize': 1024 * 16,  # 16KB buffer
            'http_chunk_size': 10485760,  # 10MB chunks for better resume

            # Avoid getting blocked
            'sleep_interval': 1,  # Sleep 1 second between requests
            'max_sleep_interval': 5,
            'sleep_interval_requests': 1,

            # Use concurrent fragments for faster download
            'concurrent_fragment_downloads': 4,

            # External downloader for better performance (if available)
            # 'external_downloader': 'aria2c',
            # 'external_downloader_args': ['-x', '16', '-k', '1M'],

            # Headers to look like a real browser
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },

            # Prevent HTTP/2 issues
            'legacy_server_connect': True,
        }

    def download(self, url: str, video_id: Optional[str] = None, quality: str = "720") -> Dict[str, Any]:
        """
        Download video from YouTube with retry and resume support

        Args:
            url: YouTube video URL
            video_id: Optional video ID (extracted from URL if not provided)
            quality: Max video height (360, 480, 720, 1080). Default 720p.

        Returns:
            Dict with video info and file path
        """
        if not video_id:
            video_id = self.extract_video_id(url)

        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")

        output_path = self.videos_dir / f"{video_id}.mp4"
        ydl_opts = self._get_download_options(output_path, quality)

        last_error = None

        for attempt in range(self.max_retries):
            try:
                print(f"\n{'='*50}")
                print(f"Download attempt {attempt + 1}/{self.max_retries}")
                print(f"{'='*50}\n")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                    # Find the actual output file
                    actual_path = output_path
                    if not actual_path.exists():
                        # Try finding with yt-dlp naming
                        possible_paths = list(self.videos_dir.glob(f"{video_id}.*"))
                        mp4_paths = [p for p in possible_paths if p.suffix == '.mp4']
                        if mp4_paths:
                            actual_path = mp4_paths[0]
                        elif possible_paths:
                            actual_path = possible_paths[0]

                    if not actual_path.exists():
                        raise FileNotFoundError(f"Download completed but file not found: {actual_path}")

                    print(f"\n✓ Download successful: {actual_path}")
                    print(f"  File size: {actual_path.stat().st_size / (1024*1024):.1f} MB")

                    return {
                        'id': info.get('id'),
                        'title': info.get('title'),
                        'duration': info.get('duration'),
                        'thumbnail': info.get('thumbnail'),
                        'video_path': str(actual_path),
                    }

            except yt_dlp.utils.DownloadError as e:
                last_error = e
                error_msg = str(e).lower()

                # Check if it's a fatal error that shouldn't be retried
                if any(x in error_msg for x in ['private video', 'video unavailable', 'copyright', 'removed']):
                    print(f"\n✗ Fatal error (not retrying): {e}")
                    raise

                print(f"\n✗ Download error (attempt {attempt + 1}): {e}")

                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"  Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

            except Exception as e:
                last_error = e
                print(f"\n✗ Unexpected error (attempt {attempt + 1}): {e}")

                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"  Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        # All retries exhausted
        raise Exception(f"Download failed after {self.max_retries} attempts. Last error: {last_error}")

    def _progress_hook(self, d: Dict[str, Any]):
        """Hook to track download progress with detailed info"""
        status = d.get('status')

        if status == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)

            # Format sizes
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024) if total else 0

            if total_mb > 0:
                print(f"  ↓ {percent} | {downloaded_mb:.1f}/{total_mb:.1f} MB | {speed} | ETA: {eta}")
            else:
                print(f"  ↓ {percent} | {downloaded_mb:.1f} MB | {speed}")

            # Call external callback if set
            if self._progress_callback:
                self._progress_callback({
                    'status': 'downloading',
                    'percent': d.get('_percent_str'),
                    'speed': speed,
                    'eta': eta,
                    'downloaded_bytes': downloaded,
                    'total_bytes': total,
                })

        elif status == 'finished':
            filename = d.get('filename', 'unknown')
            print(f"  ✓ Download complete: {Path(filename).name}")
            print(f"  → Merging video and audio...")

            if self._progress_callback:
                self._progress_callback({
                    'status': 'finished',
                    'filename': filename,
                })

        elif status == 'error':
            print(f"  ✗ Download error occurred")
            if self._progress_callback:
                self._progress_callback({'status': 'error'})


    def download_high_quality(self, url: str, video_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Download video in high quality (1080p) for cases where quality matters more than speed.
        Use this for shorter videos or when source quality is important.
        """
        return self.download(url, video_id, quality="1080")


# Quick test
if __name__ == "__main__":
    downloader = YouTubeDownloader()

    # Test URL validation
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/shorts/abc12345678",
        "invalid url",
    ]

    print("Testing URL validation:")
    print("-" * 50)
    for url in test_urls:
        video_id = downloader.extract_video_id(url)
        print(f"  {url}")
        print(f"  -> Video ID: {video_id}")
        print()
