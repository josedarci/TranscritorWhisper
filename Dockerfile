FROM python:3.12-slim

WORKDIR /app

# Instala ffmpeg e dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY transcritor-whisper/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir openai-whisper gradio requests

COPY . .

EXPOSE 7860

CMD ["python3", "app.py"]
