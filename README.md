# 🎙️ Transcritor Inteligente v2.0 Enterprise

Plataforma profissional de processamento de áudios em lote, transcrição automatizada (**Whisper**), resumo e síntese em Português (**Ollama Llama 3**), extração semântica de entidades, busca vetorial / RAG, exportação multi-formato e persistência relacional (**Node.js + Express + MySQL**).

### 🛠️ Tecnologias e Ferramentas Utilizadas

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![NodeJS](https://img.shields.io/badge/Node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white)
![Express.js](https://img.shields.io/badge/Express.js-000000?style=for-the-badge&logo=express&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![OpenAI Whisper](https://img.shields.io/badge/OpenAI_Whisper-412991?style=for-the-badge&logo=openai&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama_Llama_3-000000?style=for-the-badge&logo=ollama&logoColor=white)
![Gradio](https://img.shields.io/badge/Gradio-FF7C00?style=for-the-badge&logo=gradio&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)

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

## 📖 MANUAIS DE INSTALAÇÃO POR SISTEMA OPERACIONAL

Selecione o seu sistema operacional ou método de preferência para ver as instruções completas:

📌 **Índice de Instalação Rápida:**
- [🐳 Método Universal: Docker & Docker Compose (Recomendado)](#-método-universal-docker--docker-compose-macos--linux--windows)
- [🪟 Guia Passo a Passo: Windows (Prompt / PowerShell)](#-guia-de-instalação---windows)
- [🐧 Guia Passo a Passo: Linux (Ubuntu / Debian / Fedora)](#-guia-de-instalação---linux-ubuntu--debian--fedora)
- [🍎 Guia Passo a Passo: macOS (Homebrew)](#-guia-de-instalação---macos)

---

### 🐳 MÉTODO UNIVERSAL: Docker & Docker Compose (macOS / Linux / Windows)

O uso com **Docker** é o método recomendado pois instala o banco de dados MySQL, Node.js, Python e FFmpeg isoladamente em contêineres sem sujar o sistema.

#### 1. Pré-requisitos:
- Instalar o **Docker Desktop** (macOS/Windows) ou **Docker Engine + Docker Compose** (Linux).
- Ter o **Ollama** instalado na máquina host com o modelo `llama3`:
  ```bash
  ollama run llama3
  ```

#### 2. Passo a Passo:
1. Copie o arquivo de variáveis de ambiente:
   ```bash
   cp .env.example .env
   ```
2. Inicie os contêineres:
   ```bash
   docker compose up --build -d
   ```
3. Acessos:
   - **Interface Web Gradio**: `http://localhost:7860`
   - **API Backend Node.js**: `http://localhost:3001`

#### 🛠️ Comandos Úteis do Docker:
- **Ver logs em tempo real**: `docker compose logs -f`
- **Parar contêineres**: `docker compose stop`
- **Destruir contêineres e volumes**: `docker compose down -v`

---

### 🪟 GUIA DE INSTALAÇÃO — WINDOWS

#### 1. Instalar o Python e Node.js
- Baixe e instale o **Python 3.10+** em [python.org](https://www.python.org/). 
  > ⚠️ **IMPORTANTE**: Na tela inicial de instalação, marque a caixa **"Add Python to PATH"**.
- Baixe e instale o **Node.js LTS** em [nodejs.org](https://nodejs.org/).

#### 2. Instalar o FFmpeg no Windows
Escolha um dos métodos abaixo no PowerShell como Administrador:
- **Via Winget**:
  ```powershell
  winget install --id=Gyan.FFmpeg -e
  ```
- **Via Chocolatey**:
  ```powershell
  choco install ffmpeg
  ```
- *Ou baixe o binário no site oficial `gyan.dev/ffmpeg` e adicione a pasta `bin` às Variáveis de Ambiente do Sistema.*

#### 3. Instalar o Ollama no Windows
1. Baixe o executável `OllamaSetup.exe` em [ollama.com](https://ollama.com/download/windows).
2. Abra o Prompt de Comando ou PowerShell e baixe o modelo Llama 3:
   ```cmd
   ollama run llama3
   ```

#### 4. Instalar e Configurar o MySQL no Windows
1. Baixe o **MySQL Installer** em [dev.mysql.com](https://dev.mysql.com/downloads/installer/).
2. Abra o MySQL Workbench ou Command Line Client e crie o banco de dados:
   ```sql
   CREATE DATABASE joseda34_site DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Importe a migration executando no Prompt:
   ```cmd
   mysql -u root -p joseda34_site < database\migration_v2.sql
   ```

#### 5. Executar o Projeto no Windows
1. Copie `.env.example` para `.env`:
   ```cmd
   copy .env.example .env
   ```
2. Inicie a API Node.js:
   ```cmd
   cd transcritor-whisper\backend
   npm install
   node server.js
   ```
3. Em outra janela do Prompt/PowerShell, na raiz do projeto:
   ```cmd
   pip install -r transcritor-whisper\requirements.txt
   pip install openai-whisper gradio requests
   python app.py
   ```
4. Acesse no navegador: `http://127.0.0.1:7860`

---

### 🐧 GUIA DE INSTALAÇÃO — LINUX (Ubuntu / Debian / Fedora)

#### 1. Instalar as Dependências do Sistema e FFmpeg
No Ubuntu/Debian:
```bash
sudo apt update && sudo apt install -y ffmpeg python3-pip python3-venv git curl mysql-server nodejs npm
```
No Fedora:
```bash
sudo dnf install -y ffmpeg python3-pip git curl community-mysql-server nodejs
```

#### 2. Instalar e Configurar o Ollama
1. Execute o script oficial de instalação do Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. Inicie o serviço do Ollama:
   ```bash
   sudo systemctl enable --now ollama
   ```
3. Baixe o modelo Llama 3:
   ```bash
   ollama run llama3
   ```

#### 3. Configurar o MySQL no Linux
1. Abra o prompt do MySQL:
   ```bash
   sudo mysql -u root
   ```
2. Crie o banco e usuário:
   ```sql
   CREATE DATABASE IF NOT EXISTS joseda34_site DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER IF NOT EXISTS 'joseda34_dev'@'localhost' IDENTIFIED BY 'REDACTED_PASSWORD';
   GRANT ALL PRIVILEGES ON joseda34_site.* TO 'joseda34_dev'@'localhost';
   FLUSH PRIVILEGES;
   ```
3. Aplique a migration v2:
   ```bash
   mysql -u joseda34_dev -p joseda34_site < database/migration_v2.sql
   ```

#### 4. Executar o Projeto no Linux
1. Copie o arquivo `.env`:
   ```bash
   cp .env.example .env
   ```
2. Inicie a API Node.js:
   ```bash
   cd transcritor-whisper/backend
   npm install
   node server.js
   ```
3. Em outro terminal, crie o ambiente virtual Python e inicie o app:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r transcritor-whisper/requirements.txt
   pip install openai-whisper gradio requests
   python3 app.py
   ```
4. Acesse no navegador: `http://127.0.0.1:7860`

---

### 🍎 GUIA DE INSTALAÇÃO — macOS

#### 1. Instalar Dependências via Homebrew
```bash
brew install ffmpeg node mysql ollama
```

#### 2. Iniciar Serviços e Modelo Ollama
```bash
brew services start mysql
brew services start ollama
ollama run llama3
```

#### 3. Executar o Projeto no macOS
1. Aplicar a migration no MySQL:
   ```bash
   mysql -u root -p joseda34_site < database/migration_v2.sql
   ```
2. Iniciar a API Node.js:
   ```bash
   cd transcritor-whisper/backend
   npm install
   node server.js
   ```
3. Em outro terminal na raiz do projeto:
   ```bash
   pip3 install -r transcritor-whisper/requirements.txt
   pip3 install openai-whisper gradio requests
   python3 app.py
   ```
4. Acesse no navegador: `http://127.0.0.1:7860`

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
**Solução**: Reinstale o ffmpeg para recalibrar as bibliotecas do Homebrew:
```bash
brew reinstall ffmpeg
```

### 2. `FFmpeg not found / command not found` (Windows / Linux)
**Solução**: Certifique-se de que o executável `ffmpeg` está no PATH do sistema. No Windows, reinicie a janela do PowerShell após instalar.

### 3. `RuntimeError: cannot reshape tensor of 0 elements`
**Solução**: Já corrigido na v2.0 com `threading.Lock()` para garantir thread-safety do PyTorch.

---

## 🧪 Suíte de Testes Unitários

Para rodar a suíte de testes unitários automatizados:
```bash
python3 -m unittest discover -s tests
```
