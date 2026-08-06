import os
import uuid
import asyncio
import logging
import edge_tts

# Dicionário de vozes suportadas com rótulos amigáveis
VOIZES_DISPONIVEIS = {
    "en-US-ChristopherNeural": "🇺🇸 Inglês (EUA) - Christopher (Masculino Profissional / Técnico)",
    "en-US-JennyNeural": "🇺🇸 Inglês (EUA) - Jenny (Feminino Profissional)",
    "en-US-GuyNeural": "🇺🇸 Inglês (EUA) - Guy (Masculino Narrador)",
    "en-US-AriaNeural": "🇺🇸 Inglês (EUA) - Aria (Feminino Expresso)",
    "en-GB-SoniaNeural": "🇬🇧 Inglês (UK) - Sonia (Feminino Britânico)",
    "en-GB-RyanNeural": "🇬🇧 Inglês (UK) - Ryan (Masculino Britânico)",
    "pt-BR-AntonioNeural": "🇧🇷 Português (BR) - Antonio (Masculino)",
    "pt-BR-FranciscaNeural": "🇧🇷 Português (BR) - Francisca (Feminino)",
}

# Mapeamento inverso do rótulo da UI para o identificador da voz
MAPA_ROTULO_PARA_VOZ = {rotulo: voz_id for voz_id, rotulo in VOIZES_DISPONIVEIS.items()}

async def _sintetizar_audio_async(texto: str, voz_id: str, rate_str: str, output_path: str):
    """Executa a síntese via edge-tts assincronamente."""
    communicate = edge_tts.Communicate(texto, voz_id, rate=rate_str)
    await communicate.save(output_path)

def gerar_audio_tts(texto: str, voz_selecionada: str = "en-US-ChristopherNeural", velocidade: str = "+0%", output_path: str = None) -> tuple[str, str]:
    """
    Gera um arquivo de áudio MP3 a partir do texto fornecido.
    
    :param texto: Texto a ser convertido em voz.
    :param voz_selecionada: ID da voz ou rótulo exibido no Gradio.
    :param velocidade: Taxa de velocidade (ex: "+0%", "+10%", "-10%").
    :param output_path: Caminho opcional do arquivo de saída.
    :return: Tupla (caminho_do_arquivo_mp3, mensagem_status)
    """
    if not texto or not texto.strip():
        return None, "⚠️ O texto fornecido está vazio. Insira um texto para gerar o áudio."

    # Resolver ID da voz se for passado o rótulo da UI
    voz_id = MAPA_ROTULO_PARA_VOZ.get(voz_selecionada, voz_selecionada)
    if voz_id not in VOIZES_DISPONIVEIS:
        voz_id = "en-US-ChristopherNeural"

    # Definir diretório e arquivo de saída
    if not output_path:
        uploads_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        nome_arquivo = f"artigo_audio_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(uploads_dir, nome_arquivo)

    # Formatar taxa de velocidade
    rate_str = velocidade if velocidade.startswith(("+", "-")) else f"+{velocidade}"
    if not rate_str.endswith("%"):
        rate_str += "%"

    try:
        logging.info(f"Iniciando síntese TTS de {len(texto)} caracteres com voz {voz_id} (rate: {rate_str})...")
        
        # Tratar execução de asyncio em ambientes com loop existente ou não
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Se o loop já estiver rodando (ex: Gradio async), cria task no loop existente
            future = asyncio.run_coroutine_threadsafe(
                _sintetizar_audio_async(texto, voz_id, rate_str, output_path),
                loop
            )
            future.result(timeout=120)
        else:
            # Caso contrário, roda um novo loop síncrono
            asyncio.run(_sintetizar_audio_async(texto, voz_id, rate_str, output_path))

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            tamanho_kb = round(os.path.getsize(output_path) / 1024, 1)
            msg = f"✅ Áudio gerado com sucesso!\n• Voz: {voz_id}\n• Tamanho: {tamanho_kb} KB\n• Arquivo: {os.path.basename(output_path)}"
            logging.info(msg)
            return output_path, msg
        else:
            return None, "❌ Falha ao gerar áudio: O arquivo final ficou vazio."

    except Exception as e:
        err_msg = f"❌ Erro ao gerar áudio TTS: {str(e)}"
        logging.error(err_msg, exc_info=True)
        return None, err_msg
