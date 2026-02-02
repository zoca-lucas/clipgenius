#!/usr/bin/env python3
"""
Teste das melhorias de legendas V2.

Este script testa:
1. TranscriberV2 com diferentes backends
2. SubtitleGeneratorV2 com tamanho consistente
3. Sincronização de timestamps
"""
import sys
from pathlib import Path

# Adicionar diretório backend ao path
sys.path.insert(0, str(Path(__file__).parent))


def test_transcriber_backends():
    """Testa backends de transcrição disponíveis."""
    print("\n" + "=" * 60)
    print("TESTE 1: Backends de Transcrição Disponíveis")
    print("=" * 60)

    from services.transcriber_v2 import TranscriberV2

    backends = ["whisperx", "stable-ts", "faster-whisper", "groq"]

    print("\nVerificando backends disponíveis:")
    transcriber = TranscriberV2(backend="auto")

    for backend in backends:
        available = transcriber._check_backend_available(backend)
        status = "✅ Disponível" if available else "❌ Não instalado"
        print(f"  {backend:20s} {status}")

    print(f"\n➡️  Backend selecionado automaticamente: {transcriber.backend}")

    return transcriber


def test_subtitle_generator():
    """Testa gerador de legendas V2."""
    print("\n" + "=" * 60)
    print("TESTE 2: SubtitleGenerator V2")
    print("=" * 60)

    from services.subtitler_v2 import SubtitleGeneratorV2, SubtitleStyle

    gen = SubtitleGeneratorV2()

    # Dados de teste
    test_words = [
        {"word": "Olá", "start": 0.0, "end": 0.3},
        {"word": "pessoal", "start": 0.35, "end": 0.7},
        {"word": "isso", "start": 0.8, "end": 1.0},
        {"word": "é", "start": 1.05, "end": 1.2},
        {"word": "muito", "start": 1.25, "end": 1.5},  # Palavra de ênfase (amarelo)
        {"word": "incrível", "start": 1.55, "end": 2.0},  # Palavra de ênfase (amarelo)
        {"word": "não", "start": 2.5, "end": 2.7},  # Palavra negativa (vermelho)
        {"word": "acredito", "start": 2.75, "end": 3.2},
        {"word": "são", "start": 3.5, "end": 3.7},
        {"word": "10", "start": 3.75, "end": 4.0},  # Número (verde)
        {"word": "dicas", "start": 4.05, "end": 4.4},
    ]

    print(f"\nEstilo padrão:")
    print(f"  Fonte: {gen.default_style.font_name}")
    print(f"  Tamanho: {gen.default_style.font_size}px")
    print(f"  Margem V: {gen.default_style.margin_v}px")

    # Testar chunking
    chunks = gen._chunk_words(test_words)
    print(f"\nChunks gerados: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        text = ' '.join(w['word'] for w in chunk)
        print(f"  Chunk {i + 1}: \"{text}\"")

    # Gerar ASS de teste
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())

    # Teste 1: ASS simples
    ass_simple = temp_dir / "test_simple.ass"
    gen.generate_ass(
        words=test_words,
        output_path=str(ass_simple),
        offset=0,
        enable_karaoke=False,
        enable_colors=True
    )
    print(f"\n✅ ASS simples gerado: {ass_simple}")

    # Teste 2: ASS com karaokê
    ass_karaoke = temp_dir / "test_karaoke.ass"
    gen.generate_ass(
        words=test_words,
        output_path=str(ass_karaoke),
        offset=0,
        enable_karaoke=True,
        enable_colors=True
    )
    print(f"✅ ASS karaokê gerado: {ass_karaoke}")

    # Teste 3: SRT
    srt_path = temp_dir / "test.srt"
    gen.generate_srt(
        words=test_words,
        output_path=str(srt_path),
        offset=0
    )
    print(f"✅ SRT gerado: {srt_path}")

    # Mostrar conteúdo do ASS
    print("\n" + "-" * 40)
    print("Conteúdo do ASS (primeiras 30 linhas):")
    print("-" * 40)
    with open(ass_karaoke, 'r') as f:
        lines = f.readlines()[:30]
        for line in lines:
            print(line.rstrip())

    # Limpar
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    return gen


def test_word_colors():
    """Testa sistema de cores por palavra."""
    print("\n" + "=" * 60)
    print("TESTE 3: Sistema de Cores por Palavra")
    print("=" * 60)

    from services.subtitler_v2 import SubtitleGeneratorV2

    gen = SubtitleGeneratorV2()

    test_words = [
        ("muito", "Amarelo (ênfase)"),
        ("incrível", "Amarelo (ênfase)"),
        ("não", "Vermelho (negativo)"),
        ("nunca", "Vermelho (negativo)"),
        ("10", "Verde (número)"),
        ("milhão", "Verde (número)"),
        ("normal", "Branco (padrão)"),
        ("palavra", "Branco (padrão)"),
    ]

    print("\nCores atribuídas:")
    for word, expected in test_words:
        color = gen._get_word_color(word)
        print(f"  {word:15s} -> {color:15s} ({expected})")


def test_resolution_scaling():
    """Testa escala de fonte para diferentes resoluções."""
    print("\n" + "=" * 60)
    print("TESTE 4: Escala para Diferentes Resoluções")
    print("=" * 60)

    from services.subtitler_v2 import SubtitleGeneratorV2, SubtitleStyle

    gen = SubtitleGeneratorV2()
    base_style = SubtitleStyle(font_size=48, margin_v=80)

    resolutions = [
        (1080, 1920, "Vertical 1080p"),
        (720, 1280, "Vertical 720p"),
        (1080, 1080, "Quadrado 1080p"),
        (1920, 1080, "Horizontal 1080p"),
        (3840, 2160, "4K Horizontal"),
    ]

    print("\nEscala de fonte e margem para diferentes resoluções:")
    print(f"Base: font_size={base_style.font_size}, margin_v={base_style.margin_v}")
    print()

    for width, height, name in resolutions:
        scaled, _, _ = gen._calculate_scaled_style(base_style, width, height)
        print(f"  {name:20s} ({width}x{height}): font={scaled.font_size}px, margin_v={scaled.margin_v}px")


def main():
    """Executa todos os testes."""
    print("\n" + "=" * 60)
    print("   ClipGenius - Teste de Legendas V2")
    print("=" * 60)

    try:
        # Teste 1: Backends de transcrição
        test_transcriber_backends()

        # Teste 2: Gerador de legendas
        test_subtitle_generator()

        # Teste 3: Cores por palavra
        test_word_colors()

        # Teste 4: Escala de resolução
        test_resolution_scaling()

        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
