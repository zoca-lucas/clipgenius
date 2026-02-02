"""
ClipGenius - Configuration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _safe_int(value: str, default: int, name: str) -> int:
    """Safely convert string to int with validation"""
    try:
        result = int(value)
        if result < 0:
            print(f"⚠️  {name} deve ser >= 0, usando valor padrão: {default}")
            return default
        return result
    except (ValueError, TypeError):
        print(f"⚠️  {name} inválido: '{value}', usando valor padrão: {default}")
        return default


def _safe_float(value: str, default: float, name: str, min_val: float = None, max_val: float = None) -> float:
    """Safely convert string to float with validation"""
    try:
        result = float(value)
        if min_val is not None and result < min_val:
            print(f"⚠️  {name} deve ser >= {min_val}, usando valor padrão: {default}")
            return default
        if max_val is not None and result > max_val:
            print(f"⚠️  {name} deve ser <= {max_val}, usando valor padrão: {default}")
            return default
        return result
    except (ValueError, TypeError):
        print(f"⚠️  {name} inválido: '{value}', usando valor padrão: {default}")
        return default

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
# Groq API (FREE cloud API - fast and high quality)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Minimax API (uses Anthropic-compatible endpoint)
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "minimax/minimax-m2")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic")

# Ollama settings (FREE local AI - fallback if no cloud API key)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# AI Provider selection: "groq", "minimax", "ollama", or "auto"
# auto = use Groq if key exists, otherwise Minimax, otherwise Ollama
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto")

# Validate AI Provider
VALID_AI_PROVIDERS = ["auto", "groq", "minimax", "ollama"]
if AI_PROVIDER not in VALID_AI_PROVIDERS:
    print(f"⚠️  AI_PROVIDER inválido: '{AI_PROVIDER}', usando 'auto'")
    AI_PROVIDER = "auto"

# Whisper settings - OPTIMIZED for better quality
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "pt")  # Portuguese by default

# Transcription backend: deepgram, assemblyai, whisperx, stable-ts, faster-whisper, groq, auto
# deepgram = best quality cloud API (recommended)
# assemblyai = high quality cloud API
# whisperx = best local accuracy (forced alignment with wav2vec2)
# stable-ts = stable timestamps (local)
# faster-whisper = fast with native timestamps (local)
# groq = cloud API (fast but less precise)
# auto = automatically select best available
TRANSCRIPTION_BACKEND = os.getenv("TRANSCRIPTION_BACKEND", "auto")

# Deepgram API (HIGH QUALITY - recommended for production)
# Sign up at https://deepgram.com - generous free tier
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")

# AssemblyAI API (HIGH QUALITY alternative)
# Sign up at https://assemblyai.com - free tier available
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")

# Supported languages for transcription
SUPPORTED_LANGUAGES = {
    "pt": "Portuguese",
    "en": "English",
    "es": "Spanish",
    "auto": "Auto-detect"
}
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "pt")
WHISPER_TEMPERATURE = _safe_float(os.getenv("WHISPER_TEMPERATURE", "0.0"), 0.0, "WHISPER_TEMPERATURE", 0.0, 1.0)
WHISPER_BEAM_SIZE = _safe_int(os.getenv("WHISPER_BEAM_SIZE", "1"), 1, "WHISPER_BEAM_SIZE")
WHISPER_BEST_OF = _safe_int(os.getenv("WHISPER_BEST_OF", "1"), 1, "WHISPER_BEST_OF")

# Validate Whisper model
VALID_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
if WHISPER_MODEL not in VALID_WHISPER_MODELS:
    print(f"⚠️  WHISPER_MODEL inválido: '{WHISPER_MODEL}', usando 'base'")
    WHISPER_MODEL = "base"

# Download settings - RETRY mechanism
DOWNLOAD_MAX_RETRIES = _safe_int(os.getenv("DOWNLOAD_MAX_RETRIES", "3"), 3, "DOWNLOAD_MAX_RETRIES")
DOWNLOAD_RETRY_DELAY = _safe_int(os.getenv("DOWNLOAD_RETRY_DELAY", "5"), 5, "DOWNLOAD_RETRY_DELAY")

# Video settings
MAX_VIDEO_DURATION = 3600 * 3  # 3 hours max
CLIP_MIN_DURATION = 15  # 15 seconds min (garante conteúdo substancial)
CLIP_MAX_DURATION = 60  # 60 seconds max (permite completar ideias longas)
CLIP_IDEAL_DURATION = 30  # 30 seconds ideal (conteúdo completo + retenção)
NUM_CLIPS_TO_GENERATE = 15  # Igual ao Real Oficial

# IMPORTANTE: É melhor ter um clip de 45s com conteúdo COMPLETO
# do que um de 25s que corta no meio de uma explicação

# Sentence Boundary Detection settings
# Ajusta timestamps de clips para terminar em finais naturais de sentença
SENTENCE_DETECTION_ENABLED = os.getenv("SENTENCE_DETECTION_ENABLED", "true").lower() == "true"
SENTENCE_MIN_PAUSE = _safe_float(os.getenv("SENTENCE_MIN_PAUSE", "0.5"), 0.5, "SENTENCE_MIN_PAUSE", 0.1, 2.0)  # Segundos - pausa mínima para considerar fim de frase
SENTENCE_MAX_EXTENSION = _safe_float(os.getenv("SENTENCE_MAX_EXTENSION", "8"), 8, "SENTENCE_MAX_EXTENSION", 1, 15)  # Segundos - máximo para estender um clip

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
MAX_UPLOAD_SIZE = _safe_int(os.getenv("MAX_UPLOAD_SIZE", str(500 * 1024 * 1024)), 500 * 1024 * 1024, "MAX_UPLOAD_SIZE")
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
REFRAME_SAMPLE_INTERVAL = _safe_float(os.getenv("REFRAME_SAMPLE_INTERVAL", "0.5"), 0.5, "REFRAME_SAMPLE_INTERVAL", 0.1, 5.0)
REFRAME_DYNAMIC_MODE = os.getenv("REFRAME_DYNAMIC_MODE", "false").lower() == "true"  # Frame-by-frame (slower)

# Subtitle Style Settings
# Style types: "default" (simple text), "karaoke" (word highlight), "hormozi" (viral style - RECOMMENDED)
# hormozi = Alex Hormozi style - UPPERCASE, colorful, impactful
SUBTITLE_STYLE_TYPE = os.getenv("SUBTITLE_STYLE_TYPE", "hormozi")

# Karaoke Subtitle Settings - TikTok/Reels style word-by-word highlighting
# Only used when SUBTITLE_STYLE_TYPE is "karaoke"
SUBTITLE_KARAOKE_ENABLED = os.getenv("SUBTITLE_KARAOKE_ENABLED", "false").lower() == "true"

# Words per line settings
# For Hormozi style, fewer words per line is better (more impactful)
SUBTITLE_MAX_WORDS_PER_LINE = int(os.getenv("SUBTITLE_MAX_WORDS_PER_LINE", "4"))
SUBTITLE_HIGHLIGHT_COLOR = os.getenv("SUBTITLE_HIGHLIGHT_COLOR", "&H00FFFF&")  # Yellow (BGR format)
SUBTITLE_INACTIVE_COLOR = os.getenv("SUBTITLE_INACTIVE_COLOR", "&HFFFFFF&")  # White
SUBTITLE_SCALE_EFFECT = os.getenv("SUBTITLE_SCALE_EFFECT", "true").lower() == "true"
SUBTITLE_SCALE_AMOUNT = _safe_int(os.getenv("SUBTITLE_SCALE_AMOUNT", "110"), 110, "SUBTITLE_SCALE_AMOUNT")  # 110%

# Subtitle Font Settings
# Common fonts: Arial, Helvetica, Roboto, Montserrat, Open Sans, Poppins, Inter
# For best results, use a font installed on your system
SUBTITLE_FONT_NAME = os.getenv("SUBTITLE_FONT_NAME", "Arial")
SUBTITLE_FONT_SIZE = _safe_int(os.getenv("SUBTITLE_FONT_SIZE", "42"), 42, "SUBTITLE_FONT_SIZE")
SUBTITLE_FONT_BOLD = os.getenv("SUBTITLE_FONT_BOLD", "true").lower() == "true"
SUBTITLE_OUTLINE_SIZE = _safe_int(os.getenv("SUBTITLE_OUTLINE_SIZE", "4"), 4, "SUBTITLE_OUTLINE_SIZE")
SUBTITLE_SHADOW_SIZE = _safe_int(os.getenv("SUBTITLE_SHADOW_SIZE", "2"), 2, "SUBTITLE_SHADOW_SIZE")
SUBTITLE_MARGIN_V = _safe_int(os.getenv("SUBTITLE_MARGIN_V", "120"), 120, "SUBTITLE_MARGIN_V")  # Vertical margin from bottom

# Subtitle Position Settings
# Position: "top", "middle", "bottom" (default: bottom)
SUBTITLE_POSITION = os.getenv("SUBTITLE_POSITION", "bottom")
# Vertical offset: percentage from the position (0-100)
# For bottom: 0 = very bottom, 50 = middle-bottom
# For top: 0 = very top, 50 = middle-top
SUBTITLE_VERTICAL_OFFSET = _safe_int(os.getenv("SUBTITLE_VERTICAL_OFFSET", "10"), 10, "SUBTITLE_VERTICAL_OFFSET")

# JWT Authentication settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production-at-least-32-chars")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = _safe_int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"), 30, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
JWT_REFRESH_TOKEN_EXPIRE_DAYS = _safe_int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"), 7, "JWT_REFRESH_TOKEN_EXPIRE_DAYS")

# Google OAuth settings (for Drive integration)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

# Social Media OAuth settings
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
INSTAGRAM_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID", "")
INSTAGRAM_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# Payment settings
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")


# Startup validation message
def _print_config_summary():
    """Print configuration summary on startup"""
    groq_status = "✅ Configurada" if GROQ_API_KEY and not GROQ_API_KEY.startswith("your-") else "❌ Não configurada"
    minimax_status = "✅ Configurada" if MINIMAX_API_KEY and not MINIMAX_API_KEY.startswith("your-") else "❌ Não configurada"
    print("\n" + "=" * 50)
    print("📋 ClipGenius - Configuração")
    print("=" * 50)
    print(f"   AI Provider: {AI_PROVIDER}")
    print(f"   Groq API Key: {groq_status}")
    print(f"   Minimax API Key: {minimax_status}")
    print(f"   Whisper Model: {WHISPER_MODEL}")
    print(f"   AI Reframe: {'Ativado' if ENABLE_AI_REFRAME else 'Desativado'}")
    print(f"   Data Directory: {DATA_DIR}")
    print("=" * 50 + "\n")


# Only print summary when running as main app (not during imports for tests)
if os.getenv("CLIPGENIUS_PRINT_CONFIG", "true").lower() == "true":
    _print_config_summary()
