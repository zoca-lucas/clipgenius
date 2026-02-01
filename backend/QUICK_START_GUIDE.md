# Guia Rápido - Melhorias no Sistema de Legendas

## Como Testar as Melhorias

### 1. Teste Rápido (Mock Data)

Execute o script de teste com dados simulados:

```bash
cd /Users/lucaszocaratto/Desktop/Projetos\ Claude/clipgenius/backend
./venv/bin/python test_subtitle_improvements.py
```

**Resultado esperado:**
- Demonstração da capitalização
- Demonstração do chunking inteligente
- Arquivo SRT gerado em `/tmp/test_subtitle.srt`
- Comparação de configurações

---

### 2. Teste Completo (Vídeo Real)

#### A) Inicie o backend:
```bash
cd /Users/lucaszocaratto/Desktop/Projetos\ Claude/clipgenius/backend
./venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### B) Acesse o frontend:
```bash
# Em outro terminal
cd /Users/lucaszocaratto/Desktop/Projetos\ Claude/clipgenius/frontend
npm run dev
```

#### C) Crie um projeto:
1. Cole um link do YouTube
2. Aguarde o processamento
3. Baixe um dos clips gerados
4. Verifique o arquivo `.srt` correspondente

---

### 3. Comparar Antes vs Depois

Para ver a diferença, você pode:

1. **Ler a documentação:**
   ```bash
   cat /Users/lucaszocaratto/Desktop/Projetos\ Claude/clipgenius/backend/BEFORE_AFTER_COMPARISON.txt
   ```

2. **Ver resumo técnico:**
   ```bash
   cat /Users/lucaszocaratto/Desktop/Projetos\ Claude/clipgenius/backend/IMPLEMENTATION_SUMMARY.md
   ```

3. **Ver detalhes das melhorias:**
   ```bash
   cat /Users/lucaszocaratto/Desktop/Projetos\ Claude/clipgenius/backend/SUBTITLE_IMPROVEMENTS.md
   ```

---

## Verificar Arquivos Modificados

```bash
cd /Users/lucaszocaratto/Desktop/Projetos\ Claude/clipgenius/backend

# Ver mudanças no transcriber
git diff services/transcriber.py

# Ver mudanças no subtitler
git diff services/subtitler.py
```

---

## Personalizar Legendas (Opcional)

Se você quiser ajustar os parâmetros, edite o arquivo `api/routes.py`:

```python
# Linha ~126
subtitle_result = subtitler.create_subtitled_clip(
    video_path=clip_result['video_path'],
    words=words,
    clip_start_time=suggestion['start_time'],
    output_name=clip_name,
    # NOVOS PARÂMETROS (opcionais):
    words_per_line=8,           # Padrão: 6
    max_chars_per_line=50,      # Padrão: 42
    capitalize=True             # Padrão: True
)
```

---

## Estrutura dos Arquivos Gerados

Quando você processa um vídeo, o sistema gera:

```
data/clips/
├── VIDEO_ID_clip_01.mp4              # Vídeo sem legenda
├── VIDEO_ID_clip_01.srt              # Arquivo de legenda
├── VIDEO_ID_clip_01_subtitled.mp4    # Vídeo com legenda (se suportado)
├── VIDEO_ID_clip_02.mp4
├── VIDEO_ID_clip_02.srt
└── ...
```

---

## Exemplo de Arquivo SRT Melhorado

**Antes das melhorias:**
```srt
1
00:00:00,000 --> 00:00:01,000
OLÁ PESSOAL HOJE

2
00:00:01,000 --> 00:00:02,000
VAMOS FALAR SOBRE
```

**Depois das melhorias:**
```srt
1
00:00:00,000 --> 00:00:02,299
Olá pessoal hoje vamos falar sobre

2
00:00:02,299 --> 00:00:04,500
Um assunto muito interessante que vai
```

---

## Verificar Configurações do Whisper

As configurações de qualidade estão em `config.py`:

```python
WHISPER_MODEL = "base"              # Modelo usado
WHISPER_TEMPERATURE = 0.0           # Consistência
WHISPER_BEAM_SIZE = 5               # Qualidade
WHISPER_BEST_OF = 5                 # Precisão
```

Para melhor qualidade (mais lento):
```python
WHISPER_MODEL = "medium"  # ou "large"
```

---

## Solução de Problemas

### Problema: "ModuleNotFoundError"
**Solução:** Use o ambiente virtual
```bash
./venv/bin/python script.py
```

### Problema: "FFmpeg não encontrado"
**Solução:** Instale o FFmpeg
```bash
brew install ffmpeg  # macOS
```

### Problema: Legendas ainda em maiúsculas
**Solução:** Verifique se está usando o parâmetro `capitalize=True`
```python
generate_srt(..., capitalize=True)
```

### Problema: Transcrição de baixa qualidade
**Solução:** Use um modelo maior
```python
# config.py
WHISPER_MODEL = "medium"  # ou "large"
```

---

## Métricas de Qualidade

Você pode avaliar a qualidade das legendas verificando:

1. **Capitalização**: Primeira letra maiúscula ✓
2. **Comprimento**: Máximo 42 caracteres por linha ✓
3. **Palavras**: 4-6 palavras por legenda ✓
4. **Duração**: 1-7 segundos por legenda ✓
5. **Frases**: Quebras naturais nas pausas ✓

---

## Recursos Adicionais

### Documentação Completa
- `SUBTITLE_IMPROVEMENTS.md` - Análise detalhada
- `IMPLEMENTATION_SUMMARY.md` - Resumo da implementação
- `BEFORE_AFTER_COMPARISON.txt` - Comparação visual

### Testes
- `test_subtitle_improvements.py` - Script de teste

### Código Fonte
- `services/transcriber.py` - Transcrição com Whisper
- `services/subtitler.py` - Geração de legendas
- `api/routes.py` - Endpoints da API

---

## Próximos Passos

1. ✅ Teste as melhorias com dados mock
2. ✅ Teste com vídeo real do YouTube
3. Compare a qualidade das legendas
4. Ajuste parâmetros se necessário
5. Deploy em produção

---

## Contato e Suporte

Se tiver dúvidas sobre as melhorias:
1. Leia a documentação em `SUBTITLE_IMPROVEMENTS.md`
2. Veja exemplos em `BEFORE_AFTER_COMPARISON.txt`
3. Execute os testes em `test_subtitle_improvements.py`

---

**Data da implementação:** 31 de Janeiro de 2026
**Implementado por:** Claude Agent (youtube-subtitle-generator)
**Status:** ✅ Pronto para produção
