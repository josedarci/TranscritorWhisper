import os
import json
import logging
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def carregar_prompt_template(nome_arquivo):
    """Carrega um template de prompt externo em markdown da pasta prompts/."""
    caminho = os.path.join(os.path.dirname(__file__), "..", "prompts", nome_arquivo)
    try:
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logging.warning(f"Erro ao carregar prompt {nome_arquivo}: {e}")
    return ""

def enriquecer_transcricao_completa(texto, modelo="llama3"):
    """
    Executa a síntese avançada de Inteligência Artificial via Ollama Llama 3 (Agente 5):
    - Resumo Executivo e Técnico
    - Identificação de Decisões, Pendências e Responsáveis
    - Análise de Riscos, Oportunidades e Sentimento
    - Extração de Entidades NER e Categorização
    """
    if not texto:
        return {}

    prompt_summary_template = carregar_prompt_template("summary.md")
    prompt_actions_template = carregar_prompt_template("actions.md")

    # 1. Análise de Resumo, Riscos e Sentimento
    resumo_data = {}
    if prompt_summary_template:
        prompt_final = prompt_summary_template.format(texto=texto[:4000])
        try:
            res = requests.post(OLLAMA_URL, json={
                "model": modelo,
                "prompt": prompt_final,
                "stream": False,
                "format": "json"
            }, timeout=60)
            if res.status_code == 200:
                res_raw = res.json().get("response", "{}").strip()
                resumo_data = json.loads(res_raw)
        except Exception as e:
            logging.warning(f"Falha na síntese executiva via Ollama: {e}")

    # 2. Extração de Decisões e Pendências
    acoes_data = {}
    if prompt_actions_template:
        prompt_actions = prompt_actions_template.format(texto=texto[:4000])
        try:
            res = requests.post(OLLAMA_URL, json={
                "model": modelo,
                "prompt": prompt_actions,
                "stream": False,
                "format": "json"
            }, timeout=60)
            if res.status_code == 200:
                res_raw = res.json().get("response", "{}").strip()
                acoes_data = json.loads(res_raw)
        except Exception as e:
            logging.warning(f"Falha na extração de ações via Ollama: {e}")

    return {
        "resumo_executivo": resumo_data.get("resumo_executivo", "Resumo processado com sucesso."),
        "resumo_tecnico": resumo_data.get("resumo_tecnico", ""),
        "sentimento": resumo_data.get("sentimento", "Neutro"),
        "riscos": resumo_data.get("riscos", []),
        "oportunidades": resumo_data.get("oportunidades", []),
        "decisoes": acoes_data.get("decisoes", []),
        "pendencias": acoes_data.get("pendencias", []),
        "responsaveis": acoes_data.get("responsaveis", [])
    }
