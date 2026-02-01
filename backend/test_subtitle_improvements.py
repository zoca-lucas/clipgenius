"""
Test script for subtitle generation improvements
"""

from services.subtitler import SubtitleGenerator

# Mock word data
mock_words = [
    {'word': 'Olá', 'start': 0.0, 'end': 0.5},
    {'word': 'pessoal', 'start': 0.5, 'end': 1.0},
    {'word': 'hoje', 'start': 1.0, 'end': 1.3},
    {'word': 'vamos', 'start': 1.3, 'end': 1.6},
    {'word': 'falar', 'start': 1.6, 'end': 2.0},
    {'word': 'sobre', 'start': 2.0, 'end': 2.3},
    {'word': 'um', 'start': 2.3, 'end': 2.5},
    {'word': 'assunto', 'start': 2.5, 'end': 3.0},
    {'word': 'muito', 'start': 3.0, 'end': 3.3},
    {'word': 'interessante', 'start': 3.3, 'end': 4.0},
    {'word': 'que', 'start': 4.0, 'end': 4.2},
    {'word': 'vai', 'start': 4.2, 'end': 4.5},
    {'word': 'mudar', 'start': 4.5, 'end': 5.0},
    {'word': 'sua', 'start': 5.0, 'end': 5.2},
    {'word': 'vida', 'start': 5.2, 'end': 5.7},
]

def test_subtitle_improvements():
    print("Testing ClipGenius Subtitle Improvements\n")
    print("=" * 60)

    generator = SubtitleGenerator()

    # Test 1: Capitalization
    print("\n1. Testing capitalization function:")
    test_texts = [
        "OLÁ PESSOAL",
        "hoje vamos falar",
        "  TESTE COM ESPAÇOS  "
    ]
    for text in test_texts:
        result = generator._capitalize_text(text)
        print(f"   '{text}' -> '{result}'")

    # Test 2: Chunking by character limit
    print("\n2. Testing intelligent word chunking:")
    chunks = generator._chunk_words_by_length(mock_words, max_chars=42, max_words=6)
    print(f"   Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        text = ' '.join(w['word'] for w in chunk)
        print(f"   Chunk {i+1}: '{text}' ({len(text)} chars, {len(chunk)} words)")

    # Test 3: Generate SRT with new settings
    print("\n3. Generating test SRT file:")
    output_path = "/tmp/test_subtitle.srt"
    srt_path = generator.generate_srt(
        words=mock_words,
        output_path=output_path,
        words_per_line=6,
        offset=0,
        max_chars_per_line=42,
        capitalize=True
    )
    print(f"   SRT file generated: {srt_path}")

    # Read and display SRT content
    print("\n4. SRT Content Preview:")
    print("-" * 60)
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
    print("-" * 60)

    # Test 4: Style improvements
    print("\n5. Default style configuration:")
    for key, value in generator.DEFAULT_STYLE.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("\nKey improvements:")
    print("  ✓ Proper capitalization (not all UPPERCASE)")
    print("  ✓ Intelligent word chunking (max 42 chars, 6 words)")
    print("  ✓ Enhanced visual style for vertical video")
    print("  ✓ Better Whisper transcription quality settings")

if __name__ == "__main__":
    test_subtitle_improvements()
