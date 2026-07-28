import os
import uuid
import shutil
import time
import requests
import traceback
import logging
import hashlib
import threading
import concurrent.futures
import whisper
import gradio as gr

# Lock para garantir thread safety nas chamadas concorrentes ao PyTorch/Whisper
whisper_lock = threading.Lock()

from services.ai_extractor import gerar_tags_e_categorias, extrair_entidades
from services.vector_store import vector_store_global
from services.exporter import exportar_txt, exportar_markdown, exportar_html

# Configurações de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("transcritor.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Configurações de diretórios e endpoints da API
UPLOADS_PUBLICAS = os.path.join(os.getcwd(), "uploads")
URL_BASE = "http://localhost:3001/uploads"
API_BACKEND = "http://localhost:3001/api/salvar-completo"
API_BASE = "http://localhost:3001/api"
OLLAMA_URL = "http://localhost:11434/api/generate"

os.makedirs(UPLOADS_PUBLICAS, exist_ok=True)

# Carrega modelo Whisper uma única vez
logging.info("Carregando modelo Whisper 'base'...")
model = whisper.load_model("base")
logging.info("Modelo Whisper carregado.")

def formatar_texto_paragrafos(texto):
    """Organiza blocos contínuos de texto do Whisper em parágrafos legíveis com quebras de linha duplas."""
    if not texto:
        return ""
    import re
    frases = [f.strip() for f in re.split(r'(?<=[.!?])\s+', texto) if f.strip()]
    if not frases:
        return texto
    
    paragrafos = []
    chunk = []
    for frase in frases:
        chunk.append(frase)
        if len(chunk) >= 4:
            paragrafos.append(" ".join(chunk))
            chunk = []
    if chunk:
        paragrafos.append(" ".join(chunk))
    
    return "\n\n".join(paragrafos)

def gerar_resumo_ollama(texto, modelo="llama3"):
    """Gera resumo via API local do Ollama em Português."""
    prompt = (
        "ATENÇÃO: Responda EXCLUSIVAMENTE em Português do Brasil.\n"
        "Não inclua introduções, conversas ou saudações em inglês (como 'Here is a summary').\n\n"
        "Você é um assistente especialista em sintetizar reuniões e áudios.\n"
        "Faça um resumo claro, conciso e estruturado em tópicos (bullet points) em português para o seguinte texto transcrito:\n\n"
        f"{texto}"
    )
    try:
        t_start = time.time()
        response = requests.post(OLLAMA_URL, json={
            "model": modelo,
            "prompt": prompt,
            "stream": False
        }, timeout=120)
        t_resumo = time.time() - t_start
        
        if response.status_code == 200:
            resumo = response.json().get("response", "Erro ao obter resposta do Ollama.").strip()
            return resumo, t_resumo
        else:
            return f"⚠️ Erro no Ollama (Status {response.status_code}): Verifique se o modelo '{modelo}' está baixado.", t_resumo
    except requests.exceptions.ConnectionError:
        return f"⚠️ Não foi possível conectar ao Ollama em {OLLAMA_URL}.\nCertifique-se de que o Ollama está rodando (`ollama run {modelo}`).", 0.0
    except Exception as e:
        return f"⚠️ Erro ao gerar resumo: {e}", 0.0

def processar_audio_item(audio_item, gerar_resumo=True, extrair_tags_entidades=True, modelo_ollama="llama3"):
    """Processamento de um único arquivo de áudio isolado com extração de metadados, tags e entidades."""
    t_inicio = time.time()
    info = {
        "nome_original": "",
        "status": "Aguardando",
        "transcricao": "",
        "resumo": "",
        "tags": {},
        "entidades": {},
        "tempo_transcricao": 0.0,
        "tempo_resumo": 0.0,
        "tempo_total": 0.0,
        "erro": None
    }

    try:
        if isinstance(audio_item, dict) and "name" in audio_item:
            filepath = audio_item["name"]
        elif hasattr(audio_item, "name"):
            filepath = audio_item.name
        else:
            filepath = str(audio_item)

        nome_original = os.path.basename(filepath)
        info["nome_original"] = nome_original
        info["status"] = "Processando (Copiando arquivo)"
        logging.info(f"[{nome_original}] Iniciando...")

        ext = os.path.splitext(filepath)[1] or ".mp3"
        nome_arquivo_unico = f"{uuid.uuid4().hex}{ext}"
        caminho_destino = os.path.join(UPLOADS_PUBLICAS, nome_arquivo_unico)
        shutil.copy(filepath, caminho_destino)

        # 1. Whisper Transcrição (protegida por Lock para thread safety no PyTorch)
        info["status"] = "Transcrevendo (Whisper)"
        t_trans_start = time.time()
        with whisper_lock:
            result = model.transcribe(caminho_destino, language="pt")
        info["tempo_transcricao"] = round(time.time() - t_trans_start, 2)
        texto_raw = result["text"].strip()
        texto = formatar_texto_paragrafos(texto_raw)
        info["transcricao"] = texto

        # 2. Resumo com IA
        if gerar_resumo:
            info["status"] = "Gerando resumo (Ollama)"
            resumo_txt, t_res = gerar_resumo_ollama(texto, modelo=modelo_ollama)
            info["resumo"] = resumo_txt
            info["tempo_resumo"] = round(t_res, 2)
        else:
            info["resumo"] = "ℹ️ Resumo desativado."

        # 3. Tags Automáticas e Extração de Entidades (Etapas 7 e 8)
        if extrair_tags_entidades and texto:
            info["status"] = "Extraindo Tags e Entidades (IA)"
            info["tags"] = gerar_tags_e_categorias(texto, modelo=modelo_ollama)
            info["entidades"] = extrair_entidades(texto, modelo=modelo_ollama)

        # 4. Adicionar ao Banco Vetorial / RAG (Etapa 10)
        vector_store_global.adicionar_transcricao(nome_original, texto, meta={"resumo": info["resumo"]})

        info["tempo_total"] = round(time.time() - t_inicio, 2)
        info["status"] = "Concluído"

        # 5. Salva na API Node (MySQL)
        url_publica = f"{URL_BASE}/{nome_arquivo_unico}"
        tamanho_bytes = os.path.getsize(caminho_destino) if os.path.exists(caminho_destino) else 0
        hash_sha256 = None
        try:
            with open(caminho_destino, "rb") as f:
                hash_sha256 = hashlib.sha256(f.read()).hexdigest()
        except Exception:
            pass

        try:
            requests.post(API_BACKEND, json={
                "nome_arquivo": nome_original,
                "url": url_publica,
                "caminho": caminho_destino,
                "tamanho_bytes": tamanho_bytes,
                "duracao_segundos": 0.0,
                "idioma": "pt",
                "modelo_whisper": "base",
                "modelo_llama": modelo_ollama,
                "tempo_transcricao": info["tempo_transcricao"],
                "tempo_resumo": info["tempo_resumo"],
                "tempo_total": info["tempo_total"],
                "status": "Concluído",
                "texto": texto,
                "resumo": info["resumo"],
                "hash_sha256": hash_sha256,
                "usuario": "sistema",
                "tags": info["tags"],
                "entidades": info["entidades"]
            }, timeout=10)
        except Exception as err_api:
            logging.warning(f"[{nome_original}] Falha ao notificar backend Node.js: {err_api}")

        logging.info(f"[{nome_original}] Finalizado em {info['tempo_total']}s.")

    except Exception as err:
        tb = traceback.format_exc()
        info["status"] = "Erro"
        info["erro"] = str(err)
        info["tempo_total"] = round(time.time() - t_inicio, 2)
        info["transcricao"] = f"❌ Erro ao processar áudio: {err}\n\nDetalhes:\n{tb}"
        info["resumo"] = "❌ Falha no processamento."

    return info

def transcrever_lote_paralelo(audio_files, gerar_resumo=True, extrair_tags=True, modelo_ollama="llama3", max_workers=3, progress=gr.Progress()):
    if not audio_files:
        return "Nenhum áudio enviado.", "Nenhum resumo gerado.", "Nenhum dado."

    if not isinstance(audio_files, list):
        audio_files = [audio_files]

    total_arquivos = len(audio_files)
    progress(0, desc=f"Iniciando {total_arquivos} arquivo(s) com {max_workers} worker(s)...")

    t_start = time.time()
    resultados = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=int(max_workers)) as executor:
        future_map = {
            executor.submit(processar_audio_item, item, gerar_resumo, extrair_tags, modelo_ollama): item
            for item in audio_files
        }
        concluidos = 0
        for future in concurrent.futures.as_completed(future_map):
            concluidos += 1
            res = future.result()
            resultados.append(res)
            progress(concluidos / total_arquivos, desc=f"Processados {concluidos}/{total_arquivos} - {res['nome_original']}")

    t_total = round(time.time() - t_start, 2)
    tempo_medio = round(t_total / total_arquivos, 2) if total_arquivos > 0 else 0.0
    sucessos = sum(1 for r in resultados if r["status"] == "Concluído")
    falhas = sum(1 for r in resultados if r["status"] == "Erro")

    transcricoes_lista = [f"📄 Arquivo: {r['nome_original']}\nStatus: {r['status']}\n\n{r['transcricao']}" for r in resultados]
    resumos_lista = [f"🤖 Arquivo: {r['nome_original']}\n\n{r['resumo']}" for r in resultados]
    
    detalhes_lista = [
        f"• {r['nome_original']} | Status: {r['status']} | Total: {r['tempo_total']}s (Whisper: {r['tempo_transcricao']}s | Ollama: {r['tempo_resumo']}s)"
        for r in resultados
    ]

    relatorio = (
        f"📊 RELATÓRIO DE EXECUÇÃO EM LOTE\n"
        f"----------------------------------------\n"
        f"• Total de Arquivos: {total_arquivos} | Sucessos: {sucessos} | Falhas: {falhas}\n"
        f"• Tempo Total: {t_total}s | Tempo Médio: {tempo_medio}s | Workers: {max_workers}\n\n"
        f"⏱️ Detalhes:\n" + "\n".join(detalhes_lista)
    )

    return (
        "\n\n========================================\n\n".join(transcricoes_lista),
        "\n\n========================================\n\n".join(resumos_lista),
        relatorio
    )

def carregar_dashboard_stats():
    """Busca estatísticas agregadas da API Node.js para a Aba de Dashboard (Etapa 4)."""
    try:
        res = requests.get(f"{API_BASE}/stats", timeout=5)
        if res.status_code == 200:
            st = res.json()
            return (
                f"### 📊 Estatísticas Gerais da Plataforma\n"
                f"- **Total de Áudios Transcritos**: `{st.get('total_audios', 0)}`\n"
                f"- **Horas Totais Transcritas**: `{st.get('total_horas', '0.00')} hrs`\n"
                f"- **Total de Palavras Processadas**: `{st.get('total_palavras', 0):,}`\n"
                f"- **Tempo Médio por Áudio**: `{st.get('tempo_medio_processamento', '0.00')}s`\n"
                f"- **Total de Usuários Ativos**: `{st.get('total_usuarios', 1)}`"
            )
    except Exception as e:
        return f"⚠️ Não foi possível carregar métricas da API Node.js: {e}"
    return "Métricas indisponíveis."

def realizar_pesquisa(termo_busca):
    """Busca avançada de transcrições e busca semântica (Etapa 5 e 10)."""
    if not termo_busca:
        return "Informe um termo de busca."

    resultados_formatados = []
    # 1. Busca semântica vetorial
    docs_semanticos = vector_store_global.buscar_semantica(termo_busca, top_k=3)
    if docs_semanticos:
        resultados_formatados.append("🧠 RESULTADOS DA BUSCA SEMÂNTICA (RAG):\n" + "-"*40)
        for doc in docs_semanticos:
            resultados_formatados.append(f"📌 [{doc['nome_arquivo']}] Chunk {doc['chunk_index']}:\n\"{doc['texto']}\"")

    # 2. Busca no MySQL via API Node.js
    try:
        res = requests.get(f"{API_BASE}/transcricoes", params={"q": termo_busca, "limit": 5}, timeout=5)
        if res.status_code == 200:
            dados = res.json().get("dados", [])
            if dados:
                resultados_formatados.append("\n🗄️ RESULTADOS DO BANCO DE DADOS (MySQL):\n" + "-"*40)
                for item in dados:
                    resultados_formatados.append(
                        f"📄 {item['nome_arquivo']} | Data: {item.get('data_upload', 'N/A')}\n"
                        f"Resumo: {item.get('resumo', 'Sem resumo')[:200]}...\n"
                    )
    except Exception as e:
        logging.warning(f"Erro ao consultar API para pesquisa: {e}")

    return "\n\n".join(resultados_formatados) if resultados_formatados else "Nenhum resultado encontrado."

def responder_chat_rag(nome_arquivo, pergunta_chat):
    """Responde dúvidas usando estritamente o conteúdo da transcrição selecionada (Etapa 9)."""
    if not nome_arquivo or not pergunta_chat:
        return "Selecione um arquivo e digite uma pergunta."
    return vector_store_global.chat_com_transcricao(nome_arquivo, pergunta_chat)

def gerar_exportacao(nome_arquivo, tipo_formato):
    """Exporta o relatório nos formatos TXT, Markdown ou HTML (Etapa 6)."""
    try:
        res = requests.get(f"{API_BASE}/transcricoes", params={"q": nome_arquivo, "limit": 1}, timeout=5)
        if res.status_code == 200:
            dados = res.json().get("dados", [])
            if dados:
                item = dados[0]
                texto = item.get("texto", "")
                resumo = item.get("resumo", "")
                if tipo_formato == "TXT":
                    return exportar_txt(nome_arquivo, texto, resumo, item)
                elif tipo_formato == "Markdown":
                    return exportar_markdown(nome_arquivo, texto, resumo, item)
                elif tipo_formato == "HTML":
                    return exportar_html(nome_arquivo, texto, resumo, item)
    except Exception as e:
        return f"Erro ao gerar exportação: {e}"
    return "Transcrição não localizada para exportação."

# Interface Gradio Profissional (Fases 1 a 4)
with gr.Blocks(title="🎙️ Transcritor Inteligente v2.0 Enterprise", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎙️ Transcritor Inteligente v2.0 Enterprise")
    gr.Markdown("Plataforma Completa de Processamento em Lote, Análise Semântica, RAG e Gestão de Áudios.")

    with gr.Tabs():
        # ABA 1: Transcrição em Lote
        with gr.TabItem("🎙️ Transcrição em Lote"):
            with gr.Row():
                with gr.Column(scale=1):
                    files_input = gr.File(file_count="multiple", type="filepath", label="Envie seus arquivos de áudio (.mp3, .wav, .m4a)")
                    with gr.Accordion("⚙️ Configurações de IA e Paralelismo", open=True):
                        check_resumo = gr.Checkbox(value=True, label="Gerar Resumo Inteligente (Ollama)")
                        check_tags = gr.Checkbox(value=True, label="Extrair Tags e Entidades Automáticas")
                        input_modelo = gr.Textbox(value="llama3", label="Modelo do Ollama (ex: llama3, qwen2.5)")
                        slider_workers = gr.Slider(minimum=1, maximum=8, value=3, step=1, label="Workers Simultâneos")

                    btn_submit = gr.Button("🚀 Processar Lote de Áudios", variant="primary", size="lg")

                with gr.Column(scale=2):
                    out_relatorio = gr.Textbox(label="📊 Relatório de Estatísticas e Tempos", lines=5)
                    out_transcricoes = gr.Textbox(label="📄 Transcrições Íntegras (Whisper)", lines=10)
                    out_resumos = gr.Textbox(label="🤖 Resumos & Análises (Ollama)", lines=10)

            btn_submit.click(
                fn=transcrever_lote_paralelo,
                inputs=[files_input, check_resumo, check_tags, input_modelo, slider_workers],
                outputs=[out_transcricoes, out_resumos, out_relatorio]
            )

        # ABA 2: Pesquisa Semântica & Histórico
        with gr.TabItem("🔍 Pesquisa & Histórico"):
            gr.Markdown("### 🔍 Pesquisa Semântica & Consulta de Registros")
            input_busca = gr.Textbox(label="Digite o termo ou conceito a pesquisar (ex: 'data lake', 'orçamento', 'Azure')", placeholder="Ex: reuniões sobre custos...")
            btn_busca = gr.Button("🔍 Pesquisar", variant="secondary")
            out_busca = gr.Textbox(label="ResultadosEncontrados", lines=14)

            btn_busca.click(fn=realizar_pesquisa, inputs=[input_busca], outputs=[out_busca])

        # ABA 3: Dashboard de Métricas
        with gr.TabItem("📊 Dashboard & Estatísticas"):
            gr.Markdown("### 📊 Indicadores Globais de Uso da Plataforma")
            btn_refresh_dash = gr.Button("🔄 Atualizar Métricas")
            out_dash = gr.Markdown(value="Clique em 'Atualizar Métricas' para carregar as estatísticas.")

            btn_refresh_dash.click(fn=carregar_dashboard_stats, inputs=[], outputs=[out_dash])

        # ABA 4: Chat Inteligente com Transcrição (RAG)
        with gr.TabItem("💬 Chat RAG com Áudio"):
            gr.Markdown("### 💬 Tire Dúvidas sobre uma Transcrição Específica")
            input_nome_chat = gr.Textbox(label="Nome exato do arquivo (ex: '250704_001.mp3')", placeholder="Nome do arquivo...")
            input_pergunta_chat = gr.Textbox(label="Sua pergunta sobre o conteúdo deste áudio")
            btn_chat = gr.Button("🤖 Perguntar à IA", variant="primary")
            out_resposta_chat = gr.Textbox(label="Resposta da IA (baseada apenas na transcrição)", lines=8)

            btn_chat.click(fn=responder_chat_rag, inputs=[input_nome_chat, input_pergunta_chat], outputs=[out_resposta_chat])

        # ABA 5: Exportação de Relatórios
        with gr.TabItem("📥 Exportar Relatório"):
            gr.Markdown("### 📥 Exportação de Documentos de Transcrição")
            input_nome_exp = gr.Textbox(label="Nome do Arquivo", placeholder="Ex: 250704_001.mp3")
            radio_formato = gr.Radio(choices=["TXT", "Markdown", "HTML"], value="Markdown", label="Formato de Saída")
            btn_export = gr.Button("📄 Gerar Documento Exportado")
            out_export = gr.Textbox(label="Conteúdo Formatado do Documento", lines=15)

            btn_export.click(fn=gerar_exportacao, inputs=[input_nome_exp, radio_formato], outputs=[out_export])

demo.launch()
