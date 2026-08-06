#!/usr/bin/env python3
"""
Script utilitário para converter textos e artigos técnicos em arquivos de áudio MP3 (Text-to-Speech).
Uso no terminal:
    python gerar_audio_artigo.py "Seu texto aqui..."
    python gerar_audio_artigo.py --file artigo.txt --voice en-US-ChristopherNeural --preset "Voz de Podcast" --output artigo.mp3
"""

import sys
import os
import argparse
from services.tts_generator import gerar_audio_tts, VOIZES_DISPONIVEIS
from services.audio_equalizer import PRESETS_EQUALIZADOR

def main():
    parser = argparse.ArgumentParser(description="Gerador de Áudio MP3 para Artigos Técnicos (Edge Neural TTS + Equalizador FFmpeg)")
    parser.add_argument("text", nargs="?", help="Texto a ser convertido em áudio (opcional se --file for usado)")
    parser.add_argument("-f", "--file", help="Caminho para um arquivo .txt contendo o artigo")
    parser.add_argument("-v", "--voice", default="en-US-ChristopherNeural", help="Identificador da voz (padrão: en-US-ChristopherNeural)")
    parser.add_argument("-s", "--speed", default="+0%", help="Velocidade da voz (ex: +0%%, +10%%, -10%%)")
    parser.add_argument("-p", "--preset", default="Nenhum (Áudio Original)", help="Preset do Equalizador (ex: 'Voz de Podcast', 'Vocal Booster', 'Bass Boost')")
    parser.add_argument("--low", type=float, default=0.0, help="Ganho manual de graves (-12 a +12 dB)")
    parser.add_argument("--mid", type=float, default=0.0, help="Ganho manual de médios (-12 a +12 dB)")
    parser.add_argument("--high", type=float, default=0.0, help="Ganho manual de agudos (-12 a +12 dB)")
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
        print('  python gerar_audio_artigo.py --file artigo.txt --preset "Voz de Podcast / Rádio (Studio Warmth)" -o artigo_audio.mp3\n')
        print("Vozes disponíveis:")
        for voz_id, rotulo in VOIZES_DISPONIVEIS.items():
            print(f"  • {voz_id}: {rotulo}")
        print("\nPresets de Equalização:")
        for p in PRESETS_EQUALIZADOR.keys():
            print(f"  • {p}")
        sys.exit(0)

    # Mapear busca parcial de preset se o usuário digitar nome curto
    preset_escolhido = args.preset
    for p in PRESETS_EQUALIZADOR.keys():
        if args.preset.lower() in p.lower():
            preset_escolhido = p
            break

    print(f"🎙️ Gerando áudio MP3 com voz '{args.voice}' e equalizador '{preset_escolhido}'...")
    path, msg = gerar_audio_tts(
        texto_final,
        voz_selecionada=args.voice,
        velocidade=args.speed,
        output_path=args.output,
        eq_preset=preset_escolhido,
        eq_gain_low=args.low,
        eq_gain_mid=args.mid,
        eq_gain_high=args.high
    )
    
    print(msg)
    if path:
        print(f"🎧 Arquivo salvo em: {path}")

if __name__ == "__main__":
    main()
