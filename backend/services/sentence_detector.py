"""
ClipGenius - Sentence Boundary Detector
Ajusta timestamps de clips para terminar em finais naturais de sentença
"""
from typing import Dict, Any, List, Tuple
import re


class SentenceBoundaryDetector:
    """
    Detecta limites de sentença usando:
    1. Pontuação (. ? !)
    2. Pausas longas entre palavras (>500ms)
    3. Padrões de conclusão ("então é isso", "entendeu?", etc.)
    """

    # Configurações padrão
    MIN_PAUSE_FOR_BOUNDARY = 0.5  # 500ms
    MAX_EXTENSION_SECONDS = 8     # Máximo para estender o clip
    SENTENCE_END_PUNCTUATION = {'.', '?', '!', '...'}

    # Padrões que indicam conclusão (português)
    CONCLUSION_PATTERNS = [
        r'\bentão é isso\b',
        r'\bentendeu\b',
        r'\bsacou\b',
        r'\bbeleza\b',
        r'\bé isso aí\b',
        r'\bpronto\b',
        r'\bfechado\b',
        r'\bvamos lá\b',
        r'\bagora\b.*\bvamos\b',
    ]

    def __init__(self, config: Dict = None):
        """
        Inicializa o detector com configurações opcionais.

        Args:
            config: Dicionário com configurações opcionais:
                - min_pause: Pausa mínima em segundos para considerar fim de frase
                - max_extension: Máximo de segundos para estender um clip
        """
        if config:
            self.MIN_PAUSE_FOR_BOUNDARY = config.get('min_pause', 0.5)
            self.MAX_EXTENSION_SECONDS = config.get('max_extension', 8)

    def find_sentence_boundaries(
        self,
        words: List[Dict],
        start_time: float,
        end_time: float
    ) -> List[Dict]:
        """
        Encontra todos os possíveis limites de sentença em um intervalo.

        Args:
            words: Lista de palavras com timestamps (formato: {'word': str, 'start': float, 'end': float})
            start_time: Tempo inicial do clip em segundos
            end_time: Tempo final sugerido do clip em segundos

        Returns:
            Lista de boundaries: [{'time': float, 'type': str, 'word': str, 'score': int}, ...]
        """
        boundaries = []

        # Filtrar palavras no intervalo + buffer
        buffer_end = end_time + self.MAX_EXTENSION_SECONDS
        relevant_words = [
            w for w in words
            if w.get('start', 0) >= start_time and w.get('end', 0) <= buffer_end
        ]

        for i, word in enumerate(relevant_words):
            word_text = word.get('word', '').strip()
            word_end = word.get('end', 0)

            # 1. Verificar pontuação final
            if any(word_text.endswith(p) for p in self.SENTENCE_END_PUNCTUATION):
                boundaries.append({
                    'time': word_end,
                    'type': 'punctuation',
                    'word': word_text,
                    'score': 10  # Alta prioridade
                })

            # 2. Verificar pausa longa após a palavra
            if i < len(relevant_words) - 1:
                next_word = relevant_words[i + 1]
                gap = next_word.get('start', 0) - word_end

                if gap >= self.MIN_PAUSE_FOR_BOUNDARY:
                    boundaries.append({
                        'time': word_end,
                        'type': 'pause',
                        'word': word_text,
                        'gap': gap,
                        'score': 5 + min(gap * 2, 5)  # Pausas maiores = score maior
                    })

            # 3. Verificar padrões de conclusão
            for pattern in self.CONCLUSION_PATTERNS:
                if re.search(pattern, word_text.lower()):
                    boundaries.append({
                        'time': word_end,
                        'type': 'conclusion_pattern',
                        'word': word_text,
                        'score': 8
                    })

        # Ordenar por tempo
        boundaries.sort(key=lambda x: x['time'])
        return boundaries

    def adjust_clip_end(
        self,
        words: List[Dict],
        start_time: float,
        suggested_end: float,
        max_duration: float = 60
    ) -> Tuple[float, str]:
        """
        Ajusta o end_time do clip para o próximo limite de sentença.

        Args:
            words: Lista de palavras com timestamps
            start_time: Tempo inicial do clip em segundos
            suggested_end: Tempo final sugerido pela IA em segundos
            max_duration: Duração máxima permitida do clip em segundos

        Returns:
            Tupla (adjusted_end_time, adjustment_reason)
        """
        # Encontrar limites após o end sugerido
        boundaries = self.find_sentence_boundaries(words, start_time, suggested_end)

        # Filtrar apenas limites APÓS o end sugerido (ou muito próximos)
        tolerance = 0.3  # 300ms de tolerância
        candidates = [
            b for b in boundaries
            if b['time'] >= suggested_end - tolerance
        ]

        if not candidates:
            return suggested_end, "no_boundary_found"

        # Encontrar o melhor candidato
        for boundary in candidates:
            new_duration = boundary['time'] - start_time

            # Verificar se não excede o máximo
            if new_duration <= max_duration:
                extension = boundary['time'] - suggested_end

                # Aceitar se a extensão for razoável
                if extension <= self.MAX_EXTENSION_SECONDS:
                    return boundary['time'], f"extended_{boundary['type']}_{extension:.1f}s"

        # Se nenhum candidato válido, tentar encontrar boundary ANTES do end
        # (para não cortar no meio de uma palavra)
        pre_boundaries = [
            b for b in boundaries
            if b['time'] < suggested_end and b['time'] > start_time + 10
        ]

        if pre_boundaries:
            best = max(pre_boundaries, key=lambda x: x['score'])
            return best['time'], f"shortened_to_{best['type']}"

        return suggested_end, "kept_original"

    def validate_clip_completeness(
        self,
        words: List[Dict],
        start_time: float,
        end_time: float
    ) -> Dict:
        """
        Valida se um clip termina em um ponto completo.

        Args:
            words: Lista de palavras com timestamps
            start_time: Tempo inicial do clip em segundos
            end_time: Tempo final do clip em segundos

        Returns:
            Dict com: {'is_complete': bool, 'reason': str, 'last_word': str}
        """
        # Pegar últimas palavras do clip
        clip_words = [
            w for w in words
            if w.get('start', 0) >= start_time and w.get('end', 0) <= end_time
        ]

        if not clip_words:
            return {'is_complete': False, 'reason': 'no_words', 'last_word': ''}

        last_word = clip_words[-1].get('word', '').strip()

        # Verificar se termina com pontuação
        if any(last_word.endswith(p) for p in self.SENTENCE_END_PUNCTUATION):
            return {'is_complete': True, 'reason': 'ends_with_punctuation', 'last_word': last_word}

        # Verificar se há pausa após a última palavra
        word_end = clip_words[-1].get('end', 0)
        next_words = [w for w in words if w.get('start', 0) > word_end]

        if next_words:
            gap = next_words[0].get('start', 0) - word_end
            if gap >= self.MIN_PAUSE_FOR_BOUNDARY:
                return {'is_complete': True, 'reason': f'pause_after_{gap:.2f}s', 'last_word': last_word}

        # Verificar padrões de incompletude
        incomplete_endings = ['e', 'ou', 'mas', 'porque', 'que', 'de', 'do', 'da', 'para', 'com']
        if last_word.lower() in incomplete_endings:
            return {'is_complete': False, 'reason': 'ends_with_conjunction', 'last_word': last_word}

        return {'is_complete': False, 'reason': 'no_clear_boundary', 'last_word': last_word}
