"""
ClipGenius - Google Drive Downloader Service
Downloads videos from Google Drive shared links
"""
import re
import os
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from config import VIDEOS_DIR


class GoogleDriveDownloader:
    """Service to download videos from Google Drive"""

    # Regex patterns for extracting file ID from various Google Drive URL formats
    URL_PATTERNS = [
        r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/uc\?id=([a-zA-Z0-9_-]+)',
        r'docs\.google\.com/uc\?id=([a-zA-Z0-9_-]+)',
    ]

    DOWNLOAD_URL = "https://drive.google.com/uc?export=download"
    CHUNK_SIZE = 32768  # 32KB chunks

    def validate_url(self, url: str) -> bool:
        """Check if URL is a valid Google Drive URL"""
        return self.extract_file_id(url) is not None

    def extract_file_id(self, url: str) -> Optional[str]:
        """Extract file ID from Google Drive URL"""
        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_file_info(self, url: str) -> Dict[str, Any]:
        """
        Get file information from Google Drive.
        Note: Limited info available for public files without API key.
        """
        file_id = self.extract_file_id(url)
        if not file_id:
            raise ValueError("Invalid Google Drive URL")

        return {
            "file_id": file_id,
            "title": f"Google Drive Video ({file_id[:8]}...)",
            "duration": None,  # Cannot determine without downloading
            "thumbnail": None,
        }

    def _get_confirm_token(self, response: requests.Response) -> Optional[str]:
        """
        Get confirmation token for large files.
        Google Drive requires confirmation for files that can't be virus scanned.
        """
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None

    def download(
        self,
        url: str,
        output_name: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Download video from Google Drive.

        Args:
            url: Google Drive URL
            output_name: Name for the output file (without extension)
            progress_callback: Optional callback for progress updates

        Returns:
            dict with video_path and metadata
        """
        file_id = self.extract_file_id(url)
        if not file_id:
            raise ValueError("Invalid Google Drive URL")

        session = requests.Session()

        # Initial request
        response = session.get(self.DOWNLOAD_URL, params={'id': file_id}, stream=True)

        # Check for confirmation token (large files)
        token = self._get_confirm_token(response)
        if token:
            params = {'id': file_id, 'confirm': token}
            response = session.get(self.DOWNLOAD_URL, params=params, stream=True)

        # Check for errors
        if response.status_code != 200:
            raise Exception(f"Failed to download from Google Drive: HTTP {response.status_code}")

        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            # This might be an error page or access denied
            raise Exception("Cannot download file. It may be private or access is restricted.")

        # Determine file extension from content type or default to mp4
        if 'video/mp4' in content_type:
            ext = '.mp4'
        elif 'video/quicktime' in content_type:
            ext = '.mov'
        elif 'video/x-matroska' in content_type:
            ext = '.mkv'
        elif 'video/webm' in content_type:
            ext = '.webm'
        else:
            ext = '.mp4'  # Default to mp4

        # Output path
        output_path = VIDEOS_DIR / f"{output_name}{ext}"

        # Get total size if available
        total_size = int(response.headers.get('Content-Length', 0))

        # Download the file
        downloaded = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(self.CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback and total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_callback(progress)

        print(f"✅ Downloaded Google Drive file: {output_path}")

        return {
            "video_path": str(output_path),
            "file_id": file_id,
            "title": f"Google Drive Video",
            "duration": None,
            "thumbnail": None,
        }


# Create singleton instance
google_drive_downloader = GoogleDriveDownloader()
