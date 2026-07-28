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
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

---

## 🎯 Arquitetura do Sistema

Seu projeto utiliza uma arquitetura moderna que combina **Inteligência Artificial, processamento paralelo, backend REST, banco de dados relacional e busca semântica**. Abaixo explicamos cada tecnologia, por que ela foi escolhida e qual é seu papel dentro da plataforma.

```text
Usuário
   │
   ▼
Gradio (Interface Web)
   │
   ▼
ThreadPoolExecutor (Processamento Paralelo)
   │
   ▼
Whisper (Transcrição Audio -> Texto)
   │
   ▼
Ollama + Llama 3 (Resumos, Tags e Entidades)
   │
   ├──────────────────────────► VectorStore (ChromaDB / FAISS / Embeddings)
   │                                  │
   │                                  ▼
   │                            Busca Semântica & Chat RAG
   │                                  │
   ▼                                  ▼
Node.js + Express (API REST)
   │
   ▼
MySQL (Persistência Relacional)
   │
   ▼
Dashboard, Pesquisa, Exportação (TXT, MD, HTML)
```

---

### 1. 🐍 Python
- **O que é**: Linguagem de programação amplamente utilizada em Inteligência Artificial, Machine Learning, Ciência de Dados e automação.
- **Por que utilizar**: A maioria das bibliotecas de IA (Whisper, PyTorch, Transformers, LangChain, ChromaDB, FAISS) é desenvolvida primariamente em Python.
- **No projeto**: Responsável por toda a camada de IA, execução do Whisper, chamadas ao Ollama, processamento paralelo, exportações, embeddings e chat RAG.

---

### 2. 🎨 Gradio
- **O que é**: Framework Python para criação rápida de interfaces web interativas sem necessidade de escrever HTML, React ou Angular.
- **No projeto**: É a interface visual principal. Permite upload de vários áudios em lote, controle do número de workers simultâneos, visualização em tempo real de transcrições, resumos, dashboard, pesquisa e chat RAG.

---

### 3. 🎙️ OpenAI Whisper
- **O que é**: Modelo de IA de última geração desenvolvido pela OpenAI para conversão de fala em texto (Speech-to-Text).
- **Funciona com**: `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac` em diversos idiomas.
- **No projeto**: Responsável pela transcrição literal perfeita do áudio para o português, preservando nomes próprios e contexto.

---

### 4. 🎞️ FFmpeg
- **O que é**: Biblioteca/utilitário multimídia indispensável para abrir, extrair, normalizar e converter formatos de áudio e vídeo.
- **No projeto**: O Whisper depende internamente do FFmpeg para ler arquivos de áudio antes de passá-los aos tensores de inferência.

---

### 5. 🦙 Ollama
- **O que é**: Servidor e gerenciador local para execução de LLMs (*Large Language Models*) diretamente no seu computador.
- **Vantagem**: Roda sem dependência de internet, mantendo total privacidade dos dados e zero custos por requisição.
- **No projeto**: Gerencia a execução do modelo Llama 3 para resumos, extração de entidades e chat RAG.

---

### 6. 🧠 Llama 3 (Meta)
- **O que é**: Modelo de linguagem de grande porte (*LLM*) de última geração desenvolvido pela Meta.
- **No projeto**: Atua como o "cérebro" de síntese. Recebe a transcrição bruta do Whisper e gera o resumo estruturado em tópicos, identifica categorias e extrai entidades em JSON.

---

### 7. ⚡ ThreadPoolExecutor
- **O que é**: Módulo nativo de concorrência e multithreading do Python (`concurrent.futures`).
- **No projeto**: Permite que múltiplos arquivos de áudio sejam processados simultaneamente em segundo plano (com controle ajustável de 1 a 8 workers), aumentando a velocidade de lotes grandes.

---

### 8. 🟢 Node.js
- **O que é**: Ambiente de execução JavaScript assíncrono para desenvolvimento de serviços backend de alta performance.
- **No projeto**: Hospeda a API REST intermediária, responsável por receber requisições do Python, validar dados e se comunicar com a base MySQL.

---

### 9. 🚀 Express.js
- **O que é**: Framework web minimalista e flexível para Node.js.
- **No projeto**: Estrutura as rotas da API REST (como `POST /api/salvar-completo`, `GET /api/transcricoes` e `GET /api/stats`).

---

### 10. 🔌 API REST (REpresentational State Transfer)
- **O que é**: Arquitetura padrão de comunicação HTTP cliente-servidor baseada em JSON.
- **No projeto**: Desacopla a camada de processamento de IA (Python) da camada de armazenamento (Node.js/MySQL).

---

### 11. 🐬 MySQL Database
- **O que é**: Sistema de Gerenciamento de Banco de Dados Relacional (SGBD) confiável e amplamente utilizado no mercado.
- **No projeto**: Persiste todas as transcrições, resumos, durações, tempos de execução, hashes SHA-256, tags e entidades estruturadas.

---

### 12. 📦 JSON (JavaScript Object Notation)
- **O que é**: Formato leve de troca de dados estruturados.
- **No projeto**: Utilizado para armazenar listas dinâmicas de tags e entidades extraídas (Pessoas, Empresas, Datas, Valores, Emails) nas colunas nativas JSON do MySQL.

---

### 13. 🔍 ChromaDB
- **O que é**: Banco de dados vetorial de código aberto otimizado para aplicações de IA e pesquisas semânticas.
- **No projeto**: Indexa as transcrições para permitir buscas por conceito/significado e não apenas por palavras exatas.

---

### 14. ⚡ FAISS (Facebook AI Similarity Search)
- **O que é**: Biblioteca de busca por similaridade vetorial de altíssima velocidade desenvolvida pela Meta AI.
- **No projeto**: Trabalha em conjunto para indexar vetores e acelerar consultas conceituais em grandes volumes de áudio.

---

### 15. 🧮 Embeddings Vetoriais
- **O que é**: Representação de textos na forma de vetores numéricos de alta dimensão que capturam o significado conceitual das palavras.
- **No projeto**: Transforma cada frase da transcrição em vetores para viabilizar a busca por contexto.

---

### 16. 💬 RAG (Retrieval-Augmented Generation)
- **O que é**: Técnica avançada que combina busca em banco de dados vetorial com modelos LLM.
- **No projeto**: Alimenta a aba de Chat RAG. O sistema recupera os trechos do áudio escolhido e instrui o Llama 3 a responder à pergunta do usuário **apenas** com base naquele contexto, eliminando alucinações.

---

### 17. 🐳 Docker
- **O que é**: Plataforma de virtualização em nível de sistema operacional que empacota a aplicação e suas dependências em contêineres isolados.
- **No projeto**: Garante que os contêineres do Python, Node.js e MySQL rodem exatamente com as mesmas versões em qualquer sistema.

---

### 18. 🐙 Docker Compose
- **O que é**: Ferramenta para definir e rodar aplicações multi-contêiner Docker através de um único arquivo de configuração (`docker-compose.yml`).
- **No projeto**: Permite subir toda a infraestrutura da plataforma com um único comando: `docker compose up`.

---

### 19. 🔑 Variáveis de Ambiente (`.env`)
- **O que é**: Padrão de segurança para armazenar credenciais, hosts, portas e chaves secretas fora do código-fonte.
- **No projeto**: Centraliza em `.env` as configurações de conexões com MySQL, Ollama e rotas da API REST.

---

### 20. 🧪 Testes Unitários (`unittest`)
- **O que é**: Prática de engenharia de software para testar módulos isoladamente e prevenir regressões.
- **No projeto**: Suíte em `tests/test_transcritor.py` que valida automaticamente os exportadores (TXT, MD, HTML) e o motor de busca vetorial.

---

## 🏗️ Por que essa arquitetura é moderna e escalável?

Essa arquitetura separa claramente as responsabilidades:
- **Python** cuida de toda a Inteligência Artificial, transcrição e vetorização.
- **Whisper** transforma fala em texto.
- **Ollama + Llama 3** interpretam o conteúdo, gerando resumos, tags e respostas.
- **Node.js + Express** oferecem uma API REST organizada e desacoplada.
- **MySQL** mantém o histórico relacional seguro e estruturado.
- **VectorStore (ChromaDB/FAISS)** torna possível pesquisar por significado e realizar conversas via RAG.
- **Gradio** entrega uma interface fluida, moderna e sem complexidade de frontend.

Essa abordagem modular permite que qualquer componente seja atualizado ou escalado no futuro (ex: migrar para GPU na nuvem ou trocar o modelo de LLM) sem precisar reescrever o sistema!

---

## 💡 TUTORIAL COMPLETO DE USO E GUIA DE CADA FUNCIONALIDADE

Este guia explica detalhadamente como utilizar cada uma das 5 abas da plataforma, com instruções passo a passo e a explicação do que ocorre nos bastidores.

---

### 🎙️ 1. Aba: Transcrição em Lote
- **Objetivo**: Enviar múltiplos arquivos de áudio simultaneamente, transcrevê-los em paralelo, gerar resumos em Português e extrair tags/entidades.
- **Como Usar**:
  1. Arraste ou clique no campo de upload para selecionar seus arquivos de áudio (`.mp3`, `.wav`, `.m4a`).
  2. Marque a opção **"Gerar Resumo Inteligente (Ollama)"** para síntese em tópicos.
  3. Marque a opção **"Extrair Tags e Entidades Automáticas"** para obter Pessoas, Empresas, Datas, Valores e Emails.
  4. Ajuste o controle deslizante **"Workers Simultâneos"** (de 1 a 8 simultâneos) conforme a capacidade do seu computador.
  5. Clique em **"🚀 Processar Lote de Áudios"**.
- **Nos Bastidores**:
  - O `ThreadPoolExecutor` distribui os áudios entre os trabalhadores em paralelo.
  - Cada áudio é copiado com UUID único para `./uploads/`.
  - A transcrição é executada pelo Whisper com `threading.Lock()` para garantir thread-safety do PyTorch.
  - O Ollama (Llama 3) gera o resumo e extrai o JSON de entidades.
  - Todos os metadados, tempos por etapa e hash SHA-256 são gravados via API REST no MySQL.

---

### 🔍 2. Aba: Pesquisa & Histórico
- **Objetivo**: Consultar e filtrar transcrições anteriores por palavra-chave ou similaridade semântica por IA.
- **Como Usar**:
  1. Digite o termo ou conceito desejado no campo de busca (ex: *"contrato"*, *"orçamento"*, *"Azure"*).
  2. Clique em **"🔍 Pesquisar"**.
  3. Veja a lista com transcrição íntegra, resumo, tags e duração de cada arquivo.
- **Nos Bastidores**:
  - O sistema realiza consultas `LIKE` no MySQL combinando a busca com o `VectorStore` (algoritmo de distância por cosseno) para retornar resultados semanticamente alinhados.

---

### 📊 3. Aba: Dashboard & Estatísticas
- **Objetivo**: Visualizar métricas executivas agregadas da plataforma.
- **Como Usar**:
  1. Clique na aba **Dashboard & Estatísticas**.
  2. Clique no botão **"🔄 Atualizar Estatísticas"**.
  3. Veja os indicadores globais: total de áudios, horas acumuladas, total de palavras e tempo médio por áudio.
- **Nos Bastidores**:
  - O frontend consulta o endpoint GET `/api/stats` da API Node.js, executando queries `SUM`, `COUNT` e `AVG` no MySQL.

---

### 💬 4. Aba: Chat RAG com Áudio
- **Objetivo**: Fazer perguntas e obter respostas fundamentadas exclusivamente no texto de um áudio específico.
- **Como Usar**:
  1. Digite o nome do arquivo de áudio desejado (ex: `250704_001.mp3`).
  2. Digite sua pergunta no chat (ex: *"Quem ficou responsável pelo relatório?"*).
  3. Clique em **"Enviar"**.
- **Nos Bastidores**:
  - O sistema busca o texto da transcrição no MySQL e aplica RAG (*Retrieval-Augmented Generation*), garantindo que o Llama 3 responda baseado **estritamente** naquele áudio.

---

### 📥 5. Aba: Exportar Relatório
- **Objetivo**: Baixar relatórios individuais estilizados.
- **Como Usar**:
  1. Escolha o formato de saída: **TXT** (texto simples), **Markdown (.md)** (estruturado) ou **HTML estilizado** (design visual com CSS).
  2. Clique no botão de download para baixar o relatório formatado.

---

## 🧰 GUIA DE INSTALAÇÃO DE CADA TECNOLOGIA (PRÉ-REQUISITOS)

Antes de rodar a aplicação, certifique-se de ter as ferramentas instaladas. Abaixo estão os links e comandos oficiais para instalar cada uma:

### 1. 🐳 Docker & Docker Compose
Permite rodar todo o sistema pré-configurado sem instalar dependências manualmente.
- **Windows**: Baixe o [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) (necessita habilitar o recurso WSL2).
- **macOS**: Baixe o [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) (versão Apple Silicon M1/M2/M3 ou Intel).
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update && sudo apt install -y docker.io docker-compose-v2
  sudo usermod -aG docker $USER
  ```

### 2. 🐍 Python (versão 3.10 ou superior)
Linguagem utilizada para a interface Gradio, Whisper e módulos de IA.
- **Windows**: Baixe em [python.org/downloads](https://www.python.org/downloads/).
  > ⚠️ **Atenção**: Marque a caixa **"Add Python to PATH"** no início da instalação.
- **macOS**: `brew install python`
- **Linux**: `sudo apt install -y python3 python3-pip python3-venv`

### 3. 🟢 Node.js & NPM (versão 18 ou superior)
Runtime JavaScript utilizado para a API REST e conexão com o MySQL.
- **Windows / macOS**: Baixe a versão LTS em [nodejs.org](https://nodejs.org/).
- **Linux**: `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs`

### 4. 🐬 MySQL Server (versão 8.0 ou superior)
Banco de dados relacional que armazena os metadados, transcrições e tags.
- **Windows**: Baixe o [MySQL Community Installer](https://dev.mysql.com/downloads/installer/).
- **macOS**: `brew install mysql && brew services start mysql`
- **Linux**: `sudo apt install -y mysql-server && sudo systemctl enable --now mysql`

### 5. 🦙 Ollama & Llama 3
Servidor local de Inteligência Artificial para resumos e extração semântica.
- **Windows**: Baixe o instalador `OllamaSetup.exe` em [ollama.com/download/windows](https://ollama.com/download/windows).
- **macOS / Linux**:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```
- **Como baixar o modelo Llama 3**:
  Após instalar, execute no terminal/PowerShell:
  ```bash
  ollama run llama3
  ```

### 6. 🎞️ FFmpeg (Obrigatório)
Biblioteca essencial utilizada pelo Whisper para decodificar arquivos de áudio (`.mp3`, `.wav`, `.m4a`).
- **Windows**: `winget install --id=Gyan.FFmpeg` ou `choco install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install -y ffmpeg`

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

---

## 📜 Licença & Open Source

Este projeto é **Open Source** e está licenciado sob a **[MIT License](LICENSE)**.

Você é livre para usar, copiar, modificar, mesclar, publicar, distribuir, sublicenciar e/ou vender cópias deste software de forma totalmente gratuita e ilimitada.

