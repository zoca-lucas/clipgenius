#!/bin/bash
# ClipGenius - Iniciar servidor backend

cd "$(dirname "$0")"

# Ativar ambiente virtual
source venv/bin/activate

# Iniciar servidor
echo "==================================================="
echo "   ClipGenius Backend - V2 (Legendas Melhoradas)"
echo "==================================================="
echo ""
echo "Melhorias implementadas:"
echo "  - TranscriberV2: timestamps mais precisos"
echo "  - SubtitleGeneratorV2: tamanho consistente"
echo "  - Pós-processamento de timestamps"
echo "  - Chunking inteligente de legendas"
echo ""
echo "Iniciando servidor em http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""

python main.py
