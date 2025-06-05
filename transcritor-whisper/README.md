# Transcritor Whisper

Este projeto é uma aplicação de transcrição de áudio que utiliza o modelo Whisper para converter arquivos de áudio em texto. A aplicação permite que os usuários enviem arquivos de áudio e recebam a transcrição correspondente.

## Estrutura do Projeto

```
transcritor-whisper/
├── backend/ # API Node.js que salva transcrições no MySQL
│ ├── server.js
│ ├── .env # Variáveis de ambiente (credenciais do banco)
│ └── package.json
├── src/
│ └── app.py # Interface Gradio com Whisper (frontend)
├── uploads/ # Onde os arquivos .mp3 são salvos localmente
├── requirements.txt # Dependências do Python
└── README.md # Documentação do projeto
```
Conteúdo sugerido de requirements.txt:
openai-whisper
gradio
requests

---
Também é necessário ter o FFmpeg instalado no sistema.
2. Instale o backend Node.js
cd backend
npm install
Crie o arquivo .env com as credenciais do banco:

## ✅ Pré-requisitos

- Python 3.7+
- Node.js 16+
- MySQL (instância rodando e acessível)

---

## ⚙️ Instalação

### 1. Instale as dependências do Python

```bash
pip install -r requirements.txt
```

## Instalação

Para instalar as dependências do projeto, você precisará do Python 3.7 ou superior. Você pode usar o `pip` para instalar as bibliotecas necessárias. Execute o seguinte comando no terminal:

```
pip install -r requirements.txt
```
🚀 Execução
1. Inicie o backend
cd backend
node server.js
A API estará disponível em http://localhost:3001/api/salvar.
2. Inicie o frontend (Gradio + Whisper)

cd src
python3 app.py

A interface abrirá em http://127.0.0.1:7860.

Uso
Acesse a interface no navegador.

Envie um arquivo de áudio no formato .mp3.

O áudio será salvo em ./uploads/.

A transcrição será exibida na tela e salva no banco de dados MySQL junto com o nome e caminho do arquivo.

🛠️ Banco de Dados
Crie a tabela transcricoes no seu MySQL com o seguinte comando:
```
CREATE TABLE transcricoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_arquivo VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL,
    texto LONGTEXT NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);


## Execução do Aplicativo

Após instalar as dependências, você pode executar o aplicativo de transcrição de áudio. Navegue até o diretório `src` e execute o seguinte comando:

```
python app.py
```

## Uso

1. Acesse a interface do aplicativo em seu navegador.
2. Envie um arquivo de áudio no formato `.mp3`, `.wav`, etc.
3. Aguarde a transcrição ser gerada e exibida na tela.

## Dependências

As principais bibliotecas utilizadas neste projeto são:

- `whisper`: Para a transcrição de áudio.
- `gradio`: Para a criação da interface do usuário.

📦 Dependências
Python
openai-whisper

gradio

requests

Node.js
express

mysql2

dotenv

cors

🙋 Contribuição
Contribuições são bem-vindas! Faça um fork do repositório, crie sua branch e envie um pull request com melhorias, correções ou novas funcionalidades.