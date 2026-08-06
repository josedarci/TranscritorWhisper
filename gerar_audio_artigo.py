#!/usr/bin/env python3
"""
Script utilitário para converter textos e artigos técnicos em arquivos de áudio MP3 (Text-to-Speech).
Uso no terminal:
    python gerar_audio_artigo.py "Seu texto aqui..."
    python gerar_audio_artigo.py --file artigo.txt --voice en-US-ChristopherNeural --output artigo.mp3
"""

import sys
import os
import argparse
from services.tts_generator import gerar_audio_tts, VOIZES_DISPONIVEIS

def main():
    parser = argparse.ArgumentParser(description="Gerador de Áudio MP3 para Artigos Técnicos (Edge Neural TTS)")
    parser.add_argument("text", nargs="?", help="Texto a ser convertido em áudio (opcional se --file for usado)")
    parser.add_argument("-f", "--file", help="Caminho para um arquivo .txt contendo o artigo")
    parser.add_argument("-v", "--voice", default="en-US-ChristopherNeural", help="Identificador da voz (padrão: en-US-ChristopherNeural)")
    parser.add_argument("-s", "--speed", default="+0%", help="Velocidade da voz (ex: +0%%, +10%%, -10%%)")
    parser.add_argument("-o", "--output", help="Caminho do arquivo de saída .mp3")

    args = parser.parse_args()

    texto_final = ""
    if args.file:
        if os.path.exists(args.file):
            with open(args.file, "r", encoding="utf-8") as f:
                texto_final = f.read()
        else:
            print(f"❌ Arquivo não encontrado: {args.file}")
            sys.exit(1)
    elif args.text:
        texto_final = args.text
    else:
        print("💡 Exemplo de uso:")
        print('  python gerar_audio_artigo.py "Vector Databases for RAG Architectures..."')
        print("  python gerar_audio_artigo.py --file artigo.txt -o artigo_audio.mp3\n")
        print("Vozes disponíveis:")
        for voz_id, rotulo in VOIZES_DISPONIVEIS.items():
            print(f"  • {voz_id}: {rotulo}")
        sys.exit(0)

    print(f"🎙️ Gerando áudio MP3 com voz '{args.voice}'...")
    path, msg = gerar_audio_tts(texto_final, voz_selecionada=args.voice, velocidade=args.speed, output_path=args.output)
    
    print(msg)
    if path:
        print(f"🎧 Arquivo salvo em: {path}")

if __name__ == "__main__":
    main()
