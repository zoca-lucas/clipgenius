# 🎬 ClipGenius - Gerador Automático de Cortes com IA

Transforme vídeos longos do YouTube em cortes virais automaticamente usando IA.

**💰 100% GRATUITO - Usa Ollama (IA local) + Whisper**

![ClipGenius Demo](https://via.placeholder.com/800x400?text=ClipGenius+Demo)

## ✨ Funcionalidades

- 📥 **Download automático** do YouTube via yt-dlp
- 🎙️ **Transcrição com Whisper** - legendas sincronizadas (gratuito, local)
- 🤖 **Análise com Ollama** - IA local gratuita identifica os melhores momentos
- ✂️ **15 cortes automáticos** - formato 9:16 para Shorts/Reels
- ⭐ **Notas de viralidade** - cada corte recebe nota de 0-10
- 📝 **Legendas estilizadas** - burn-in automático

## 🛠️ Tecnologias

| Componente | Tecnologia | Custo |
|------------|------------|-------|
| Backend | Python + FastAPI | Gratuito |
| Frontend | Next.js 14 + React | Gratuito |
| Transcrição | OpenAI Whisper (local) | **Gratuito** |
| Análise IA | **Ollama (local)** | **Gratuito** |
| Vídeo | FFmpeg | Gratuito |
| Download | yt-dlp | Gratuito |
| Database | SQLite | Gratuito |

## 📋 Pré-requisitos

- Python 3.9+
- Node.js 18+
- FFmpeg instalado no sistema
- **Ollama** instalado (IA local gratuita)

### Instalando FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
```bash
winget install ffmpeg
```

### 🤖 Instalando Ollama (IMPORTANTE!)

Ollama é a IA local que analisa os vídeos. 100% gratuito e privado.

**1. Instale o Ollama:**
```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Ou baixe em: https://ollama.ai/download
```

**2. Baixe um modelo:**
```bash
# Recomendado para Mac (rápido e bom)
ollama pull llama3.2

# Alternativas:
# ollama pull mistral     # Mais leve
# ollama pull llama3.1    # Mais potente
```

**3. Verifique se está funcionando:**
```bash
ollama list
# Deve mostrar: llama3.2:latest
```

## 🚀 Instalação

### 1. Vá para o diretório

```bash
cd ~/clipgenius
```

### 2. Configure o Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou: venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configure o Frontend

```bash
cd ../frontend

# Instalar dependências
npm install
```

## 🎯 Como Usar

### 1. Inicie o Ollama (em um terminal)

```bash
ollama serve
```

### 2. Inicie o Backend (em outro terminal)

```bash
cd ~/clipgenius/backend
source venv/bin/activate
python main.py
```

O backend estará em: http://localhost:8000

### 3. Inicie o Frontend (em outro terminal)

```bash
cd ~/clipgenius/frontend
npm run dev
```

O frontend estará em: http://localhost:3000

### 4. Use o App

1. Acesse http://localhost:3000
2. Cole um link do YouTube
3. Clique em "Gerar Cortes"
4. Aguarde o processamento (alguns minutos)
5. Visualize e baixe seus cortes!

## 📁 Estrutura do Projeto

```
clipgenius/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configurações
│   ├── models/              # Modelos do banco
│   ├── services/            # Serviços (download, transcrição, etc)
│   ├── api/                 # Rotas da API
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Páginas Next.js
│   │   ├── components/      # Componentes React
│   │   └── lib/             # Utilitários e API client
│   └── package.json
└── data/
    ├── videos/              # Vídeos originais
    ├── clips/               # Cortes gerados
    ├── audio/               # Áudios extraídos
    └── database.db          # SQLite
```

## 🔧 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/projects` | Criar projeto (URL do YouTube) |
| GET | `/api/projects` | Listar projetos |
| GET | `/api/projects/{id}` | Detalhes do projeto |
| GET | `/api/projects/{id}/status` | Status do processamento |
| GET | `/api/projects/{id}/clips` | Listar cortes |
| GET | `/api/clips/{id}/download` | Baixar corte |
| DELETE | `/api/projects/{id}` | Deletar projeto |
| DELETE | `/api/clips/{id}` | Deletar corte |

## ⚙️ Configurações

### Variáveis de Ambiente (backend/.env)

```env
# Ollama (IA local gratuita)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Whisper (transcrição local)
WHISPER_MODEL=base

# Diretórios
DATA_DIR=../data
DATABASE_URL=sqlite:///../data/database.db
```

### Modelos do Ollama

| Modelo | RAM | Velocidade | Qualidade |
|--------|-----|------------|-----------|
| mistral | ~4GB | Muito rápido | Boa |
| llama3.2 | ~4GB | Rápido | Muito boa |
| llama3.1 | ~8GB | Moderado | Excelente |
| llama3.1:70b | ~40GB | Lento | Máxima |

### Modelos do Whisper

| Modelo | VRAM | Velocidade | Qualidade |
|--------|------|------------|-----------|
| tiny | ~1GB | Muito rápido | Básica |
| base | ~1GB | Rápido | Boa |
| small | ~2GB | Moderado | Muito boa |
| medium | ~5GB | Lento | Excelente |
| large | ~10GB | Muito lento | Máxima |

## 💡 Dicas

1. **Vídeos curtos primeiro**: Teste com vídeos de 5-10 minutos
2. **Modelo Whisper**: Use `base` para equilíbrio velocidade/qualidade
3. **Modelo Ollama**: Use `llama3.2` para melhor custo-benefício
4. **GPU**: Se tiver NVIDIA, Whisper e Ollama usam CUDA automaticamente
5. **Legendas**: Edite o arquivo .ass se quiser customizar o estilo

## 💰 Custos

| Item | Custo |
|------|-------|
| Ollama | **Gratuito** (local) |
| Whisper | **Gratuito** (local) |
| FFmpeg | **Gratuito** |
| **Total por vídeo** | **R$ 0,00** |

## 🐛 Troubleshooting

### Ollama não está rodando
```bash
# Inicie o Ollama
ollama serve

# Em outro terminal, verifique
curl http://localhost:11434/api/tags
```

### Modelo não encontrado
```bash
# Baixe o modelo
ollama pull llama3.2

# Liste modelos disponíveis
ollama list
```

### FFmpeg não encontrado
```bash
# Verifique a instalação
ffmpeg -version

# macOS
brew install ffmpeg
```

### Erro de CUDA/GPU
```bash
# Use CPU se não tiver GPU NVIDIA
# Ollama e Whisper detectam automaticamente
```

### Processamento muito lento
```bash
# Use modelos menores
# Em backend/.env:
OLLAMA_MODEL=mistral
WHISPER_MODEL=tiny
```

## 📜 Licença

MIT License - Use como quiser para projetos pessoais!

---

**Feito com ❤️ usando Ollama, Whisper e FFmpeg - 100% Gratuito!**
