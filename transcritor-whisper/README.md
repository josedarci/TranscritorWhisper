# 🎙️ Transcritor Whisper & Ollama IA (Backend & Modules)

Documentação do módulo backend e serviços do **Transcritor Inteligente v2.0 Enterprise**.

---

## 🛠️ Módulos e Componentes

### 1. API Node.js Express (`backend/server.js`)
Servidor REST em Node.js com conexão MySQL para persistência de transcrições e metadados.

#### Endpoints Principais:
- `POST /api/salvar-completo`: Registra transcrições com metadados avançados (durações, palavras, SHA-256, tags JSON, entidades).
- `GET /api/transcricoes`: Histórico paginado e pesquisável.
- `GET /api/stats`: Métricas agregadas do sistema.

### 2. Módulos de Inteligência Artificial (`services/`)
- `ai_extractor.py`: Tags automáticas e extração estruturada de entidades.
- `vector_store.py`: Engine de Busca Semântica e RAG Chat.
- `exporter.py`: Gerador de relatórios nos formatos TXT, Markdown e HTML.

---

## ⚙️ Instalação e Execução do Backend

```bash
cd backend
npm install
node server.js
```
A API ficará disponível em `http://localhost:3001`.
