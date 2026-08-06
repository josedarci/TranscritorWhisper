import os
import shutil
import subprocess
import logging

PRESETS_EQUALIZADOR = {
    "Nenhum (Áudio Original)": None,
    "📻 Voz de Podcast / Rádio (Studio Warmth)": "highpass=f=70,equalizer=f=120:width_type=h:width=60:g=4,equalizer=f=3200:width_type=h:width=800:g=3",
    "🎙️ Vocal Booster (Clareza Vocal)": "highpass=f=80,equalizer=f=1000:width_type=h:width=400:g=3,equalizer=f=3500:width_type=h:width=1000:g=4",
    "🔊 Bass Boost (Graves Profundos)": "equalizer=f=100:width_type=h:width=60:g=6",
    "🤫 Soft & Mellow (Agudos Suaves)": "equalizer=f=7000:width_type=h:width=2000:g=-5,equalizer=f=10000:width_type=h:width=3000:g=-6"
}

def aplicar_equalizador(
    input_path: str,
    output_path: str = None,
    preset: str = "Nenhum (Áudio Original)",
    gain_low: float = 0.0,
    gain_mid: float = 0.0,
    gain_high: float = 0.0
) -> str:
    """
    Aplica equalizador de áudio e filtros no arquivo de áudio utilizando o FFmpeg.
    
    :param input_path: Caminho do arquivo de áudio de entrada.
    :param output_path: Caminho opcional do arquivo processado.
    :param preset: Nome do preset escolhido.
    :param gain_low: Ganho manual de graves em dB (-12 a +12).
    :param gain_mid: Ganho manual de médios em dB (-12 a +12).
    :param gain_high: Ganho manual de agudos em dB (-12 a +12).
    :return: Caminho do arquivo de áudio equalizado.
    """
    if not os.path.exists(input_path):
        logging.error(f"Arquivo de entrada não encontrado: {input_path}")
        return input_path

    filtros = []

    # 1. Aplicar filtro do preset se selecionado
    filtro_preset = PRESETS_EQUALIZADOR.get(preset)
    if filtro_preset:
        filtros.append(filtro_preset)

    # 2. Aplicar equalizador manual de 3 bandas se houver ajuste diferente de zero
    manual_filters = []
    if gain_low != 0.0:
        manual_filters.append(f"equalizer=f=100:width_type=h:width=100:g={gain_low}")
    if gain_mid != 0.0:
        manual_filters.append(f"equalizer=f=1000:width_type=h:width=500:g={gain_mid}")
    if gain_high != 0.0:
        manual_filters.append(f"equalizer=f=6000:width_type=h:width=2000:g={gain_high}")

    if manual_filters:
        filtros.append(",".join(manual_filters))

    # Se nenhum filtro for especificado, retorna o arquivo original
    if not filtros:
        return input_path

    # Definir caminho de saída
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_eq{ext}"

    temp_output = f"{output_path}.tmp{os.path.splitext(input_path)[1]}"
    cruzamento_filtros = ",".join(filtros)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af", cruzamento_filtros,
        "-b:a", "192k",
        temp_output
    ]

    try:
        logging.info(f"Executando FFmpeg EQ filter: {cruzamento_filtros}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        if os.path.exists(temp_output) and os.path.getsize(temp_output) > 0:
            shutil.move(temp_output, output_path)
            logging.info(f"Equalização aplicada com sucesso -> {output_path}")
            return output_path
        else:
            logging.warning("FFmpeg gerou um arquivo vazio. Mantendo arquivo original.")
            return input_path
            
    except Exception as err:
        logging.error(f"Erro ao aplicar equalizador com FFmpeg: {err}")
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except Exception:
                pass
        return input_path
