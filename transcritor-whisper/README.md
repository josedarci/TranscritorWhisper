# 🎙️ Transcritor Whisper & Ollama IA (Backend & Multiagent Modules v3.0 Enterprise)

Documentação técnica do módulo backend, APIs REST e serviços de Inteligência Artificial do **Transcritor Inteligente Enterprise**.

---

## 🛠️ Arquitetura de Módulos & Componentes v3.0

### 1. API Node.js Express & Segurança (`backend/server.js`)
Servidor REST de alta performance em Node.js com conexão MySQL relacional v3, suporte a Multi-Tenancy (Empresas), Autenticação JWT, Controle RBAC e Trilha de Auditoria.

#### 🔌 Endpoints Principais:
- **Autenticação & Segurança**:
  - `POST /api/auth/register`: Cadastro de usuários e empresas.
  - `POST /api/auth/login`: Autenticação e emissão de tokens JWT.
  - `GET /api/auth/me`: Perfil e permissões do usuário logado.
  - `GET /api/docs`: Documentação interativa em formato OpenAPI 3.0 (Swagger).
- **Mídia & Transcrições**:
  - `POST /api/salvar-completo`: Registra transcrições com metadados avançados (durações, palavras, SHA-256, tags JSON, entidades).
  - `GET /api/transcricoes`: Histórico paginado e pesquisável.
  - `GET /api/stats`: Métricas agregadas e estatísticas do Dashboard.
- **Integração Móvel (Android / iOS / Desktop)**:
  - `POST /api/mobile/upload`: Upload direto de mídias do smartphone.
  - `GET /api/mobile/transcricoes`: Feed de notícias otimizado para mobile.
  - `POST /api/mobile/notificacoes`: Notificações Push de processamento.

### 2. Módulos de Inteligência Artificial & Pipeline (`pipeline/` & `services/`)
- **`pipeline/audio_processor.py`**: **Speaker Diarization (Identificação de Locutores)** e **Deduplicação via Cache Hash SHA-256**.
- **`pipeline/llm_enricher.py`**: Motor de síntese com **Templates de Prompts Externos em Markdown** ([`prompts/`](../prompts/)).
- **`services/vector_store.py`**: Engine de **Busca Semântica & Chat RAG Avançado** com **Citação de Fontes** e **Pontuação de Confiança %**.
- **`services/exporter.py`**: Gerador de relatórios nos formatos **TXT, Markdown, HTML e Atas Operacionais em PDF**.

---

## ⚙️ Instalação e Execução do Backend

```bash
cd backend
npm install
node server.js
```
A API REST v3 ficará disponível em `http://localhost:3001`.
