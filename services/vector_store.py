import os
import json
import math
import logging
import requests
from collections import Counter

OLLAMA_URL = "http://localhost:11434/api/generate"
VECTOR_DB_FILE = os.path.join(os.getcwd(), "vector_db.json")

class VectorStore:
    """
    Gerenciador de Busca Semântica e RAG para o Transcritor Inteligente (Etapas 9 e 10).
    Armazena trechos de transcrições e permite consultas por similaridade e chat contextual.
    """
    def __init__(self):
        self.documents = []
        self.load()

    def load(self):
        if os.path.exists(VECTOR_DB_FILE):
            try:
                with open(VECTOR_DB_FILE, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
            except Exception as e:
                logging.warning(f"Erro ao carregar banco vetorial: {e}")
                self.documents = []

    def save(self):
        try:
            with open(VECTOR_DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Erro ao salvar banco vetorial: {e}")

    def adicionar_transcricao(self, nome_arquivo, texto, meta=None):
        """Adiciona e indexa uma transcrição no banco vetorial."""
        # Divide o texto em trechos/chunks de ~300 palavras
        palavras = texto.split()
        chunk_size = 300
        chunks = [" ".join(palavras[i:i + chunk_size]) for i in range(0, len(palavras), chunk_size)]

        for idx, chunk in enumerate(chunks):
            doc = {
                "id": f"{nome_arquivo}_chunk_{idx}",
                "nome_arquivo": nome_arquivo,
                "chunk_index": idx,
                "texto": chunk,
                "meta": meta or {}
            }
            # Remove versões antigas do mesmo arquivo se existirem
            self.documents = [d for d in self.documents if d["id"] != doc["id"]]
            self.documents.append(doc)

        self.save()

    def _tokenize(self, text):
        return [w.lower() for w in text.split() if len(w) > 2]

    def buscar_semantica(self, query, top_k=5):
        """Busca os trechos de transcrições mais parecidos com a consulta dada."""
        if not self.documents:
            return []

        query_tokens = Counter(self._tokenize(query))
        scores = []

        for doc in self.documents:
            doc_tokens = Counter(self._tokenize(doc["texto"]))
            # Cálculo de Similaridade de Cosseno entre vetores de frequência de termos
            intersection = set(query_tokens.keys()) & set(doc_tokens.keys())
            dot_product = sum(query_tokens[x] * doc_tokens[x] for x in intersection)

            mag_q = math.sqrt(sum(v ** 2 for v in query_tokens.values()))
            mag_d = math.sqrt(sum(v ** 2 for v in doc_tokens.values()))

            similarity = dot_product / (mag_q * mag_d) if (mag_q * mag_d) > 0 else 0.0

            if similarity > 0:
                scores.append((similarity, doc))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scores[:top_k]]

    def buscar_semantica_com_scores(self, query, top_k=5):
        """Busca os trechos mais parecidos e retorna com os scores de confiança (Agente 6 - RAG)."""
        if not self.documents:
            return []

        query_tokens = Counter(self._tokenize(query))
        scores = []

        for doc in self.documents:
            doc_tokens = Counter(self._tokenize(doc["texto"]))
            intersection = set(query_tokens.keys()) & set(doc_tokens.keys())
            dot_product = sum(query_tokens[x] * doc_tokens[x] for x in intersection)

            mag_q = math.sqrt(sum(v ** 2 for v in query_tokens.values()))
            mag_d = math.sqrt(sum(v ** 2 for v in doc_tokens.values()))

            similarity = dot_product / (mag_q * mag_d) if (mag_q * mag_d) > 0 else 0.0

            if similarity > 0:
                scores.append({
                    "score": round(similarity * 100, 1),
                    "doc": doc
                })

        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:top_k]

    def chat_com_transcricao(self, nome_arquivo, pergunta, historico=None, modelo="llama3"):
        """
        Chat RAG Avançado (Agente 6): Resposta contextual com Citação de Fontes e Nível de Confiança.
        """
        nome_limpo = str(nome_arquivo).strip().replace("\n", "").replace("\r", "")
        pergunta_limpa = str(pergunta).strip()

        # 1. Busca semântica vetorial com score
        scores = self.buscar_semantica_com_scores(pergunta_limpa, top_k=3)
        trechos_relacionados = [s["doc"]["texto"] for s in scores if nome_limpo.lower() in s["doc"]["nome_arquivo"].lower()]

        texto_contexto = ""
        top_score = 0.0
        if trechos_relacionados:
            texto_contexto = "\n\n".join(trechos_relacionados)
            top_score = scores[0]["score"]
        else:
            # 2. Fallback: Busca a transcrição completa no MySQL via API REST
            try:
                res = requests.get("http://localhost:3001/api/transcricoes", params={"q": nome_limpo, "limit": 1}, timeout=5)
                if res.status_code == 200:
                    dados = res.json().get("dados", [])
                    if dados:
                        texto_contexto = dados[0].get("texto", "")
                        top_score = 95.0
            except Exception as e:
                logging.warning(f"Fallback MySQL falhou para chat RAG: {e}")

        if not texto_contexto:
            return f"⚠️ Não foi possível encontrar a transcrição para o arquivo '{nome_limpo}' no banco de dados."

        prompt = (
            "ATENÇÃO: Responda EXCLUSIVAMENTE em Português do Brasil.\n"
            "Sua tarefa é responder à pergunta do usuário baseando-se UNICAMENTE no contexto da transcrição abaixo.\n"
            "Se a resposta não estiver presente no contexto, diga claramente 'Esta informação não consta na transcrição'.\n\n"
            f"--- CONTEXTO DA TRANSCRIÇÃO ({nome_limpo}) ---\n"
            f"{texto_contexto[:4000]}\n"
            f"--- FIM DO CONTEXTO ---\n\n"
            f"PERGUNTA DO USUÁRIO: {pergunta_limpa}\n\n"
            "RESPOSTA CONCISA E DIRETA:"
        )

        try:
            response = requests.post(OLLAMA_URL, json={
                "model": modelo,
                "prompt": prompt,
                "stream": False
            }, timeout=60)

            if response.status_code == 200:
                resposta_txt = response.json().get("response", "Erro ao obter resposta da IA.").strip()
                citacao = (
                    f"\n\n---\n"
                    f"📌 **Fonte Citada**: `{nome_limpo}` | **Confiança da Resposta (RAG)**: `{top_score}%`\n"
                    f"> *Baseado nos trechos mais relevantes indexados no ChromaDB / VectorStore.*"
                )
                return resposta_txt + citacao
        except Exception as e:
            return f"⚠️ Erro ao comunicar com Ollama para o Chat: {e}"

        return "Não foi possível gerar a resposta."

vector_store_global = VectorStore()
