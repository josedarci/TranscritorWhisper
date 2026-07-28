# 🎙️ Transcritor Inteligente v2.0 Enterprise

Plataforma profissional de processamento de áudios em lote, transcrição automatizada (**Whisper**), resumo e síntese em Português (**Ollama Llama 3**), extração semântica de entidades, busca vetorial / RAG, exportação multi-formato e persistência relacional (**Node.js + Express + MySQL**).

---

## 🎯 Arquitetura do Sistema

```text
                                 ┌─────────────────────────────────┐
                                 │     Interface Gradio Web UI     │
                                 └────────────────┬────────────────┘
                                                  │
                                  ┌───────────────┴───────────────┐
                                  ▼                               ▼
                      ┌──────────────────────┐        ┌──────────────────────┐
                      │ ThreadPoolExecutor   │        │ VectorStore & RAG    │
                      │ (Process. Paralelo)  │        │ (Busca Semântica)    │
                      └───────────┬──────────┘        └──────────────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
      ┌────────────────────┐            ┌────────────────────┐
      │  OpenAI Whisper    │            │  Ollama Llama 3    │
      │  (Transcrição)     │            │  (Resumos & Tags)  │
      └──────────┬─────────┘            └──────────┬─────────┘
                 │                                 │
                 └────────────────┬────────────────┘
                                  ▼
                      ┌──────────────────────┐
                      │ Node.js REST API     │
                      └───────────┬──────────┘
                                  ▼
                      ┌──────────────────────┐
                      │  MySQL Database v2   │
                      └──────────────────────┘
```

---

## 🚀 Novas Funcionalidades Implementadas

### 🎙️ 1. Processamento Paralelo & Progresso em Tempo Real
- **Concorrência com ThreadPoolExecutor**: Processamento simultâneo de múltiplos arquivos de áudio com controle configurável de workers (1 a 8 simultâneos).
- **Rastreamento de Estados**: Progresso percentual visual no Gradio com status individual por arquivo (`Aguardando`, `Transcrevendo`, `Gerando Resumo`, `Salvando`, `Concluído`, `Erro`).
- **Isolamento de Falhas**: Erros em um arquivo não interrompem o processamento dos demais.
- **Relatório de Desempenho**: Exibição do tempo total do lote, tempo médio por arquivo e métricas detalhadas.

### 🧠 2. Inteligência Artificial Avançada & Extração Semântica
- **Resumos em Português do Brasil**: Geração automática de resumos concisos e estruturados em tópicos via Ollama (Llama 3).
- **Tags Automáticas**: Identificação de categorias, temas centrais, área de negócio e nível de prioridade.
- **Extração de Entidades**: Extração em JSON de Pessoas, Empresas, Datas, Valores, E-mails e Telefones citados nos áudios.

### 💬 3. Chat RAG & Busca Semântica
- **Chat com a Transcrição (RAG)**: Faça perguntas sobre o conteúdo de um áudio específico. A IA responde fundamentando-se estritamente na transcrição.
- **Busca Semântica (VectorStore)**: Busca conceitual por similaridade de cosseno ("Encontre reuniões sobre custos ou Azure").

### 📊 4. Dashboard de Métricas & Histórico
- **Painel de Indicadores Globais**: Visualização de horas acumuladas, total de palavras processadas, tempo médio de execução e total de usuários.
- **Histórico & Pesquisa Híbrida**: Consulta por palavra-chave no banco MySQL combinada com busca vetorial.

### 📥 5. Exportação Multi-formato
- **Formatos Suportados**: Exportação instantânea de relatórios completos nos formatos **TXT**, **Markdown (.md)** e **HTML estilizado**.

---

## 📂 Estrutura do Projeto

```text
Transcritor/
├── app.py                      # Aplicação Principal Gradio Web UI (Python)
├── services/
│   ├── ai_extractor.py          # Serviço de Tags e Extração de Entidades via Ollama
│   ├── vector_store.py          # Banco Vetorial e Engine de RAG/Busca Semântica
│   └── exporter.py              # Exportador nos formatos TXT, Markdown e HTML
├── database/
│   └── migration_v2.sql         # Script SQL de Expansão da Tabela transcricoes
├── transcritor-whisper/
│   └── backend/
│       ├── server.js            # API REST Node.js + Express
│       ├── package.json         # Dependências do Backend Node
│       └── Dockerfile           # Dockerfile do Backend Node
├── tests/
│   └── test_transcritor.py      # Suíte de Testes Unitários (unittest)
├── .env / .env.example          # Configurações Centralizadas de Ambiente
├── docker-compose.yml           # Orquestração Completa de Contêineres
├── Dockerfile                   # Dockerfile da Aplicação Python
└── README.md                    # Documentação Técnica Oficial
```

---

## 🛠️ Endpoints da API REST Node.js v2

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `POST` | `/api/salvar-completo` | Registra a transcrição completa com metadados, tempos, tags e entidades |
| `GET` | `/api/transcricoes` | Lista histórico com suporte a busca (`?q=`), filtro e paginação (`?page=&limit=`) |
| `GET` | `/api/transcricoes/:id` | Retorna os detalhes de um registro específico por ID |
| `DELETE` | `/api/transcricoes/:id` | Exclui um registro do banco de dados |
| `GET` | `/api/stats` | Retorna métricas agregadas para o Dashboard |

---

## 🗄️ Estrutura da Tabela MySQL (`transcricoes`)

Campos presentes na versão v2 (`database/migration_v2.sql`):
- `id`, `nome_arquivo`, `url`, `caminho`, `tamanho_bytes`, `duracao_segundos`, `idioma`, `modelo_whisper`, `modelo_llama`, `tempo_transcricao`, `tempo_resumo`, `tempo_total`, `status`, `texto`, `resumo`, `quantidade_palavras`, `quantidade_caracteres`, `data_upload`, `data_processamento`, `hash_sha256`, `usuario`, `tags` (JSON), `entidades` (JSON), `criado_em`.

---

## ⚙️ Instalação e Execução

### 1. Aplicar a Migration no MySQL
```bash
mysql -u root -p joseda34_site < database/migration_v2.sql
```

### 2. Iniciar o Backend Node.js
```bash
cd transcritor-whisper/backend
npm install
node server.js
```

### 3. Iniciar a Aplicação Python Gradio
No diretório raiz:
```bash
python3 app.py
```
Acesse no navegador: **[http://127.0.0.1:7860](http://127.0.0.1:7860)**

---

## 🐳 Execução via Docker Compose

Para subir o ambiente containerizado completo (MySQL + Node API + Python App):
```bash
docker compose up --build -d
```

---

## 🧪 Suíte de Testes Unitários

Para rodar os testes unitários automatizados:
```bash
python3 -m unittest discover -s tests
```
