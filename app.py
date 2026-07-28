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
import pandas as pd
import gradio as gr

# Lock para garantir thread safety nas chamadas concorrentes ao PyTorch/Whisper
whisper_lock = threading.Lock()

from services.ai_extractor import gerar_tags_e_categorias, extrair_entidades
from services.vector_store import vector_store_global
from services.exporter import exportar_txt, exportar_markdown, exportar_html, exportar_pdf_ata_operacional, formatar_data_br
from pipeline.audio_processor import calcular_hash_sha256, aplicar_diarization_simulada
from pipeline.llm_enricher import enriquecer_transcricao_completa

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
        texto_paragrafos = formatar_texto_paragrafos(texto_raw)
        texto = aplicar_diarization_simulada(texto_paragrafos)
        info["transcricao"] = texto

        # 2. Resumo e Enriquecimento com IA (Agente 4 e 5)
        if gerar_resumo:
            info["status"] = "Gerando resumo e análise de IA (Ollama)"
            resumo_txt, t_res = gerar_resumo_ollama(texto, modelo=modelo_ollama)
            enriquecimento = enriquecer_transcricao_completa(texto, modelo=modelo_ollama)
            info["resumo"] = resumo_txt + f"\n\n#### 🎯 Sentimento Geral: **{enriquecimento.get('sentimento', 'Neutro')}**"
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
            total_audios = st.get('total_audios', 0)
            total_horas = st.get('total_horas', '0.00')
            
            try:
                total_palavras = int(st.get('total_palavras', 0) or 0)
            except Exception:
                total_palavras = 0
                
            tempo_medio = st.get('tempo_medio_processamento', '0.00')
            total_usuarios = st.get('total_usuarios', 1)

            return f"""### 📊 Dashboard & Indicadores Globais da Plataforma

| 📈 Métrica | 🔢 Valor Acumulado |
| :--- | :--- |
| **Total de Áudios Transcritos** | `{total_audios}` áudios |
| **Horas Totais Transcritas** | `{total_horas}` horas |
| **Total de Palavras Processadas** | `{total_palavras:,}` palavras |
| **Tempo Médio por Áudio** | `{tempo_medio}` segundos |
| **Usuários Ativos no Sistema** | `{total_usuarios}` usuário |
"""
    except Exception as e:
        logging.error(f"Erro ao carregar dashboard: {e}")
        return f"⚠️ Não foi possível carregar métricas da API Node.js: {e}"
    return "Métricas indisponíveis."

def destacar_termo_texto(texto, termo):
    """Destaca todas as ocorrências insensíveis a maiúsculas/minúsculas do termo pesquisado no texto usando a tag HTML <mark>."""
    if not texto or not termo or not str(termo).strip():
        return texto
    
    termo_limpo = str(termo).strip()
    if len(termo_limpo) < 2:
        return texto

    import re
    pattern = re.compile(re.escape(termo_limpo), re.IGNORECASE)
    def replacer(match):
        w = match.group(0)
        return f'<mark style="background-color: #fef08a; color: #854d0e; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{w}</mark>'

    return pattern.sub(replacer, texto)

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
            snippet = destacar_termo_texto(doc['texto'], termo_busca)
            resultados_formatados.append(f"📌 [{doc['nome_arquivo']}] Chunk {doc['chunk_index']}:\n\"{snippet}\"")

    # 2. Busca no MySQL via API Node.js
    try:
        res = requests.get(f"{API_BASE}/transcricoes", params={"q": termo_busca, "limit": 5}, timeout=5)
        if res.status_code == 200:
            dados = res.json().get("dados", [])
            if dados:
                resultados_formatados.append("\n🗄️ RESULTADOS DO BANCO DE DADOS (MySQL):\n" + "-"*40)
                for item in dados:
                    dt = formatar_data_br(item.get('data_upload'))
                    resumo_destacado = destacar_termo_texto(item.get('resumo', 'Sem resumo')[:300], termo_busca)
                    resultados_formatados.append(
                        f"📄 {item['nome_arquivo']} | Data: {dt}\n"
                        f"Resumo: {resumo_destacado}...\n"
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
    """Exporta o relatório nos formatos TXT, Markdown, HTML ou PDF Ata Operacional (Etapa 6 + Ata PDF)."""
    nome_limpo = str(nome_arquivo).strip().replace("\n", "").replace("\r", "")
    if not nome_limpo:
        return "Informe o nome do arquivo para exportação.", None

    try:
        res = requests.get(f"{API_BASE}/transcricoes", params={"q": nome_limpo, "limit": 1}, timeout=5)
        if res.status_code == 200:
            dados = res.json().get("dados", [])
            if dados:
                item = dados[0]
                texto = item.get("texto", "")
                resumo = item.get("resumo", "")
                if tipo_formato == "TXT":
                    return exportar_txt(nome_limpo, texto, resumo, item), None
                elif tipo_formato == "Markdown":
                    return exportar_markdown(nome_limpo, texto, resumo, item), None
                elif tipo_formato == "HTML":
                    return exportar_html(nome_limpo, texto, resumo, item), None
                elif tipo_formato == "PDF (Ata Operacional)":
                    caminho_pdf = exportar_pdf_ata_operacional(nome_limpo, texto, resumo, item)
                    msg = (
                        f"📝 ATA FORMAL DE REUNIÃO OPERACIONAL GERADA COM SUCESSO!\n\n"
                        f"• Documento PDF criado em: {caminho_pdf}\n"
                        f"• O arquivo está pronto para impressão, visto e assinatura formal no campo abaixo."
                    )
                    return msg, caminho_pdf
    except Exception as e:
        return f"Erro ao gerar exportação: {e}", None
    return f"Transcrição para '{nome_limpo}' não foi localizada no banco de dados.", None

def melhorar_audio_ffmpeg(caminho_entrada):
    """
    Aplica filtros avançados de áudio via FFmpeg para clareza vocal máxima:
    - Bandpass filter (80Hz - 8000Hz): elimina zumbidos de fundo graves e chiados agudos
    - Normalização EBU R128 (loudnorm): equilibra vozes baixas e altas
    - Reamostragem Mono 16kHz: padrão de máxima precisão do Whisper
    """
    if not caminho_entrada or not os.path.exists(caminho_entrada):
        return caminho_entrada

    base, ext = os.path.splitext(caminho_entrada)
    caminho_saida = f"{base}_enhanced.mp3"

    cmd = [
        "ffmpeg", "-y",
        "-i", caminho_entrada,
        "-af", "highpass=f=80,lowpass=f=8000,loudnorm=I=-16:LRA=11:TP=-1.5",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        caminho_saida
    ]

    try:
        import subprocess
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and os.path.exists(caminho_saida):
            logging.info(f"✨ Áudio aprimorado via FFmpeg: {caminho_saida}")
            return caminho_saida
    except Exception as e:
        logging.warning(f"Falha ao processar áudio com FFmpeg: {e}")

    return caminho_entrada

def acao_melhorar_audio_selecionado(id_ou_nome, termo_destaque=""):
    """Aplica o tratamento de áudio via FFmpeg no registro selecionado e recarrega o player."""
    if not id_ou_nome:
        return "Selecione um arquivo da grid primeiro.", None
    
    md, caminho_audio = abrir_modal_detalhes(id_ou_nome, termo_destaque)
    if caminho_audio and os.path.exists(caminho_audio):
        audio_tratado = melhorar_audio_ffmpeg(caminho_audio)
        msg_md = md + "\n\n> [!TIP]\n> ✨ **Áudio Tratado com Sucesso!** Aplicação de Filtro Passa-Banda Vocal (80Hz-8000Hz) e Normalização EBU R128."
        return msg_md, audio_tratado
    return md, caminho_audio

def obter_caminho_audio_local(item):
    """Localiza o arquivo de áudio físico no servidor correspondente à transcrição."""
    if not item:
        return None
        
    caminho = item.get("caminho") or item.get("url") or ""
    nome = item.get("nome_arquivo") or ""

    candidatos = [
        caminho.lstrip("/"),
        os.path.join("uploads", os.path.basename(caminho.lstrip("/"))),
        os.path.join("uploads", nome),
        os.path.join("transcritor-whisper/backend/uploads", os.path.basename(caminho.lstrip("/"))),
        os.path.join("transcritor-whisper/backend/uploads", nome)
    ]

    for cand in candidatos:
        if cand and os.path.exists(cand) and os.path.isfile(cand):
            return os.path.abspath(cand)

    return None

def carregar_acervo_grid(filtro=""):
    """Carrega todos os registros do MySQL formatados como DataFrame para a Grid do Acervo."""
    cols = ["ID", "Nome do Arquivo", "Data Upload", "Duração", "Palavras", "Status", "Player / Mídia", "Transcrição Disponível?"]
    try:
        params = {"limit": 100}
        if filtro and str(filtro).strip():
            params["q"] = str(filtro).strip()
        res = requests.get(f"{API_BASE}/transcricoes", params=params, timeout=5)
        if res.status_code == 200:
            dados = res.json().get("dados", [])
            grid_data = []
            for item in dados:
                duracao = f"{round(item.get('duracao_segundos', 0)/60, 1)} min" if item.get('duracao_segundos') else "N/A"
                palavras = item.get("quantidade_palavras", 0)
                tem_transcricao = "✅ Sim" if item.get("texto") and len(item["texto"]) > 10 else "❌ Não"
                data_up = formatar_data_br(item.get("data_upload"))
                grid_data.append({
                    "ID": item.get("id"),
                    "Nome do Arquivo": item.get("nome_arquivo"),
                    "Data Upload": data_up,
                    "Duração": duracao,
                    "Palavras": f"{palavras:,}",
                    "Status": item.get("status", "Concluído"),
                    "Player / Mídia": "🔊 Tocador (Clique p/ Ouvir)",
                    "Transcrição Disponível?": tem_transcricao
                })
            if grid_data:
                return pd.DataFrame(grid_data)
    except Exception as e:
        logging.error(f"Erro ao carregar acervo: {e}")
    return pd.DataFrame(columns=cols)

def abrir_modal_detalhes(id_ou_nome, termo_destaque=""):
    """Exibe os detalhes formatados da transcrição com destaque de termos e retorna o caminho do áudio para o Player."""
    if not id_ou_nome:
        return "Selecione ou digite o ID/nome do arquivo para visualizar.", None
    
    termo = str(id_ou_nome).strip().replace("\n", "").replace("\r", "")
    try:
        item = None
        if termo.isdigit():
            res = requests.get(f"{API_BASE}/transcricoes/{termo}", timeout=5)
            if res.status_code == 200:
                item = res.json()
        
        if not item:
            res = requests.get(f"{API_BASE}/transcricoes", params={"q": termo, "limit": 1}, timeout=5)
            dados = res.json().get("dados", []) if res.status_code == 200 else []
            item = dados[0] if dados else None

        if not item:
            return f"⚠️ Transcrição '{termo}' não encontrada no banco de dados.", None

        caminho_audio = obter_caminho_audio_local(item)
        texto_formatado = formatar_texto_paragrafos(item.get("texto", ""))
        resumo_formatado = item.get("resumo", "Sem resumo gerado.")

        # Destaque de palavra-chave pesquisada se houver
        banner_destaque = ""
        if termo_destaque and str(termo_destaque).strip():
            termo_clean = str(termo_destaque).strip()
            texto_formatado = destacar_termo_texto(texto_formatado, termo_clean)
            resumo_formatado = destacar_termo_texto(resumo_formatado, termo_clean)
            banner_destaque = f"\n> 🔍 **Termo Pesquisado Destacado no Texto**: <mark style=\"background-color: #fef08a; color: #854d0e; padding: 2px 6px; border-radius: 4px; font-weight: bold;\">{termo_clean}</mark>\n"

        entidades_json = item.get("entidades", {})
        if isinstance(entidades_json, str):
            try: entidades_json = json.loads(entidades_json)
            except: entidades_json = {}
        
        entidades_md = ""
        if entidades_json and isinstance(entidades_json, dict):
            entidades_md += "\n#### 🏷️ Entidades Identificadas (NER):\n"
            if entidades_json.get("pessoas"): entidades_md += f"- 👤 **Pessoas**: {', '.join(entidades_json['pessoas'])}\n"
            if entidades_json.get("empresas"): entidades_md += f"- 🏢 **Empresas**: {', '.join(entidades_json['empresas'])}\n"
            if entidades_json.get("datas"): entidades_md += f"- 📅 **Datas/Prazos**: {', '.join(entidades_json['datas'])}\n"
            if entidades_json.get("valores"): entidades_md += f"- 💰 **Valores**: {', '.join(entidades_json['valores'])}\n"

        data_formatada = formatar_data_br(item.get('data_upload'))

        md = f"""## 📄 Inspeção da Transcrição: `{item.get('nome_arquivo')}`
{banner_destaque}
### 📋 Metadados do Arquivo
- **ID no Banco**: `{item.get('id')}`
- **Data de Registro**: `{data_formatada}`
- **Duração Total**: `{round(item.get('duracao_segundos', 0)/60, 1)} minutos` (`{item.get('duracao_segundos', 0)}s`)
- **Volume de Palavras**: `{item.get('quantidade_palavras', 0):,}` palavras (`{item.get('quantidade_caracteres', 0):,}` caracteres)
- **Hash de Integridade (SHA-256)**: `{item.get('hash_sha256', 'N/A')}`
{entidades_md}
---

### 🤖 Síntese Executiva (Ollama - Llama 3)
{resumo_formatado}

---

### 📄 Transcrição Íntegra Formatada
{texto_formatado}
"""
        return md, caminho_audio
    except Exception as e:
        return f"⚠️ Erro ao carregar detalhes: {e}", None

def excluir_registro_acervo(id_ou_nome):
    """Exclui um registro do MySQL."""
    if not id_ou_nome:
        return "Informe o ID para exclusão.", carregar_acervo_grid()
    termo = str(id_ou_nome).strip()
    try:
        res = requests.delete(f"{API_BASE}/transcricoes/{termo}", timeout=5)
        if res.status_code == 200:
            msg = f"✅ Registro ID #{termo} excluído com sucesso!"
            return msg, carregar_acervo_grid()
    except Exception as e:
        return f"Erro ao excluir: {e}", carregar_acervo_grid()
    return f"Não foi possível excluir o registro #{termo}.", carregar_acervo_grid()

def obter_lista_choices_acervo():
    """Gera a lista de arquivos formatada '[ID] nome_arquivo' para o Dropdown."""
    try:
        res = requests.get(f"{API_BASE}/transcricoes", params={"limit": 100}, timeout=5)
        if res.status_code == 200:
            dados = res.json().get("dados", [])
            return [f"[{item['id']}] {item['nome_arquivo']}" for item in dados]
    except Exception:
        pass
    return []

def obter_lista_nomes_arquivos():
    """Retorna uma lista simples com os nomes dos arquivos de áudio transcritos no acervo."""
    try:
        res = requests.get(f"{API_BASE}/transcricoes", params={"limit": 100}, timeout=5)
        if res.status_code == 200:
            dados = res.json().get("dados", [])
            nomes = [item['nome_arquivo'] for item in dados if item.get('nome_arquivo')]
            if nomes:
                return sorted(list(set(nomes)))
    except Exception:
        pass
    return []

def ao_selecionar_dropdown_acervo(opcao, termo_filtro=""):
    """Executado automaticamente ao selecionar um item no Dropdown de arquivos."""
    if not opcao:
        return "", "*Selecione um arquivo no menu acima para visualizar.*", None
    import re
    match = re.search(r'\[(\d+)\]', str(opcao))
    if match:
        id_str = match.group(1)
        md, audio_path = abrir_modal_detalhes(id_str, termo_filtro)
        return id_str, md, audio_path
    md, audio_path = abrir_modal_detalhes(opcao, termo_filtro)
    return str(opcao), md, audio_path

def ao_selecionar_linha_grid(evt: gr.SelectData, termo_filtro=""):
    """Disparado automaticamente ao clicar em qualquer célula ou linha da Grid do Acervo."""
    if evt:
        if evt.index is not None:
            try:
                row_idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else int(evt.index)
                df = carregar_acervo_grid(termo_filtro)
                if not df.empty and row_idx < len(df):
                    id_row = str(df.iloc[row_idx]["ID"])
                    md, audio_path = abrir_modal_detalhes(id_row, termo_filtro)
                    return id_row, md, audio_path
            except Exception as ex:
                logging.warning(f"Erro ao selecionar linha da grid por index: {ex}")
        
        val = str(evt.value).strip() if evt.value else ""
        if val:
            md, audio_path = abrir_modal_detalhes(val, termo_filtro)
            return val, md, audio_path

    return "", "*Clique em uma linha da grid acima para visualizar a transcrição formatada.*", None

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

        # ABA 2: Acervo & Gestão de Áudios
        with gr.TabItem("📁 Acervo & Gestão"):
            gr.Markdown("### 📁 Acervo Geral de Transcrições & Gestão do Banco de Dados")
            
            with gr.Row():
                input_filtro_acervo = gr.Textbox(label="Filtrar por nome ou palavra-chave", placeholder="Ex: Empresa XYZ, 250704...", scale=3)
                btn_refresh_acervo = gr.Button("🔄 Atualizar / Filtrar Acervo", variant="secondary", scale=1)

            grid_acervo = gr.Dataframe(
                value=carregar_acervo_grid,
                headers=["ID", "Nome do Arquivo", "Data Upload", "Duração", "Palavras", "Status", "Player / Mídia", "Transcrição Disponível?"],
                datatype=["number", "str", "str", "str", "str", "str", "str", "str"],
                col_count=(8, "fixed"),
                type="pandas",
                label="📊 Lista de Áudios e Metadados do Banco de Dados (MySQL) - Clique em qualquer linha para tocar o áudio e abrir a transcrição!",
                interactive=True
            )

            gr.Markdown("---")
            gr.Markdown("### 👁️ Inspeção Detalhada e Player de Mídia da Transcrição")

            with gr.Row():
                dropdown_selecao = gr.Dropdown(
                    choices=obter_lista_choices_acervo(),
                    label="⚡ Seleção Rápida por Menu Dropdown (Escolha qualquer arquivo)",
                    value=None,
                    scale=2
                )
                input_id_selecionado = gr.Textbox(label="ID / Arquivo Selecionado", placeholder="Ex: 36 ou 250704_001.mp3", scale=1)

            with gr.Row():
                btn_abrir_modal = gr.Button("👁️ Visualizar Transcrição & Carregar Áudio", variant="primary", scale=2)
                btn_melhorar_audio = gr.Button("✨ Tratar Áudio (Filtro Vocal & Normalização)", variant="secondary", scale=2)
                btn_excluir_acervo = gr.Button("🗑️ Excluir Registro", variant="stop", scale=1)

            out_status_acervo = gr.Textbox(label="Status da Ação", visible=False)

            with gr.Accordion("🎧 Player de Áudio Integrado - Tocador da Reunião (Play / Pausa)", open=True):
                player_audio_acervo = gr.Audio(label="🎧 Controles de Mídia: Tocar, Pausar, Avançar e Ajustar Velocidade", type="filepath", interactive=False)
            
            with gr.Accordion("📄 Visualizador de Transcrição Formatada & Metadados", open=True):
                out_modal_conteudo = gr.Markdown(value="*Selecione um arquivo no Dropdown ou clique em qualquer linha da grid para carregar o áudio e a transcrição automaticamente.*")

            dropdown_selecao.change(fn=ao_selecionar_dropdown_acervo, inputs=[dropdown_selecao, input_filtro_acervo], outputs=[input_id_selecionado, out_modal_conteudo, player_audio_acervo])
            grid_acervo.select(fn=ao_selecionar_linha_grid, inputs=[input_filtro_acervo], outputs=[input_id_selecionado, out_modal_conteudo, player_audio_acervo])
            btn_refresh_acervo.click(fn=carregar_acervo_grid, inputs=[input_filtro_acervo], outputs=[grid_acervo])
            btn_abrir_modal.click(fn=abrir_modal_detalhes, inputs=[input_id_selecionado, input_filtro_acervo], outputs=[out_modal_conteudo, player_audio_acervo])
            btn_melhorar_audio.click(fn=acao_melhorar_audio_selecionado, inputs=[input_id_selecionado, input_filtro_acervo], outputs=[out_modal_conteudo, player_audio_acervo])
            btn_excluir_acervo.click(fn=excluir_registro_acervo, inputs=[input_id_selecionado], outputs=[out_status_acervo, grid_acervo])

        # ABA 3: Pesquisa Semântica & Histórico
        with gr.TabItem("🔍 Pesquisa & Histórico"):
            gr.Markdown("### 🔍 Pesquisa Semântica & Consulta de Registros")
            input_busca = gr.Textbox(label="Digite o termo ou conceito a pesquisar (ex: 'data lake', 'orçamento', 'Azure')", placeholder="Ex: reuniões sobre custos...")
            btn_busca = gr.Button("🔍 Pesquisar", variant="secondary")
            out_busca = gr.Textbox(label="ResultadosEncontrados", lines=14)

            btn_busca.click(fn=realizar_pesquisa, inputs=[input_busca], outputs=[out_busca])

        # ABA 4: Dashboard de Métricas
        with gr.TabItem("📊 Dashboard & Estatísticas"):
            gr.Markdown("### 📊 Indicadores Globais de Uso da Plataforma")
            btn_refresh_dash = gr.Button("🔄 Atualizar Métricas")
            out_dash = gr.Markdown(value=carregar_dashboard_stats)

            btn_refresh_dash.click(fn=carregar_dashboard_stats, inputs=[], outputs=[out_dash])

        # ABA 5: Chat Inteligente com Transcrição (RAG)
        with gr.TabItem("💬 Chat RAG com Áudio"):
            gr.Markdown("### 💬 Tire Dúvidas sobre uma Transcrição Específica")
            input_nome_chat = gr.Dropdown(
                choices=obter_lista_nomes_arquivos(),
                label="Selecione o arquivo de áudio para tirar dúvidas (Chat RAG)",
                value=None,
                allow_custom_value=True
            )
            input_pergunta_chat = gr.Textbox(label="Sua pergunta sobre o conteúdo deste áudio")
            btn_chat = gr.Button("🤖 Perguntar à IA", variant="primary")
            out_resposta_chat = gr.Textbox(label="Resposta da IA (baseada apenas na transcrição)", lines=8)

            btn_chat.click(fn=responder_chat_rag, inputs=[input_nome_chat, input_pergunta_chat], outputs=[out_resposta_chat])

        # ABA 6: Exportação de Relatórios e Atas em PDF
        with gr.TabItem("📥 Exportar Relatório"):
            gr.Markdown("### 📥 Exportação de Documentos e Atas Operacionais em PDF")
            input_nome_exp = gr.Dropdown(
                choices=obter_lista_nomes_arquivos(),
                label="Selecione o arquivo para exportar relatório / PDF",
                value=None,
                allow_custom_value=True
            )
            radio_formato = gr.Radio(choices=["PDF (Ata Operacional)", "TXT", "Markdown", "HTML"], value="PDF (Ata Operacional)", label="Formato de Saída")
            btn_export = gr.Button("📝 Gerar e Baixar Documento Exportado", variant="primary")
            
            with gr.Row():
                out_export = gr.Textbox(label="Status e Detalhes do Documento", lines=8)
                out_file_pdf = gr.File(label="📥 Download Direto do PDF (Ata Operacional)")

            btn_export.click(fn=gerar_exportacao, inputs=[input_nome_exp, radio_formato], outputs=[out_export, out_file_pdf])

demo.launch(server_name="127.0.0.1", server_port=7860)
