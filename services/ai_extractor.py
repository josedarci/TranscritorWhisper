import json
import logging
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def gerar_tags_e_categorias(texto, modelo="llama3"):
    """
    Solicita ao Ollama a geração de tags, categorias, área de negócio,
    tema central e nível de prioridade (Etapa 7).
    """
    prompt = (
        "ATENÇÃO: Responda EXCLUSIVAMENTE em formato JSON válido contendo as chaves exatas indicadas.\n"
        "Não inclua nenhuma introdução ou texto fora do objeto JSON.\n\n"
        "Analise o seguinte texto transcrito de áudio/reunião e extraia:\n"
        "1. categorias: lista de 2 a 4 categorias principais\n"
        "2. tags: lista de 5 a 10 tags/palavras-chave relevantes\n"
        "3. area: área de negócio ou departamento relacionado (ex: Tecnologia, Finanças, RH, Vendas)\n"
        "4. tema: tema principal em poucas palavras\n"
        "5. prioridade: nível de prioridade estimado ('Baixa', 'Média', 'Alta', 'Crítica')\n\n"
        f"Texto:\n{texto[:4000]}\n\n"
        "Exemplo de resposta JSON:\n"
        "{\n"
        '  "categorias": ["Engenharia de Software", "Conhecimento Internalizado"],\n'
        '  "tags": ["data lake", "conhecimento", "processos", "eficiência"],\n'
        '  "area": "Tecnologia da Informação",\n'
        '  "tema": "Implantação de Data Lake e Base de Conhecimento",\n'
        '  "prioridade": "Alta"\n'
        "}"
    )

    try:
        response = requests.post(OLLAMA_URL, json={
            "model": modelo,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=60)

        if response.status_code == 200:
            res_raw = response.json().get("response", "{}").strip()
            return json.loads(res_raw)
    except Exception as e:
        logging.warning(f"Erro ao extrair tags via Ollama: {e}")

    return {
        "categorias": ["Geral"],
        "tags": ["transcrição"],
        "area": "Geral",
        "tema": "Geral",
        "prioridade": "Média"
    }

def extrair_entidades(texto, modelo="llama3"):
    """
    Solicita ao Ollama a extração estruturada de entidades como pessoas,
    empresas, datas, valores, emails, URLs e documentos (Etapa 8).
    """
    prompt = (
        "ATENÇÃO: Responda EXCLUSIVAMENTE em formato JSON válido contendo as chaves exatas.\n"
        "Não inclua explicações ou texto fora do JSON.\n\n"
        "Extraia do texto transcrito abaixo todas as entidades mencionadas:\n"
        "- pessoas: lista de nomes de pessoas\n"
        "- empresas: lista de empresas, organizações ou marcas\n"
        "- datas: lista de datas, prazos ou momentos citados\n"
        "- valores: lista de valores monetários ou quantias\n"
        "- telefones: lista de números de telefone\n"
        "- emails: lista de endereços de e-mail\n"
        "- urls: lista de links ou sites citados\n"
        "- cpf_cnpj: lista de CPFs ou CNPJs citados\n\n"
        f"Texto:\n{texto[:4000]}\n\n"
        "Resposta JSON:"
    )

    try:
        response = requests.post(OLLAMA_URL, json={
            "model": modelo,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=60)

        if response.status_code == 200:
            res_raw = response.json().get("response", "{}").strip()
            return json.loads(res_raw)
    except Exception as e:
        logging.warning(f"Erro ao extrair entidades via Ollama: {e}")

    return {
        "pessoas": [],
        "empresas": [],
        "datas": [],
        "valores": [],
        "telefones": [],
        "emails": [],
        "urls": [],
        "cpf_cnpj": []
    }
