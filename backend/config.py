"""
ClipGenius - Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths - sempre usar caminhos absolutos para evitar problemas com FFmpeg
BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data")).resolve()
VIDEOS_DIR = (DATA_DIR / "videos").resolve()
CLIPS_DIR = (DATA_DIR / "clips").resolve()
AUDIO_DIR = (DATA_DIR / "audio").resolve()

# Create directories if they don't exist
for dir_path in [VIDEOS_DIR, CLIPS_DIR, AUDIO_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/database.db")

# AI Provider settings
# Groq (FREE cloud API - much faster and better quality)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # Best quality model

# Ollama settings (FREE local AI - fallback if no Groq API key)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# AI Provider selection: "groq" (default if API key exists) or "ollama"
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto")  # auto, groq, or ollama

# Whisper settings - OPTIMIZED for better quality
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "pt")  # Portuguese by default
WHISPER_TEMPERATURE = float(os.getenv("WHISPER_TEMPERATURE", "0.0"))  # Lower = more consistent
WHISPER_BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "5"))  # Higher = better quality, slower
WHISPER_BEST_OF = int(os.getenv("WHISPER_BEST_OF", "5"))  # Number of candidates

# Download settings - RETRY mechanism
DOWNLOAD_MAX_RETRIES = int(os.getenv("DOWNLOAD_MAX_RETRIES", "3"))
DOWNLOAD_RETRY_DELAY = int(os.getenv("DOWNLOAD_RETRY_DELAY", "5"))  # seconds between retries

# Video settings
MAX_VIDEO_DURATION = 3600 * 3  # 3 hours max
CLIP_MIN_DURATION = 15  # 15 seconds min (ajustado para vídeos curtos)
CLIP_MAX_DURATION = 60  # 60 seconds max
NUM_CLIPS_TO_GENERATE = 15  # Igual ao Real Oficial

# FFmpeg settings
VIDEO_FORMAT = "mp4"
AUDIO_FORMAT = "wav"
OUTPUT_ASPECT_RATIO = "9:16"  # Vertical for shorts/reels (default)

# Output format presets
# Each format defines: aspect ratio, resolution, and platform info
OUTPUT_FORMATS = {
    "vertical": {
        "id": "vertical",
        "name": "Vertical (9:16)",
        "aspect_ratio": "9:16",
        "resolution": (1080, 1920),
        "platforms": ["TikTok", "Instagram Reels", "YouTube Shorts"],
        "description": "Formato vertical para shorts e reels"
    },
    "square": {
        "id": "square",
        "name": "Quadrado (1:1)",
        "aspect_ratio": "1:1",
        "resolution": (1080, 1080),
        "platforms": ["Instagram Feed", "Facebook", "Twitter"],
        "description": "Formato quadrado para feed"
    },
    "landscape": {
        "id": "landscape",
        "name": "Horizontal (16:9)",
        "aspect_ratio": "16:9",
        "resolution": (1920, 1080),
        "platforms": ["YouTube", "LinkedIn", "Website"],
        "description": "Formato horizontal tradicional"
    },
    "portrait": {
        "id": "portrait",
        "name": "Retrato (4:5)",
        "aspect_ratio": "4:5",
        "resolution": (1080, 1350),
        "platforms": ["Instagram Post", "Facebook Post"],
        "description": "Formato retrato para posts"
    }
}

DEFAULT_OUTPUT_FORMAT = "vertical"

# Upload settings
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(500 * 1024 * 1024)))  # 500MB default
ALLOWED_VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
ALLOWED_MIME_TYPES = [
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm"
]

# AI Reframe settings - Face tracking for vertical video
ENABLE_AI_REFRAME = os.getenv("ENABLE_AI_REFRAME", "true").lower() == "true"
REFRAME_SAMPLE_INTERVAL = float(os.getenv("REFRAME_SAMPLE_INTERVAL", "0.5"))  # Face detection every 0.5s
REFRAME_DYNAMIC_MODE = os.getenv("REFRAME_DYNAMIC_MODE", "false").lower() == "true"  # Frame-by-frame (slower)
