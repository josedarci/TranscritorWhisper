import os
import uuid
import asyncio
import logging
import hashlib
import requests
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
    "zh-CN-XiaoxiaoNeural": "🇨🇳 Chinês (Mandarim) - Xiaoxiao (Feminino Neural)",
    "zh-CN-YunxiNeural": "🇨🇳 Chinês (Mandarim) - Yunxi (Masculino Neural)",
    "zh-CN-YunjianNeural": "🇨🇳 Chinês (Mandarim) - Yunjian (Masculino Narrador)",
}

# Mapeamento inverso do rótulo da UI para o identificador da voz
MAPA_ROTULO_PARA_VOZ = {rotulo: voz_id for voz_id, rotulo in VOIZES_DISPONIVEIS.items()}

async def _sintetizar_audio_async(texto: str, voz_id: str, rate_str: str, output_path: str):
    """Executa a síntese via edge-tts assincronamente."""
    communicate = edge_tts.Communicate(texto, voz_id, rate=rate_str)
    await communicate.save(output_path)

def salvar_artigo_no_banco_e_vectorstore(nome_arquivo: str, output_path: str, texto: str, voz_id: str):
    """Persiste o artigo fonte e o áudio gerado no MySQL e no VectorStore/RAG."""
    # 1. Adicionar ao VectorStore para busca semântica e Chat RAG
    try:
        from services.vector_store import vector_store_global
        resumo_tts = f"🔊 Artigo Técnico sintetizado via TTS com voz neural ({voz_id})."
        vector_store_global.adicionar_transcricao(nome_arquivo, texto, meta={"resumo": resumo_tts})
        logging.info(f"[{nome_arquivo}] Texto do artigo indexado com sucesso no VectorStore/RAG.")
    except Exception as err_vs:
        logging.warning(f"[{nome_arquivo}] Erro ao indexar no VectorStore: {err_vs}")

    # 2. Persistir no MySQL através da API REST Backend
    api_backend = "http://localhost:3001/api/salvar-completo"
    url_base = "http://localhost:3001/uploads"
    
    tamanho_bytes = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    url_publica = f"{url_base}/{nome_arquivo}"
    
    hash_sha256 = None
    try:
        with open(output_path, "rb") as f:
            hash_sha256 = hashlib.sha256(f.read()).hexdigest()
    except Exception:
        pass

    try:
        resp = requests.post(api_backend, json={
            "nome_arquivo": nome_arquivo,
            "url": url_publica,
            "caminho": output_path,
            "tamanho_bytes": tamanho_bytes,
            "duracao_segundos": 0.0,
            "idioma": "zh" if "zh-" in voz_id else ("en" if "en-" in voz_id else "pt"),
            "modelo_whisper": f"Edge-TTS ({voz_id})",
            "modelo_llama": "N/A",
            "tempo_transcricao": 0.0,
            "tempo_resumo": 0.0,
            "tempo_total": 0.0,
            "status": "Concluído",
            "texto": texto,
            "resumo": f"📄 Artigo Técnico gravado em áudio MP3 (Voz: {voz_id}).",
            "hash_sha256": hash_sha256,
            "usuario": "sistema",
            "tags": ["TTS", "Artigo Técnico", "Edge-TTS"],
            "entidades": []
        }, timeout=5)
        if resp.status_code in (200, 201):
            logging.info(f"[{nome_arquivo}] Artigo e áudio persistidos no MySQL com sucesso.")
            return True
        else:
            logging.warning(f"[{nome_arquivo}] Backend respondeu com status {resp.status_code}")
    except Exception as err_api:
        logging.warning(f"[{nome_arquivo}] Backend Node.js não disponível no momento (banco local ou offline): {err_api}")
    
    return False

from services.audio_equalizer import aplicar_equalizador, PRESETS_EQUALIZADOR

def gerar_audio_tts(
    texto: str,
    voz_selecionada: str = "en-US-ChristopherNeural",
    velocidade: str = "+0%",
    output_path: str = None,
    salvar_banco: bool = True,
    eq_preset: str = "Nenhum (Áudio Original)",
    eq_gain_low: float = 0.0,
    eq_gain_mid: float = 0.0,
    eq_gain_high: float = 0.0
) -> tuple[str, str]:
    """
    Gera um arquivo de áudio MP3 a partir do texto fornecido, aplica equalização (se configurado) e salva no banco de dados.
    
    :param texto: Texto a ser convertido em voz.
    :param voz_selecionada: ID da voz ou rótulo exibido no Gradio.
    :param velocidade: Taxa de velocidade (ex: "+0%", "+10%", "-10%").
    :param output_path: Caminho opcional do arquivo de saída.
    :param salvar_banco: Se True, registra o texto e o áudio no MySQL e VectorStore.
    :param eq_preset: Preset de equalizador a ser aplicado.
    :param eq_gain_low: Ganho manual de graves em dB (-12 a +12).
    :param eq_gain_mid: Ganho manual de médios em dB (-12 a +12).
    :param eq_gain_high: Ganho manual de agudos em dB (-12 a +12).
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
    else:
        nome_arquivo = os.path.basename(output_path)

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
            future = asyncio.run_coroutine_threadsafe(
                _sintetizar_audio_async(texto, voz_id, rate_str, output_path),
                loop
            )
            future.result(timeout=120)
        else:
            asyncio.run(_sintetizar_audio_async(texto, voz_id, rate_str, output_path))

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            # Aplicar equalizador se preset for diferente do original ou houver ganho manual
            eq_aplicado = False
            if eq_preset != "Nenhum (Áudio Original)" or eq_gain_low != 0.0 or eq_gain_mid != 0.0 or eq_gain_high != 0.0:
                output_path = aplicar_equalizador(
                    output_path,
                    output_path,
                    preset=eq_preset,
                    gain_low=eq_gain_low,
                    gain_mid=eq_gain_mid,
                    gain_high=eq_gain_high
                )
                eq_aplicado = True

            tamanho_kb = round(os.path.getsize(output_path) / 1024, 1)
            
            banco_msg = ""
            if salvar_banco:
                salvo = salvar_artigo_no_banco_e_vectorstore(nome_arquivo, output_path, texto, voz_id)
                if salvo:
                    banco_msg = "\n• Banco de Dados: ✅ Artigo e Áudio salvos no MySQL e Acervo/RAG!"
                else:
                    banco_msg = "\n• Banco de Dados: ℹ️ Indexado no VectorStore/RAG (Backend MySQL off)."

            eq_status = f"\n• Equalizador: 🎛️ Preset '{eq_preset}' aplicado" if eq_aplicado else "\n• Equalizador: Nenhum (Original)"

            msg = (
                f"✅ Áudio gerado com sucesso!\n"
                f"• Voz: {voz_id}\n"
                f"• Tamanho: {tamanho_kb} KB\n"
                f"• Arquivo: {nome_arquivo}"
                f"{eq_status}"
                f"{banco_msg}"
            )
            logging.info(msg)
            return output_path, msg
        else:
            return None, "❌ Falha ao gerar áudio: O arquivo final ficou vazio."

    except Exception as e:
        err_msg = f"❌ Erro ao gerar áudio TTS: {str(e)}"
        logging.error(err_msg, exc_info=True)
        return None, err_msg

