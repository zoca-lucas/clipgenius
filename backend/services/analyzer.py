"""
ClipGenius - AI Clip Analyzer Service
Uses Groq (FREE cloud API) or Ollama (local) to analyze transcription and suggest viral clips
Groq is 10x faster with better quality models (70B parameters)
"""
import json
import re
import httpx
from typing import Dict, Any, List
from config import (
    NUM_CLIPS_TO_GENERATE,
    CLIP_MIN_DURATION,
    CLIP_MAX_DURATION,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    AI_PROVIDER
)


class ClipAnalyzer:
    """Service to analyze transcription and suggest viral clips using Groq or Ollama"""

    ANALYSIS_PROMPT = """Você é um especialista em conteúdo viral para redes sociais (TikTok, Reels, Shorts).

Analise a transcrição abaixo de um vídeo do YouTube e identifique os {num_clips} MELHORES momentos para criar cortes virais.

REGRAS IMPORTANTES:
1. Cada corte deve ter entre {min_duration} e {max_duration} segundos
2. O corte deve começar com um GANCHO forte (frase que prende atenção)
3. O corte deve ter uma ideia COMPLETA (não cortar no meio de um raciocínio)
4. Priorize momentos com: emoção, polêmica, humor, insights únicos, frases de impacto
5. Os cortes NÃO devem se sobrepor (timestamps únicos)
6. Ordene do MELHOR para o pior (maior nota primeiro)

CRITÉRIOS DE AVALIAÇÃO (nota de 0 a 10):
- Gancho inicial forte (0-2 pts): A primeira frase prende atenção?
- Conteúdo emocional/polêmico (0-2 pts): Gera reação emocional?
- Frase de impacto/citável (0-2 pts): Tem frases que as pessoas vão querer compartilhar?
- Completude da ideia (0-2 pts): O pensamento está completo?
- Potencial de compartilhamento (0-2 pts): As pessoas vão querer enviar para amigos?

TRANSCRIÇÃO COM TIMESTAMPS:
{transcription}

IMPORTANTE: Responda APENAS com JSON válido, sem texto adicional antes ou depois. Use este formato EXATO:

{{"clips": [{{"timestamp_inicio": "MM:SS", "timestamp_fim": "MM:SS", "titulo": "Título curto", "nota_viral": 8.5, "justificativa": "Por que é viral", "gancho": "Primeira frase"}}]}}

Retorne EXATAMENTE {num_clips} cortes."""

    def __init__(self, provider: str = None):
        """
        Initialize analyzer with specified provider

        Args:
            provider: "groq", "ollama", or "auto" (default)
                      auto = use Groq if API key exists, otherwise Ollama
        """
        self.provider = self._determine_provider(provider)

        if self.provider == "groq":
            self.model = GROQ_MODEL
            self._verify_groq()
        else:
            self.model = OLLAMA_MODEL
            self.base_url = OLLAMA_BASE_URL
            self._verify_ollama()

        print(f"🤖 AI Provider: {self.provider.upper()} ({self.model})")

    def _determine_provider(self, provider: str = None) -> str:
        """Determine which AI provider to use"""
        provider = provider or AI_PROVIDER

        if provider == "auto":
            # Use Groq if API key is available, otherwise Ollama
            if GROQ_API_KEY:
                return "groq"
            else:
                print("⚠️  GROQ_API_KEY não configurada, usando Ollama local")
                return "ollama"

        return provider

    def _verify_groq(self):
        """Verify Groq API key is configured"""
        if not GROQ_API_KEY:
            raise ValueError(
                "\n❌ GROQ_API_KEY não configurada!\n"
                "   \n"
                "   Para configurar:\n"
                "   1. Acesse: https://console.groq.com/keys\n"
                "   2. Crie uma API key gratuita\n"
                "   3. Adicione no .env: GROQ_API_KEY=sua_chave_aqui\n"
            )

        # Test connection
        try:
            response = httpx.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                timeout=10
            )
            if response.status_code != 200:
                raise ConnectionError(f"Groq API error: {response.status_code}")
            print("✅ Groq API conectada com sucesso!")
        except httpx.ConnectError:
            raise ConnectionError("❌ Não foi possível conectar à API do Groq")

    def _verify_ollama(self):
        """Verify Ollama is running and model is available"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError("Ollama não está respondendo")

            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]

            if self.model not in model_names and f"{self.model}:latest" not in [m.get("name") for m in models]:
                available = ", ".join(model_names) if model_names else "nenhum"
                print(f"⚠️  Modelo '{self.model}' não encontrado.")
                print(f"   Modelos disponíveis: {available}")
                print(f"   Execute: ollama pull {self.model}")

        except httpx.ConnectError:
            raise ConnectionError(
                "\n❌ Ollama não está rodando!\n"
                "   \n"
                "   Para instalar e iniciar:\n"
                "   1. Instale: https://ollama.ai\n"
                "   2. Execute: ollama serve\n"
                "   3. Baixe um modelo: ollama pull llama3.2\n"
            )

    def _format_transcription_for_prompt(self, transcription: Dict[str, Any]) -> str:
        """Format transcription with timestamps for the prompt"""
        lines = []

        for segment in transcription.get('segments', []):
            start = segment.get('start', 0)
            text = segment.get('text', '')

            # Format timestamp as MM:SS
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"

            lines.append(f"{timestamp} {text}")

        return '\n'.join(lines)

    def _parse_timestamp(self, timestamp: str) -> float:
        """Convert MM:SS to seconds"""
        try:
            parts = timestamp.replace('[', '').replace(']', '').split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return 0
        except (ValueError, IndexError):
            return 0

    def _call_groq(self, prompt: str) -> str:
        """Call Groq API (OpenAI-compatible)"""
        print(f"⚡ Chamando Groq ({self.model})... (muito mais rápido!)")

        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um assistente especializado em análise de conteúdo viral. Sempre responda em JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            timeout=httpx.Timeout(120.0, connect=30.0)
        )

        if response.status_code != 200:
            error_detail = response.json().get("error", {}).get("message", response.text)
            raise Exception(f"Groq API error: {error_detail}")

        return response.json()["choices"][0]["message"]["content"]

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        print(f"🤖 Chamando Ollama ({self.model})...")

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 4096,
                }
            },
            timeout=httpx.Timeout(600.0, connect=30.0)  # 10 minutes read timeout
        )

        if response.status_code != 200:
            raise Exception(f"Ollama error: {response.text}")

        return response.json().get("response", "")

    def _call_ai(self, prompt: str) -> str:
        """Call the configured AI provider"""
        if self.provider == "groq":
            return self._call_groq(prompt)
        else:
            return self._call_ollama(prompt)

    def _try_fix_json(self, text: str) -> Dict:
        """Try to fix common JSON parsing issues from LLM output"""
        # Try to extract just the clips array
        clips_match = re.search(r'\[.*\]', text, re.DOTALL)
        if clips_match:
            try:
                clips = json.loads(clips_match.group())
                return {"clips": clips}
            except:
                pass

        # Try to find individual clip objects
        clip_pattern = r'\{[^{}]*"timestamp_inicio"[^{}]*\}'
        matches = re.findall(clip_pattern, text)
        if matches:
            clips = []
            for match in matches:
                try:
                    clip = json.loads(match)
                    clips.append(clip)
                except:
                    continue
            if clips:
                return {"clips": clips}

        # Return empty result
        print("❌ Não foi possível extrair JSON válido da resposta")
        return {"clips": []}

    def analyze(
        self,
        transcription: Dict[str, Any],
        num_clips: int = None,
        min_duration: int = None,
        max_duration: int = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze transcription and return suggested clips

        Args:
            transcription: Transcription dict with segments
            num_clips: Number of clips to generate
            min_duration: Minimum clip duration in seconds
            max_duration: Maximum clip duration in seconds

        Returns:
            List of clip suggestions with timestamps and scores
        """
        num_clips = num_clips or NUM_CLIPS_TO_GENERATE
        min_duration = min_duration or CLIP_MIN_DURATION
        max_duration = max_duration or CLIP_MAX_DURATION

        # Format transcription for prompt
        formatted_transcription = self._format_transcription_for_prompt(transcription)

        # Build prompt
        prompt = self.ANALYSIS_PROMPT.format(
            num_clips=num_clips,
            min_duration=min_duration,
            max_duration=max_duration,
            transcription=formatted_transcription
        )

        provider_name = "Groq" if self.provider == "groq" else "Ollama"
        print(f"📊 Analisando transcrição com {provider_name}... (solicitando {num_clips} cortes)")

        # Call AI
        response_text = self._call_ai(prompt)

        # Parse JSON from response
        try:
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

        except json.JSONDecodeError as e:
            print(f"⚠️  Erro ao parsear JSON: {e}")
            print(f"   Tentando recuperar...")
            result = self._try_fix_json(response_text)

        # Process clips
        clips = []
        for clip_data in result.get('clips', []):
            start_seconds = self._parse_timestamp(clip_data.get('timestamp_inicio', '00:00'))
            end_seconds = self._parse_timestamp(clip_data.get('timestamp_fim', '00:00'))

            # Validate clip duration
            duration = end_seconds - start_seconds
            if duration < 10:  # Skip invalid clips
                continue

            clips.append({
                'start_time': start_seconds,
                'end_time': end_seconds,
                'duration': duration,
                'title': clip_data.get('titulo', 'Sem título'),
                'viral_score': float(clip_data.get('nota_viral', 5)),
                'justification': clip_data.get('justificativa', ''),
                'hook': clip_data.get('gancho', '')
            })

        # Sort by viral score (highest first)
        clips.sort(key=lambda x: x['viral_score'], reverse=True)

        print(f"✅ Gerados {len(clips)} cortes sugeridos")
        return clips


# Quick test
if __name__ == "__main__":
    print("🧪 Testando conexão com AI...")
    try:
        analyzer = ClipAnalyzer()
        print("✅ Analyzer inicializado com sucesso!")
        print(f"   Provider: {analyzer.provider}")
        print(f"   Modelo: {analyzer.model}")
    except (ConnectionError, ValueError) as e:
        print(e)
