"""
ClipGenius - Services

Versões disponíveis:
- V1 (original): WhisperTranscriber, SubtitleGenerator
- V2 (melhorado): TranscriberV2, SubtitleGeneratorV2

Recomendação: Use V2 para melhor sincronização de timestamps e
tamanho consistente de legendas.
"""
from .downloader import YouTubeDownloader
from .transcriber import WhisperTranscriber
from .analyzer import ClipAnalyzer
from .cutter import VideoCutter
from .subtitler import SubtitleGenerator
from .reframer import AIReframer
from .auth import AuthService
from .sentence_detector import SentenceBoundaryDetector

# V2 - Versões melhoradas com timestamps precisos
from .transcriber_v2 import TranscriberV2, create_transcriber
from .subtitler_v2 import SubtitleGeneratorV2, SubtitleStyle, create_subtitle_generator

__all__ = [
    # V1 (original)
    "YouTubeDownloader",
    "WhisperTranscriber",
    "ClipAnalyzer",
    "VideoCutter",
    "SubtitleGenerator",
    "AIReframer",
    "AuthService",
    # V2 (melhorado)
    "TranscriberV2",
    "SubtitleGeneratorV2",
    "SubtitleStyle",
    "create_transcriber",
    "create_subtitle_generator",
    # Sentence Boundary Detection
    "SentenceBoundaryDetector",
]
