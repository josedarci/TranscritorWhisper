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
                      └───────────┬──────────┘
```

---

## 📖 MANUAL DE INSTALAÇÃO PASSO A PASSO

Você pode instalar o projeto de duas formas:
1. **Via Docker & Docker Compose (Recomendado - Mais Fácil e Rápido)**
2. **Instalação Nativa no Sistema Operacional (macOS / Linux / Windows)**

---

### 🐳 OPÇÃO 1: Instalação e Uso com Docker & Docker Compose (RECOMENDADO)

O uso com **Docker** elimina a necessidade de instalar MySQL, Node.js ou FFmpeg manualmente no seu sistema. Tudo roda de forma isolada e pré-configurada em contêineres.

#### 1. Pré-requisitos para Docker:
- **Docker Desktop** (macOS ou Windows) ou **Docker Engine + Docker Compose** (Linux).
- **Ollama** instalado e rodando na máquina host com o modelo `llama3` baixado:
  ```bash
  ollama run llama3
  ```

#### 2. Configurar o Arquivo de Ambiente:
Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

#### 3. Subir a Plataforma com Docker Compose:
No diretório raiz do projeto, execute:
```bash
docker compose up --build -d
```
*A opção `-d` roda os contêineres em segundo plano (detached mode).*

#### 4. Verificar se os Serviços Estão Rodando:
```bash
docker compose ps
```
Você verá os contêineres:
- `transcritor_mysql` (Porta 3306)
- `transcritor_backend` (Porta 3001)
- `transcritor_python` (Porta 7860)

#### 5. Acessar a Aplicação:
- **Interface Web (Gradio)**: `http://localhost:7860`
- **API REST (Node.js)**: `http://localhost:3001`

#### 🛠️ Comandos Úteis do Docker:
- **Ver logs em tempo real**:
  ```bash
  docker compose logs -f
  ```
- **Ver logs apenas da aplicação Python**:
  ```bash
  docker compose logs -f python-app
  ```
- **Parar os serviços sem apagar dados**:
  ```bash
  docker compose stop
  ```
- **Reiniciar a aplicação**:
  ```bash
  docker compose restart
  ```
- **Desligar e remover contêineres e volumes**:
  ```bash
  docker compose down -v
  ```

---

### 💻 OPÇÃO 2: Instalação Nativa no Sistema (macOS / Linux / Windows)

Caso prefira rodar os componentes diretamente no seu sistema operacional, siga a ordem abaixo:

#### 1. Instalar o FFmpeg (Obrigatório para o Whisper decodificar áudios)
- **macOS**:
  ```bash
  brew install ffmpeg
  ```
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```
- **Windows**:
  Instale via Chocolatey (`choco install ffmpeg`) ou baixe o executável oficial e adicione ao PATH do sistema.

#### 2. Instalar e Iniciar o Ollama (Para Resumos e Tags com Llama 3)
- **macOS / Linux**:
  ```bash
  brew install ollama
  brew services start ollama
  ollama run llama3
  ```
- **Windows**: Baixe o instalador em [ollama.com](https://ollama.com) e execute `ollama run llama3` no Prompt/PowerShell.

#### 3. Configurar o Banco de Dados MySQL
1. Abra o seu cliente MySQL e crie o banco de dados:
   ```sql
   CREATE DATABASE IF NOT EXISTS joseda34_site DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. Aplique o script de migration v2:
   ```bash
   mysql -u seu_usuario -p joseda34_site < database/migration_v2.sql
   ```

#### 4. Configurar as Variáveis de Ambiente
Copie `.env.example` para `.env` e ajuste as credenciais do seu MySQL local:
```bash
cp .env.example .env
```

#### 5. Iniciar o Backend Node.js API
```bash
cd transcritor-whisper/backend
npm install
node server.js
```
*A API estará pronta em `http://localhost:3001`.*

#### 6. Iniciar a Aplicação Python Gradio
Em outro terminal, no diretório raiz do projeto:
```bash
pip install -r transcritor-whisper/requirements.txt
pip install openai-whisper gradio requests
python3 app.py
```
*A interface web abrirá em **`http://127.0.0.1:7860`**.*

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

## ❓ Troubleshooting / Solução de Problemas Comuns

### 1. `dyld: Library not loaded / libx265.dylib` (macOS)
Isso acontece se o Homebrew atualizar bibliotecas do sistema e quebrar os links dinâmicos do FFmpeg antigo.
**Solução**:
```bash
brew reinstall ffmpeg
```

### 2. `RuntimeError: cannot reshape tensor of 0 elements`
Isso ocorria quando múltiplas threads tentavam acessar a inferência do Whisper simultaneamente. 
**Solução**: Já foi corrigido na versão v2.0 através da inclusão de um `threading.Lock()` em `app.py`.

### 3. `Connection Refused: http://localhost:11434`
Significa que o servidor do Ollama não está ativo no seu computador.
**Solução**: Inicie o Ollama com `ollama serve` ou `brew services start ollama`.

---

## 🧪 Suíte de Testes Unitários

Para rodar a suíte de testes unitários automatizados:
```bash
python3 -m unittest discover -s tests
```
