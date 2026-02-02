"""
ClipGenius - AI Clip Analyzer Service
Uses Groq (FREE cloud API), Minimax, or Ollama (local) to analyze transcription and suggest viral clips
Groq is 10x faster with high quality models (70B parameters)
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
    MINIMAX_API_KEY,
    MINIMAX_MODEL,
    MINIMAX_BASE_URL,
    AI_PROVIDER
)
from logging_config import get_service_logger

logger = get_service_logger("analyzer")


class ClipAnalyzer:
    """Service to analyze transcription and suggest viral clips using Groq, Minimax, or Ollama"""

    ANALYSIS_PROMPT = """🎯 SISTEMA ESPECIALIZADO EM ANÁLISE E GERAÇÃO DE CORTES VIRAIS PARA TIKTOK/REELS/SHORTS

Você é um EDITOR PROFISSIONAL de vídeos virais que aplica:
- Raciocínio MINIMAX (maximizar chance de viralização, minimizar risco de cortes fracos)
- Conhecimento profundo de padrões virais do TikTok, Instagram Reels e YouTube Shorts
- Técnicas dos maiores criadores de conteúdo viral (Alex Hormozi, MrBeast, etc.)

⚠️ REGRA CRÍTICA: NUNCA retorne zero cortes. SEMPRE selecione pelo menos 1 corte, mesmo que o conteúdo seja fraco.

📊 PARÂMETROS:
- CORTES SOLICITADOS: {num_clips}
- DURAÇÃO MÍNIMA: {min_duration}s | MÁXIMA: {max_duration}s
- DURAÇÃO IDEAL: 20-35 segundos (MELHOR para conteúdo completo + algoritmo viral)
- ⚠️ CLIPS MENORES QUE {min_duration}s SERÃO REJEITADOS AUTOMATICAMENTE

🚨🚨🚨 REGRA MAIS IMPORTANTE - COMPLETUDE DO CONTEÚDO 🚨🚨🚨

**NUNCA, EM HIPÓTESE ALGUMA, CORTE NO MEIO DE:**
- Uma explicação que está sendo dada (ex: "a fórmula é..." → ESPERE A FÓRMULA COMPLETA)
- Uma história sendo contada (ex: "então aconteceu..." → ESPERE O DESFECHO)
- Uma lista de itens (ex: "primeiro..., segundo..." → INCLUA TODOS OS ITENS)
- Uma pergunta sendo respondida (ex: "a resposta é..." → INCLUA A RESPOSTA)
- Um conceito sendo explicado (ex: "isso funciona porque..." → INCLUA A EXPLICAÇÃO)
- Uma revelação/insight (ex: "o segredo é..." → INCLUA O SEGREDO COMPLETO)

**ONDE COMEÇAR O CORTE:**
✅ Logo ANTES de uma pergunta/promessa ("Você sabe qual é...", "O segredo é...")
✅ No início de uma nova ideia/tópico
✅ Quando alguém levanta um problema/dor
✅ Em momentos de tensão/curiosidade

**ONDE TERMINAR O CORTE:**
✅ DEPOIS que a ideia foi COMPLETAMENTE explicada
✅ DEPOIS de uma conclusão natural ("...então é isso", "...entendeu?", pausa longa)
✅ DEPOIS de uma frase de impacto/punchline
✅ Em um momento de pausa natural na fala
✅ DEPOIS de responder a pergunta que foi feita no início
❌ NUNCA termine com "então a fórmula é..." sem dar a fórmula
❌ NUNCA termine com "e aí..." deixando no ar
❌ NUNCA termine no meio de uma frase

**TESTE DE COMPLETUDE:**
Antes de definir o timestamp_fim, pergunte-se:
1. "Se eu fosse o espectador, eu ficaria frustrado por não saber o resto?"
2. "A ideia principal foi entregue por completo?"
3. "O corte faz sentido sozinho, sem contexto adicional?"
Se a resposta for NÃO para qualquer pergunta, ESTENDA o timestamp_fim até a conclusão.

🔍 FLUXO DE ANÁLISE:

**1. MAPEAMENTO DE MOMENTOS VIRAIS**
Identifique na transcrição os seguintes gatilhos:

🎭 MUDANÇAS EMOCIONAIS (prioridade máxima):
- Surpresa ou revelação inesperada
- Raiva ou indignação genuína
- Felicidade ou entusiasmo contagiante

❓ MOMENTOS DE CLAREZA:
- Dúvidas sendo respondidas de forma clara e COMPLETA
- "Aha moments" - quando algo faz sentido
- Explicações simples de conceitos complexos (INCLUIR EXPLICAÇÃO TODA)

💬 FRASES DE IMPACTO:
- Declarações polêmicas ou controversas
- Ensinamentos rápidos e aplicáveis (INCLUIR O ENSINAMENTO COMPLETO)
- Gatilhos: "ninguém te conta", "o segredo é", "pare de fazer isso"

**2. REGRA DOS 3 SEGUNDOS (HOOK)**
Os PRIMEIROS 3 SEGUNDOS decidem se a pessoa continua assistindo.
O corte DEVE começar com:
- Uma pergunta intrigante
- Uma declaração chocante
- Uma promessa de valor
- Um momento de tensão

**3. ESTRUTURA IDEAL DO CORTE**
- HOOK (0-3s): Captura atenção imediata
- CONTEÚDO (3-30s): Entrega valor COMPLETO
- FECHAMENTO (últimos segundos): Conclusão satisfatória, não corte abrupto

**4. PONTUAÇÃO VIRAL (nota_viral 0-10):**

| Critério | Pontos | Descrição |
|----------|--------|-----------|
| HOOK | 0-2 | Primeiros 3 segundos PRENDEM? |
| ENTREGA | 0-3 | O conteúdo prometido é ENTREGUE POR COMPLETO? |
| FECHAMENTO | 0-2 | Termina de forma satisfatória? Não deixa no ar? |
| ENGAJAMENTO | 0-2 | Gera comentários? Debate? |
| STANDALONE | 0-1 | Faz sentido sozinho sem contexto? |

**5. REGRAS DE VALIDAÇÃO:**
- Cortes NÃO podem se sobrepor (timestamps únicos)
- Ordene do MELHOR para o PIOR (maior nota primeiro)
- SEMPRE inclua a conclusão do raciocínio no corte
- Se a explicação é longa, é MELHOR ter um clip de 40s completo do que um de 25s incompleto
- NUNCA retorne lista vazia

📝 TRANSCRIÇÃO PARA ANÁLISE:
{transcription}

📦 RESPONDA APENAS COM JSON VÁLIDO:
{{"clips": [
  {{
    "timestamp_inicio": "MM:SS",
    "timestamp_fim": "MM:SS",
    "titulo": "Título chamativo e curto (máx 60 chars)",
    "nota_viral": 8.5,
    "justificativa": "Por que vai viralizar E por que o corte está completo",
    "gancho": "Primeira frase exata do corte (o HOOK)",
    "fecho": "Última frase do corte (deve ser uma conclusão satisfatória)",
    "categoria": "emocao|curiosidade|humor|polemico|educativo|revelacao",
    "conteudo_completo": true
  }}
]}}

🎯 MISSÃO: Retorne EXATAMENTE {num_clips} cortes com conteúdo COMPLETO e satisfatório.
Cada corte deve entregar o que promete no início - NUNCA deixe o espectador frustrado."""

    def __init__(self, provider: str = None):
        """
        Initialize analyzer with specified provider

        Args:
            provider: "groq", "minimax", "ollama", or "auto" (default)
                      auto = use Groq if key exists, otherwise Minimax, otherwise Ollama
        """
        self.provider = self._determine_provider(provider)

        if self.provider == "groq":
            self.model = GROQ_MODEL
            self._verify_groq()
        elif self.provider == "minimax":
            self.model = MINIMAX_MODEL
            self.base_url = MINIMAX_BASE_URL
            self._verify_minimax()
        else:
            self.model = OLLAMA_MODEL
            self.base_url = OLLAMA_BASE_URL
            self._verify_ollama()

        logger.info("AI provider initialized", provider=self.provider.upper(), model=self.model)
        print(f"AI Provider: {self.provider.upper()} ({self.model})")

    def _determine_provider(self, provider: str = None) -> str:
        """Determine which AI provider to use"""
        provider = provider or AI_PROVIDER

        if provider == "auto":
            # Use Groq if API key is available and not empty/placeholder
            if GROQ_API_KEY and GROQ_API_KEY.strip() and not GROQ_API_KEY.startswith("your-"):
                return "groq"
            # Otherwise try Minimax
            elif MINIMAX_API_KEY and MINIMAX_API_KEY.strip() and not MINIMAX_API_KEY.startswith("your-"):
                return "minimax"
            else:
                logger.warning("No API key configured, falling back to local Ollama")
                print("No API key configured, using local Ollama")
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
                logger.error("Groq API connection failed", status_code=response.status_code)
                raise ConnectionError(f"Groq API error: {response.status_code}")
            logger.info("Groq API connected successfully")
            print("Groq API connected successfully!")
        except httpx.ConnectError as e:
            logger.error("Failed to connect to Groq API", error=str(e))
            raise ConnectionError("Could not connect to Groq API")

    def _verify_minimax(self):
        """Verify Minimax API key is configured"""
        if not MINIMAX_API_KEY:
            raise ValueError(
                "\n❌ MINIMAX_API_KEY não configurada!\n"
                "   \n"
                "   Para configurar:\n"
                "   1. Acesse: https://platform.minimax.io/\n"
                "   2. Crie uma API key\n"
                "   3. Adicione no .env: MINIMAX_API_KEY=sua_chave_aqui\n"
            )

        # Test connection with a simple request
        try:
            response = httpx.post(
                f"{MINIMAX_BASE_URL}/v1/messages",
                headers={
                    "x-api-key": MINIMAX_API_KEY,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": self.model,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "test"}]
                },
                timeout=30
            )
            # Accept 200 (success) or 400 (bad request but API is reachable)
            if response.status_code not in [200, 400]:
                logger.error("Minimax API connection failed", status_code=response.status_code)
                raise ConnectionError(f"Minimax API error: {response.status_code}")
            logger.info("Minimax API connected successfully")
            print("Minimax API connected successfully!")
        except httpx.ConnectError as e:
            logger.error("Failed to connect to Minimax API", error=str(e))
            raise ConnectionError("Could not connect to Minimax API")

    def _verify_ollama(self):
        """Verify Ollama is running and model is available"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError("Ollama não está respondendo")

            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]

            if self.model not in model_names and f"{self.model}:latest" not in [m.get("name") for m in models]:
                available = ", ".join(model_names) if model_names else "none"
                logger.warning(
                    "Ollama model not found",
                    requested_model=self.model,
                    available_models=available
                )
                print(f"Model '{self.model}' not found.")
                print(f"   Available models: {available}")
                print(f"   Run: ollama pull {self.model}")

        except httpx.ConnectError as e:
            logger.error("Ollama is not running", error=str(e))
            raise ConnectionError(
                "\nOllama is not running!\n"
                "   \n"
                "   To install and start:\n"
                "   1. Install: https://ollama.ai\n"
                "   2. Run: ollama serve\n"
                "   3. Pull a model: ollama pull llama3.2\n"
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
        logger.info("Calling Groq API", model=self.model)
        print(f"Calling Groq ({self.model})...")

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
            logger.error("Groq API request failed", status_code=response.status_code, error=error_detail)
            raise Exception(f"Groq API error: {error_detail}")

        return response.json()["choices"][0]["message"]["content"]

    def _call_minimax(self, prompt: str) -> str:
        """Call Minimax API (Anthropic-compatible endpoint)"""
        logger.info("Calling Minimax API", model=self.model)
        print(f"Calling Minimax ({self.model})...")

        # Build the system prompt and user message
        system_prompt = "Você é um assistente especializado em análise de conteúdo viral. Sempre responda em JSON válido."

        response = httpx.post(
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": MINIMAX_API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": self.model,
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
            },
            timeout=httpx.Timeout(300.0, connect=30.0)  # 5 minutes timeout for long analysis
        )

        if response.status_code != 200:
            error_detail = response.json().get("error", {}).get("message", response.text)
            logger.error("Minimax API request failed", status_code=response.status_code, error=error_detail)
            raise Exception(f"Minimax API error: {error_detail}")

        # Anthropic format returns content as a list of blocks
        result = response.json()
        content_blocks = result.get("content", [])
        if content_blocks and isinstance(content_blocks, list):
            # Extract text from content blocks
            text_parts = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
            return "".join(text_parts)

        return ""

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        logger.info("Calling Ollama API", model=self.model)
        print(f"Calling Ollama ({self.model})...")

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
            logger.error("Ollama API request failed", status_code=response.status_code, error=response.text)
            raise Exception(f"Ollama error: {response.text}")

        return response.json().get("response", "")

    def _call_ai(self, prompt: str) -> str:
        """Call the configured AI provider"""
        if self.provider == "groq":
            return self._call_groq(prompt)
        elif self.provider == "minimax":
            return self._call_minimax(prompt)
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
            except Exception:
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
                except Exception:
                    continue
            if clips:
                return {"clips": clips}

        # Return empty result
        logger.error("Failed to extract valid JSON from AI response", response_preview=text[:200])
        print("Could not extract valid JSON from response")
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

        # Validate transcription format
        if not transcription or not isinstance(transcription, dict):
            raise ValueError("Transcrição inválida: deve ser um dicionário")

        segments = transcription.get('segments', [])
        if not segments:
            raise ValueError("Transcrição inválida: não contém segmentos")

        # Format transcription for prompt
        formatted_transcription = self._format_transcription_for_prompt(transcription)

        # Build prompt
        prompt = self.ANALYSIS_PROMPT.format(
            num_clips=num_clips,
            min_duration=min_duration,
            max_duration=max_duration,
            transcription=formatted_transcription
        )

        provider_names = {"groq": "Groq", "minimax": "Minimax", "ollama": "Ollama"}
        provider_name = provider_names.get(self.provider, self.provider)
        logger.info(
            "Starting transcription analysis",
            provider=provider_name,
            num_clips_requested=num_clips,
            min_duration=min_duration,
            max_duration=max_duration,
            segments_count=len(segments)
        )
        print(f"Analyzing transcription with {provider_name}... (requesting {num_clips} clips)")

        # Call AI
        response_text = self._call_ai(prompt)

        # Debug: show first 500 chars of response
        logger.debug("AI response received", response_length=len(response_text), preview=response_text[:200])
        print(f"AI Response (first 500 chars):")
        print(response_text[:500] if len(response_text) > 500 else response_text)
        print("---")

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
            logger.warning("JSON parse error, attempting recovery", error=str(e))
            print(f"JSON parse error: {e}")
            print(f"   Attempting recovery...")
            result = self._try_fix_json(response_text)

        # Process clips
        clips = []
        raw_clips_count = len(result.get('clips', []))
        logger.info("Processing clips from AI response", raw_clips_count=raw_clips_count)
        print(f"Processing {raw_clips_count} clips from response...")
        for i, clip_data in enumerate(result.get('clips', [])):
            start_seconds = self._parse_timestamp(clip_data.get('timestamp_inicio', '00:00'))
            end_seconds = self._parse_timestamp(clip_data.get('timestamp_fim', '00:00'))
            duration = end_seconds - start_seconds

            print(f"   Clip {i+1}: {clip_data.get('timestamp_inicio')} - {clip_data.get('timestamp_fim')} = {duration}s")

            # Validate clip duration using configured minimum
            if duration < min_duration:
                logger.debug("Clip rejected: too short", clip_index=i+1, duration=duration, min_duration=min_duration)
                print(f"   Rejected: duration too short ({duration}s < {min_duration}s)")
                continue

            # Validate maximum duration
            if duration > max_duration:
                logger.debug("Clip rejected: too long", clip_index=i+1, duration=duration, max_duration=max_duration)
                print(f"   Rejected: duration too long ({duration}s > {max_duration}s)")
                continue

            # Safe conversion of viral score
            try:
                viral_score = float(clip_data.get('nota_viral', 5))
                viral_score = max(0, min(10, viral_score))  # Clamp between 0-10
            except (ValueError, TypeError):
                viral_score = 5.0

            # Check if content is marked as complete
            is_complete = clip_data.get('conteudo_completo', True)
            if not is_complete:
                logger.warning("Clip marked as incomplete content", clip_index=i+1)
                print(f"   ⚠️ Warning: Clip {i+1} was marked as incomplete content")

            clips.append({
                'start_time': start_seconds,
                'end_time': end_seconds,
                'duration': duration,
                'title': clip_data.get('titulo', 'Sem título'),
                'viral_score': viral_score,
                'justification': clip_data.get('justificativa', ''),
                'hook': clip_data.get('gancho', ''),
                'closing': clip_data.get('fecho', ''),  # New field for the closing phrase
                'category': clip_data.get('categoria', 'insight'),
                'is_complete': is_complete
            })

        # Sort by viral score (highest first)
        clips.sort(key=lambda x: x['viral_score'], reverse=True)

        # FALLBACK: Nunca retornar 0 clips
        if len(clips) == 0 and raw_clips_count > 0:
            logger.warning("All clips rejected, applying fallback with relaxed duration")
            print("⚠️ Todos os clips foram rejeitados. Aplicando fallback com duração relaxada...")

            # Tentar novamente com duração mínima de 10 segundos (fallback relaxado)
            fallback_min_duration = 10
            for i, clip_data in enumerate(result.get('clips', [])):
                start_seconds = self._parse_timestamp(clip_data.get('timestamp_inicio', '00:00'))
                end_seconds = self._parse_timestamp(clip_data.get('timestamp_fim', '00:00'))
                duration = end_seconds - start_seconds

                # Aceitar clips com pelo menos 10 segundos no fallback
                if duration >= fallback_min_duration and duration <= max_duration:
                    try:
                        viral_score = float(clip_data.get('nota_viral', 5))
                        viral_score = max(0, min(10, viral_score))
                    except (ValueError, TypeError):
                        viral_score = 5.0

                    clips.append({
                        'start_time': start_seconds,
                        'end_time': end_seconds,
                        'duration': duration,
                        'title': clip_data.get('titulo', 'Sem título'),
                        'viral_score': viral_score,
                        'justification': clip_data.get('justificativa', ''),
                        'hook': clip_data.get('gancho', ''),
                        'closing': clip_data.get('fecho', ''),
                        'category': clip_data.get('categoria', 'insight'),
                        'is_complete': clip_data.get('conteudo_completo', True)
                    })
                    print(f"   ✅ Clip {i+1} aceito via fallback (min {fallback_min_duration}s): {duration}s")

            clips.sort(key=lambda x: x['viral_score'], reverse=True)

        # FALLBACK FINAL: Se ainda não há clips, criar do melhor segmento disponível
        if len(clips) == 0:
            logger.warning("No clips found, creating fallback from best segment")
            print("⚠️ Nenhum clip encontrado. Criando clip do melhor segmento disponível...")

            segments = transcription.get('segments', [])
            if segments:
                # Encontrar sequência de segmentos com boa duração (15-30 segundos ideal)
                best_start = segments[0].get('start', 0)
                video_end = segments[-1].get('end', 30)
                best_end = min(best_start + 25, video_end)  # 25 segundos ideal

                # Garantir duração mínima de 15 segundos
                if best_end - best_start < 15:
                    best_end = best_start + min(20, video_end - best_start)

                # Construir texto do clip
                clip_text = ""
                for seg in segments:
                    if seg.get('start', 0) >= best_start and seg.get('end', 0) <= best_end:
                        clip_text += seg.get('text', '') + " "

                clips.append({
                    'start_time': best_start,
                    'end_time': best_end,
                    'duration': best_end - best_start,
                    'title': 'Destaque do Vídeo',
                    'viral_score': 5.0,
                    'justification': 'Clip gerado automaticamente do início do vídeo',
                    'hook': clip_text[:100].strip() if clip_text else 'Confira este momento',
                    'closing': '',
                    'category': 'insight',
                    'is_complete': True
                })
                print(f"   ✅ Clip fallback criado: {best_start:.0f}s - {best_end:.0f}s ({best_end - best_start:.0f}s)")

        logger.info(
            "Clip analysis completed",
            clips_generated=len(clips),
            clips_rejected=raw_clips_count - len(clips),
            provider=self.provider
        )
        print(f"Generated {len(clips)} clip suggestions")
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
