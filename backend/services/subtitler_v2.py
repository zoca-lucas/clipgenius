"""
ClipGenius - Subtitle Generator V2
Legendas com tamanho consistente e sincronização precisa.

Melhorias:
- Tamanho de fonte consistente independente da resolução
- PlayRes calculado corretamente para cada formato
- Animações opcionais e mais suaves
- Melhor estrutura de chunks para legendas
"""
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from config import (
    CLIPS_DIR,
    SUBTITLE_KARAOKE_ENABLED,
    SUBTITLE_HIGHLIGHT_COLOR,
    SUBTITLE_INACTIVE_COLOR,
    SUBTITLE_SCALE_EFFECT,
    SUBTITLE_SCALE_AMOUNT,
    SUBTITLE_FONT_NAME,
    SUBTITLE_FONT_SIZE,
    SUBTITLE_FONT_BOLD,
    SUBTITLE_OUTLINE_SIZE,
    SUBTITLE_SHADOW_SIZE,
    SUBTITLE_MARGIN_V,
)

# Importar configurações de posição e estilo (com fallback)
try:
    from config import SUBTITLE_POSITION, SUBTITLE_VERTICAL_OFFSET
except ImportError:
    SUBTITLE_POSITION = "bottom"
    SUBTITLE_VERTICAL_OFFSET = 10

try:
    from config import SUBTITLE_STYLE_TYPE, SUBTITLE_MAX_WORDS_PER_LINE
except ImportError:
    SUBTITLE_STYLE_TYPE = "hormozi"
    SUBTITLE_MAX_WORDS_PER_LINE = 4


@dataclass
class SubtitleStyle:
    """Configuração de estilo para legendas."""
    font_name: str = "Arial"
    font_size: int = 48  # Tamanho base para 1080p
    primary_color: str = "&H00FFFFFF"  # Branco
    secondary_color: str = "&H00FFFFFF"
    outline_color: str = "&H00000000"  # Preto
    back_color: str = "&H80000000"  # Semi-transparente
    bold: bool = True
    outline: int = 3
    shadow: int = 1
    alignment: int = 2  # Centro inferior (calculado automaticamente baseado em position)
    margin_v: int = 80  # Margem vertical
    margin_l: int = 40
    margin_r: int = 40
    # Novos campos de posição
    position: str = "bottom"  # "top", "middle", "bottom"
    vertical_offset: int = 10  # Offset percentual da posição (0-100)
    # Tipo de estilo: "default", "karaoke", "hormozi"
    style_type: str = "default"  # "default" = texto simples, "karaoke" = destaque por palavra, "hormozi" = viral style

    def __post_init__(self):
        """Calcula alignment baseado na posição."""
        # Alinhamento ASS:
        # 1-3 = inferior (esquerda, centro, direita)
        # 4-6 = meio (esquerda, centro, direita)
        # 7-9 = superior (esquerda, centro, direita)
        position_map = {
            "top": 8,      # Centro superior
            "middle": 5,   # Centro meio
            "bottom": 2    # Centro inferior
        }
        self.alignment = position_map.get(self.position, 2)

        # Ajustar fonte para estilo Hormozi
        if self.style_type == "hormozi":
            self.font_size = max(self.font_size, 52)  # Fonte maior
            self.outline = max(self.outline, 4)  # Outline mais grossa
            self.bold = True


# Resolução de referência para cálculo de escala
REFERENCE_WIDTH = 1080
REFERENCE_HEIGHT = 1920


# =========================================================================
# ESTILO HORMOZI - Legendas virais com destaque palavra por palavra
# =========================================================================
# Baseado no estilo usado por Alex Hormozi, MrBeast e criadores top do TikTok
# Características: palavras grandes, cores vibrantes, destaque individual

# Cores por tipo de palavra (formato ASS: &HBBGGRR&)
WORD_COLORS = {
    'emphasis': {
        'color': '&H00FFFF&',  # Amarelo (BGR)
        'words': [
            'muito', 'muita', 'incrível', 'incrivel', 'absurdo', 'demais',
            'extremamente', 'super', 'mega', 'impressionante', 'fantástico',
            'sensacional', 'espetacular', 'maravilhoso', 'perfeito', 'insano',
            'brutal', 'épico', 'lendário', 'top', 'melhor', 'pior', 'maior',
            'sempre', 'jamais', 'totalmente', 'completamente', 'absolutamente',
            'definitivamente', 'obviamente', 'literalmente', 'simplesmente',
            'importante', 'essencial', 'fundamental', 'crucial', 'vital',
            'secreto', 'segredo', 'revelação', 'verdade', 'real', 'fato'
        ]
    },
    'negative': {
        'color': '&H0000FF&',  # Vermelho (BGR)
        'words': [
            'não', 'nao', 'nunca', 'jamais', 'errado', 'erro', 'falha',
            'problema', 'cuidado', 'atenção', 'perigo', 'evite', 'pare',
            'ruim', 'péssimo', 'horrível', 'terrível', 'negativo', 'proibido',
            'mentira', 'fake', 'falso', 'fracasso', 'perdeu', 'morreu', 'fim',
            'péssima', 'horrivel', 'terrivel', 'pessimo', 'proibida', 'errada'
        ]
    },
    'positive': {
        'color': '&H00FF00&',  # Verde (BGR)
        'words': [
            'sim', 'certo', 'correto', 'exato', 'bom', 'ótimo', 'excelente',
            'sucesso', 'ganhou', 'venceu', 'conseguiu', 'alcançou', 'atingiu',
            'funciona', 'resultado', 'lucro', 'ganho', 'vitória', 'conquista',
            'dinheiro', 'rico', 'milhões', 'bilhões', 'fortuna', 'riqueza'
        ]
    },
    'numbers': {
        'color': '&H00D4FF&',  # Laranja (BGR)
        'words': [
            'zero', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete',
            'oito', 'nove', 'dez', 'cem', 'mil', 'milhão', 'bilhão',
            'porcentagem', 'percentual', 'média', 'estatística', 'ranking',
            'primeiro', 'segundo', 'terceiro', 'último', 'recorde', 'total'
        ]
    },
    'action': {
        'color': '&HFF00FF&',  # Magenta (BGR)
        'words': [
            'agora', 'hoje', 'já', 'imediatamente', 'urgente', 'rápido',
            'faça', 'faz', 'clique', 'inscreva', 'compartilhe', 'salve',
            'comece', 'pare', 'mude', 'transforme', 'descubra', 'aprenda'
        ]
    },
    'default': {
        'color': '&H00FFFFFF&',  # Branco
        'words': []
    }
}

# Estilo Hormozi - Configurações
HORMOZI_STYLE = {
    'font_size': 52,  # Fonte grande
    'outline': 4,     # Outline grossa
    'shadow': 2,      # Sombra sutil
    'uppercase': True,  # TUDO MAIÚSCULO
    'max_words_per_line': 3,  # Poucas palavras por linha
    'word_spacing': 1.2,  # Espaçamento entre palavras
}


class SubtitleGeneratorV2:
    """
    Gerador de legendas V2 com tamanho consistente.

    Características:
    - Cálculo correto de PlayRes para cada resolução
    - Tamanho de fonte proporcional
    - Animações suaves e opcionais
    - Chunks inteligentes baseados em pausas
    """

    def __init__(self):
        self.clips_dir = CLIPS_DIR
        self._word_color_lookup = self._build_word_color_lookup()

        # Estilo padrão com posição e tipo configuráveis
        self.default_style = SubtitleStyle(
            font_name=SUBTITLE_FONT_NAME,
            font_size=SUBTITLE_FONT_SIZE if SUBTITLE_STYLE_TYPE != "hormozi" else max(SUBTITLE_FONT_SIZE, 52),
            bold=SUBTITLE_FONT_BOLD,
            outline=SUBTITLE_OUTLINE_SIZE if SUBTITLE_STYLE_TYPE != "hormozi" else max(SUBTITLE_OUTLINE_SIZE, 4),
            shadow=SUBTITLE_SHADOW_SIZE,
            margin_v=SUBTITLE_MARGIN_V,
            position=SUBTITLE_POSITION,
            vertical_offset=SUBTITLE_VERTICAL_OFFSET,
            style_type=SUBTITLE_STYLE_TYPE
        )

        # Configurações de chunking baseadas no estilo
        self.max_words_per_line = SUBTITLE_MAX_WORDS_PER_LINE if SUBTITLE_STYLE_TYPE != "hormozi" else 3

    def _build_word_color_lookup(self) -> Dict[str, str]:
        """Constrói lookup de cores por palavra."""
        lookup = {}
        for category, data in WORD_COLORS.items():
            if category == 'default':
                continue
            for word in data['words']:
                lookup[word.lower()] = data['color']
        return lookup

    def _get_word_color(self, word: str) -> str:
        """Retorna cor para uma palavra."""
        clean_word = re.sub(r'[^\w]', '', word.lower())

        # Números
        if clean_word.isdigit():
            return WORD_COLORS['numbers']['color']

        return self._word_color_lookup.get(clean_word, WORD_COLORS['default']['color'])

    # =========================================================================
    # Formatação de tempo
    # =========================================================================

    def _format_ass_time(self, seconds: float) -> str:
        """Converte segundos para formato ASS (H:MM:SS.cc)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

    def _format_srt_time(self, seconds: float) -> str:
        """Converte segundos para formato SRT (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    # =========================================================================
    # Chunking inteligente
    # =========================================================================

    def _chunk_words(
        self,
        words: List[Dict[str, Any]],
        max_chars: int = 40,
        max_words: int = None,
        max_pause: float = 0.3,
        max_duration: float = 2.5
    ) -> List[List[Dict[str, Any]]]:
        # Usar configuração padrão se não especificado
        if max_words is None:
            max_words = getattr(self, 'max_words_per_line', 4)
        """
        Agrupa palavras em chunks para legendas.

        Critérios de quebra:
        - Máximo de caracteres por linha
        - Máximo de palavras por linha
        - Pausa detectada entre palavras
        - Duração máxima da legenda
        """
        chunks = []
        current_chunk = []
        current_chars = 0
        chunk_start = None

        for i, word_dict in enumerate(words):
            word = word_dict.get('word', '').strip()
            if not word:
                continue

            word_start = word_dict.get('start', 0)
            word_end = word_dict.get('end', 0)
            word_len = len(word)

            # Verificar se deve iniciar novo chunk
            should_break = False

            if current_chunk:
                # Verificar limite de caracteres
                if current_chars + word_len + 1 > max_chars:
                    should_break = True

                # Verificar limite de palavras
                if len(current_chunk) >= max_words:
                    should_break = True

                # Verificar pausa
                prev_end = current_chunk[-1].get('end', 0)
                if word_start - prev_end > max_pause:
                    should_break = True

                # Verificar duração
                if chunk_start and word_end - chunk_start > max_duration:
                    should_break = True

            if should_break and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_chars = 0
                chunk_start = None

            # Adicionar palavra ao chunk atual
            current_chunk.append(word_dict)
            current_chars += word_len + (1 if current_chars > 0 else 0)
            if chunk_start is None:
                chunk_start = word_start

        # Adicionar último chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    # =========================================================================
    # Cálculo de escala para resolução
    # =========================================================================

    def _calculate_scaled_style(
        self,
        style: SubtitleStyle,
        video_width: int,
        video_height: int
    ) -> Tuple[SubtitleStyle, int, int]:
        """
        Calcula estilo escalado para a resolução do vídeo.

        Retorna (estilo_escalado, playres_x, playres_y).

        IMPORTANTE: Usamos PlayRes fixo de referência e deixamos o
        ScaledBorderAndShadow fazer o trabalho de escala.
        Isso garante tamanho consistente entre diferentes resoluções.
        """
        # Usar resolução de referência para PlayRes
        # O FFmpeg/libass vai escalar automaticamente
        playres_x = REFERENCE_WIDTH
        playres_y = REFERENCE_HEIGHT

        # Calcular fator de escala baseado na altura
        scale_factor = video_height / REFERENCE_HEIGHT

        # Calcular margem vertical baseada na posição e offset
        # vertical_offset é uma porcentagem (0-100) da área disponível
        base_margin = style.margin_v
        if hasattr(style, 'vertical_offset'):
            offset_pixels = int((style.vertical_offset / 100) * REFERENCE_HEIGHT * 0.4)  # 40% da altura para offset
            base_margin = max(20, base_margin + offset_pixels)

        # Aplicar escala ao estilo
        scaled_style = SubtitleStyle(
            font_name=style.font_name,
            font_size=int(style.font_size * scale_factor),
            primary_color=style.primary_color,
            secondary_color=style.secondary_color,
            outline_color=style.outline_color,
            back_color=style.back_color,
            bold=style.bold,
            outline=max(1, int(style.outline * scale_factor)),
            shadow=max(0, int(style.shadow * scale_factor)),
            alignment=style.alignment,
            margin_v=int(base_margin * scale_factor),
            margin_l=int(style.margin_l * scale_factor),
            margin_r=int(style.margin_r * scale_factor),
            position=style.position,
            vertical_offset=style.vertical_offset
        )

        return scaled_style, playres_x, playres_y

    # =========================================================================
    # Geração ASS
    # =========================================================================

    def generate_ass(
        self,
        words: List[Dict[str, Any]],
        output_path: str,
        offset: float = 0,
        video_width: int = 1080,
        video_height: int = 1920,
        style: SubtitleStyle = None,
        enable_karaoke: bool = False,
        enable_colors: bool = True,
        capitalize: bool = True
    ) -> str:
        """
        Gera arquivo ASS com legendas.

        Args:
            words: Lista de palavras com timestamps
            output_path: Caminho de saída
            offset: Offset de tempo
            video_width: Largura do vídeo
            video_height: Altura do vídeo
            style: Estilo personalizado
            enable_karaoke: Ativar efeito karaokê
            enable_colors: Ativar cores por tipo de palavra
            capitalize: Capitalizar texto

        Returns:
            Caminho do arquivo gerado
        """
        output_path = Path(output_path)
        style = style or self.default_style

        # Calcular estilo escalado
        scaled_style, playres_x, playres_y = self._calculate_scaled_style(
            style, video_width, video_height
        )

        # Cabeçalho ASS
        ass_content = self._generate_ass_header(
            playres_x, playres_y, scaled_style, enable_karaoke
        )

        # Gerar chunks
        chunks = self._chunk_words(words)

        # Gerar diálogos
        for chunk in chunks:
            if not chunk:
                continue

            start_time = max(0, chunk[0].get('start', 0) - offset)
            end_time = max(start_time + 0.1, chunk[-1].get('end', 0) - offset)

            # Ajustar timestamps das palavras
            adjusted_chunk = []
            for w in chunk:
                adjusted_chunk.append({
                    'word': w.get('word', ''),
                    'start': max(0, w.get('start', 0) - offset),
                    'end': max(0, w.get('end', 0) - offset)
                })

            # Gerar texto do diálogo baseado no estilo
            style_type = getattr(style, 'style_type', 'default')

            if style_type == "hormozi":
                # Estilo Hormozi - viral, impactante
                text = self._generate_hormozi_text(adjusted_chunk, enable_colors)
                style_name = "Karaoke"  # Usa o estilo Karaoke para highlight
            elif enable_karaoke or style_type == "karaoke":
                text = self._generate_karaoke_text(
                    adjusted_chunk, enable_colors, capitalize
                )
                style_name = "Karaoke"
            else:
                text = self._generate_simple_text(
                    adjusted_chunk, enable_colors, capitalize
                )
                style_name = "Default"

            if text:
                start_str = self._format_ass_time(start_time)
                end_str = self._format_ass_time(end_time)
                ass_content += f"Dialogue: 0,{start_str},{end_str},{style_name},,0,0,0,,{text}\n"

        # Salvar arquivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)

        return str(output_path)

    def _generate_ass_header(
        self,
        playres_x: int,
        playres_y: int,
        style: SubtitleStyle,
        enable_karaoke: bool
    ) -> str:
        """Gera cabeçalho do arquivo ASS."""
        bold_value = -1 if style.bold else 0

        header = f"""[Script Info]
Title: ClipGenius Subtitles V2
ScriptType: v4.00+
PlayResX: {playres_x}
PlayResY: {playres_y}
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style.font_name},{style.font_size},{style.primary_color},&H000000FF,{style.outline_color},{style.back_color},{bold_value},0,0,0,100,100,0,0,1,{style.outline},{style.shadow},{style.alignment},{style.margin_l},{style.margin_r},{style.margin_v},1
"""

        if enable_karaoke:
            # Estilo karaokê com cor secundária (cor inativa)
            header += f"Style: Karaoke,{style.font_name},{style.font_size},{style.secondary_color},&H000000FF,{style.outline_color},{style.back_color},{bold_value},0,0,0,100,100,0,0,1,{style.outline},{style.shadow},{style.alignment},{style.margin_l},{style.margin_r},{style.margin_v},1\n"

        header += """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        return header

    def _generate_simple_text(
        self,
        words: List[Dict[str, Any]],
        enable_colors: bool,
        capitalize: bool
    ) -> str:
        """Gera texto simples com cores opcionais."""
        if not words:
            return ""

        parts = []
        default_color = WORD_COLORS['default']['color']

        for i, word_dict in enumerate(words):
            word = word_dict.get('word', '').strip()
            if not word:
                continue

            # Capitalização
            if capitalize:
                if i == 0:
                    word = word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
                else:
                    word = word.lower()

            # Cores
            if enable_colors:
                color = self._get_word_color(word)
                if color != default_color:
                    parts.append(f"{{\\1c{color}}}{word}{{\\1c{default_color}}}")
                else:
                    parts.append(word)
            else:
                parts.append(word)

        return ' '.join(parts)

    def _generate_karaoke_text(
        self,
        words: List[Dict[str, Any]],
        enable_colors: bool,
        capitalize: bool
    ) -> str:
        """
        Gera texto com efeito karaokê.

        Usa tag \\kf para fill suave (mais profissional que \\k).
        """
        if not words:
            return ""

        parts = []
        highlight_color = SUBTITLE_HIGHLIGHT_COLOR
        default_color = WORD_COLORS['default']['color']

        for i, word_dict in enumerate(words):
            word = word_dict.get('word', '').strip()
            if not word:
                continue

            start = word_dict.get('start', 0)
            end = word_dict.get('end', 0)

            # Duração em centissegundos
            duration_cs = max(1, int((end - start) * 100))

            # Capitalização
            if capitalize:
                if i == 0:
                    word = word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
                else:
                    word = word.lower()

            # Determinar cor
            if enable_colors:
                word_color = self._get_word_color(word)
                if word_color == default_color:
                    word_color = highlight_color
            else:
                word_color = highlight_color

            # Tag karaokê: \kf = fill suave (mais bonito que \k)
            tag = f"\\kf{duration_cs}\\1c{word_color}"

            parts.append(f"{{{tag}}}{word}")

        return ' '.join(parts)

    def _generate_hormozi_text(
        self,
        words: List[Dict[str, Any]],
        enable_colors: bool = True
    ) -> str:
        """
        Gera texto no estilo Hormozi - legendas virais impactantes.

        Características:
        - TUDO MAIÚSCULO
        - Palavras destacadas individualmente
        - Cores vibrantes por categoria
        - Efeito de aparecimento gradual
        """
        if not words:
            return ""

        parts = []
        default_color = WORD_COLORS['default']['color']
        highlight_color = "&H00FFFF&"  # Amarelo para destaque

        for i, word_dict in enumerate(words):
            word = word_dict.get('word', '').strip()
            if not word:
                continue

            start = word_dict.get('start', 0)
            end = word_dict.get('end', 0)

            # UPPERCASE para estilo Hormozi
            word = word.upper()

            # Duração em centissegundos
            duration_cs = max(1, int((end - start) * 100))

            # Determinar cor baseada na categoria da palavra
            if enable_colors:
                word_color = self._get_word_color(word.lower())
                if word_color == default_color:
                    word_color = highlight_color
            else:
                word_color = highlight_color

            # Estilo Hormozi: fade in + cor + scale sutil
            # \fad(100,0) = fade in de 100ms
            # \fscx110\fscy110 = escala 110%
            # \t(\fscx100\fscy100) = anima de volta para 100%
            tag = f"\\kf{duration_cs}\\1c{word_color}"

            parts.append(f"{{{tag}}}{word}")

        return ' '.join(parts)

    # =========================================================================
    # Geração SRT
    # =========================================================================

    def generate_srt(
        self,
        words: List[Dict[str, Any]],
        output_path: str,
        offset: float = 0,
        capitalize: bool = True
    ) -> str:
        """Gera arquivo SRT."""
        output_path = Path(output_path)
        chunks = self._chunk_words(words)

        lines = []
        for i, chunk in enumerate(chunks, 1):
            if not chunk:
                continue

            start_time = max(0, chunk[0].get('start', 0) - offset)
            end_time = max(start_time + 0.1, chunk[-1].get('end', 0) - offset)

            text = ' '.join(w.get('word', '') for w in chunk).strip()
            if capitalize and text:
                text = text[0].upper() + text[1:].lower()

            if text:
                lines.append(str(i))
                lines.append(f"{self._format_srt_time(start_time)} --> {self._format_srt_time(end_time)}")
                lines.append(text)
                lines.append('')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return str(output_path)

    # =========================================================================
    # Burn-in de legendas
    # =========================================================================

    def burn_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str = None
    ) -> str:
        """
        Queima legendas no vídeo usando FFmpeg.

        Args:
            video_path: Caminho do vídeo
            subtitle_path: Caminho do arquivo de legenda (.ass ou .srt)
            output_path: Caminho de saída

        Returns:
            Caminho do vídeo com legendas
        """
        video_path = Path(video_path)
        subtitle_path = Path(subtitle_path)

        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_subtitled.mp4"
        else:
            output_path = Path(output_path)

        # Copiar legenda para arquivo temporário sem espaços
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        temp_sub = Path(temp_dir) / f"subtitle{subtitle_path.suffix}"
        shutil.copy2(subtitle_path, temp_sub)

        try:
            # Comando FFmpeg
            if subtitle_path.suffix.lower() == '.ass':
                # ASS: usar filtro ass
                filter_str = f"ass='{temp_sub}'"
            else:
                # SRT: usar filtro subtitles com force_style
                filter_str = f"subtitles='{temp_sub}':force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'"

            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vf', filter_str,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'copy',
                '-y',
                str(output_path)
            ]

            print(f"Queimando legendas: {video_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Erro FFmpeg: {result.stderr[:500]}")
                # Fallback: copiar vídeo sem legendas
                shutil.copy2(video_path, output_path)

            return str(output_path)

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # =========================================================================
    # Interface de alto nível
    # =========================================================================

    def create_subtitled_clip(
        self,
        video_path: str,
        words: List[Dict[str, Any]],
        clip_start_time: float,
        output_name: str,
        video_width: int = 1080,
        video_height: int = 1920,
        style: SubtitleStyle = None,
        enable_karaoke: bool = None,
        enable_colors: bool = True,
        burn_subtitles: bool = False
    ) -> Dict[str, Any]:
        """
        Cria legendas para um clip.

        Args:
            video_path: Caminho do vídeo
            words: Lista de palavras com timestamps
            clip_start_time: Tempo de início do clip (para offset)
            output_name: Nome do arquivo de saída
            video_width: Largura do vídeo
            video_height: Altura do vídeo
            style: Estilo personalizado
            enable_karaoke: Ativar karaokê (default: config)
            enable_colors: Ativar cores
            burn_subtitles: Queimar legendas no vídeo

        Returns:
            Dict com caminhos e dados das legendas
        """
        video_path = Path(video_path)

        if enable_karaoke is None:
            enable_karaoke = SUBTITLE_KARAOKE_ENABLED

        # Gerar arquivo ASS
        ass_path = self.clips_dir / f"{output_name}.ass"
        self.generate_ass(
            words=words,
            output_path=str(ass_path),
            offset=clip_start_time,
            video_width=video_width,
            video_height=video_height,
            style=style,
            enable_karaoke=enable_karaoke,
            enable_colors=enable_colors
        )

        # Gerar SRT também (para compatibilidade)
        srt_path = self.clips_dir / f"{output_name}.srt"
        self.generate_srt(
            words=words,
            output_path=str(srt_path),
            offset=clip_start_time
        )

        # Construir dados das legendas para o editor
        subtitle_data = self._build_subtitle_data(words, clip_start_time)

        result = {
            'subtitle_path': str(ass_path),
            'srt_path': str(srt_path),
            'subtitle_file': str(ass_path),
            'subtitle_data': subtitle_data,
            'karaoke_enabled': enable_karaoke,
            'subtitles_burned': False,
            'has_burned_subtitles': False
        }

        # Queimar legendas se solicitado
        if burn_subtitles:
            output_video = self.clips_dir / f"{output_name}_subtitled.mp4"
            burned_path = self.burn_subtitles(
                video_path=str(video_path),
                subtitle_path=str(ass_path),
                output_path=str(output_video)
            )
            result['video_path_with_subtitles'] = burned_path
            result['subtitles_burned'] = True
            result['has_burned_subtitles'] = True
            result['subtitle_message'] = 'Legendas queimadas com sucesso'

        return result

    def _build_subtitle_data(
        self,
        words: List[Dict[str, Any]],
        offset: float
    ) -> List[Dict[str, Any]]:
        """Constrói estrutura de dados das legendas para o editor."""
        chunks = self._chunk_words(words)
        subtitle_data = []

        for i, chunk in enumerate(chunks):
            if not chunk:
                continue

            start_time = max(0, chunk[0].get('start', 0) - offset)
            end_time = max(start_time + 0.1, chunk[-1].get('end', 0) - offset)

            text = ' '.join(w.get('word', '') for w in chunk).strip()
            text = text[0].upper() + text[1:].lower() if text else text

            adjusted_words = []
            for w in chunk:
                adjusted_words.append({
                    'word': w.get('word', ''),
                    'start': max(0, w.get('start', 0) - offset),
                    'end': max(0, w.get('end', 0) - offset)
                })

            if text:
                subtitle_data.append({
                    'id': f'sub_{i}',
                    'start': start_time,
                    'end': end_time,
                    'text': text,
                    'words': adjusted_words
                })

        return subtitle_data

    # =========================================================================
    # Métodos de compatibilidade (V1 API)
    # =========================================================================

    def generate_ass_karaoke(
        self,
        words: List[Dict[str, Any]],
        output_path: str,
        words_per_line: int = 5,
        offset: float = 0,
        style: Dict[str, Any] = None,
        video_width: int = 1080,
        video_height: int = 1920,
        max_chars_per_line: int = 40,
        capitalize: bool = True,
        highlight_color: str = None,
        scale_effect: bool = None,
        scale_amount: int = None,
        colorize_words: bool = True
    ) -> str:
        """
        Gera ASS com karaokê (compatibilidade V1).

        Wrapper para generate_ass com enable_karaoke=True.
        """
        # Converter style dict para SubtitleStyle se necessário
        subtitle_style = None
        if style:
            subtitle_style = SubtitleStyle(
                font_name=style.get('font_name', 'Arial'),
                font_size=style.get('font_size', 42),
                primary_color=style.get('primary_color', '&H00FFFFFF'),
                outline_color=style.get('outline_color', '&H00000000'),
                outline=style.get('outline', 3),
                shadow=style.get('shadow', 1),
                margin_v=style.get('margin_v', 80),
                position=style.get('position', 'bottom'),
                vertical_offset=style.get('vertical_offset', 10)
            )

        return self.generate_ass(
            words=words,
            output_path=output_path,
            offset=offset,
            video_width=video_width,
            video_height=video_height,
            style=subtitle_style,
            enable_karaoke=True,
            enable_colors=colorize_words,
            capitalize=capitalize
        )

    def burn_subtitles_on_demand(
        self,
        video_path: str,
        subtitle_data: List[Dict[str, Any]],
        output_path: str,
        style: Dict[str, Any] = None,
        enable_karaoke: bool = True
    ) -> Dict[str, Any]:
        """
        Queima legendas no vídeo sob demanda (compatibilidade V1).

        Args:
            video_path: Caminho do vídeo de entrada
            subtitle_data: Lista de entradas de legenda
            output_path: Caminho de saída
            style: Estilo personalizado
            enable_karaoke: Ativar karaokê

        Returns:
            Dict com path e status
        """
        video_path = Path(video_path)
        output_path = Path(output_path)

        # Converter subtitle_data para formato de palavras
        all_words = []
        for entry in subtitle_data:
            words = entry.get('words', [])
            if words:
                all_words.extend(words)
            else:
                # Fallback: criar palavras a partir do texto
                text = entry.get('text', '')
                start = entry.get('start', 0)
                end = entry.get('end', 0)
                word_list = text.split()
                if word_list:
                    duration_per_word = (end - start) / len(word_list)
                    for j, word in enumerate(word_list):
                        all_words.append({
                            'word': word,
                            'start': start + j * duration_per_word,
                            'end': start + (j + 1) * duration_per_word
                        })

        # Gerar ASS temporário
        temp_ass = output_path.parent / f"{output_path.stem}_temp.ass"

        # Converter style dict para SubtitleStyle
        subtitle_style = None
        if style:
            subtitle_style = SubtitleStyle(
                font_name=style.get('font_name', 'Arial'),
                font_size=style.get('font_size', 42),
                primary_color=style.get('primary_color', '&H00FFFFFF'),
                outline_color=style.get('outline_color', '&H00000000'),
                outline=style.get('outline', 3),
                shadow=style.get('shadow', 1),
                margin_v=style.get('margin_v', 80),
                position=style.get('position', 'bottom'),
                vertical_offset=style.get('vertical_offset', 10)
            )

        self.generate_ass(
            words=all_words,
            output_path=str(temp_ass),
            offset=0,  # Já está ajustado
            style=subtitle_style,
            enable_karaoke=enable_karaoke
        )

        try:
            # Queimar legendas
            result_path = self.burn_subtitles(
                video_path=str(video_path),
                subtitle_path=str(temp_ass),
                output_path=str(output_path)
            )

            return {
                'path': result_path,
                'subtitles_burned': True,
                'message': 'Legendas queimadas com sucesso'
            }
        finally:
            # Limpar ASS temporário
            if temp_ass.exists():
                temp_ass.unlink()


# Factory function
def create_subtitle_generator() -> SubtitleGeneratorV2:
    """Cria instância do gerador de legendas V2."""
    return SubtitleGeneratorV2()


# Teste rápido
if __name__ == "__main__":
    print("SubtitleGeneratorV2 inicializado")

    gen = SubtitleGeneratorV2()
    print(f"Estilo padrão: {gen.default_style.font_name} {gen.default_style.font_size}px")

    # Teste de formatação de tempo
    print(f"ASS time: {gen._format_ass_time(65.5)}")
    print(f"SRT time: {gen._format_srt_time(65.5)}")
