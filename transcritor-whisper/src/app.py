import whisper
import gradio as gr
import requests
import os
import uuid
import shutil

# Caminhos para uso local
UPLOADS_PUBLICAS = os.path.join(os.getcwd(), "uploads")
API_BACKEND = "http://localhost:3001/api/salvar"

# Garante que a pasta exista
os.makedirs(UPLOADS_PUBLICAS, exist_ok=True)

# Carrega modelo Whisper
model = whisper.load_model("base")

def transcrever(audio_path):
    if audio_path is None:
        return "Nenhum áudio enviado."

    # Gera nome único para o .mp3
    nome_arquivo = f"{uuid.uuid4().hex}.mp3"
    destino = os.path.join(UPLOADS_PUBLICAS, nome_arquivo)

    # Copia o arquivo para ./uploads/
    shutil.copy(audio_path, destino)

    # Transcreve
    result = model.transcribe(destino, language="pt")
    texto = result["text"]

    # Monta "URL" local fictícia
    url_local = f"uploads/{nome_arquivo}"

    # Envia para o backend
    try:
        requests.post(API_BACKEND, json={
            "nome_arquivo": nome_arquivo,
            "url": url_local,
            "texto": texto
        })
    except Exception as e:
        print("Erro ao enviar para o backend:", e)

    return texto

# Interface Gradio
gr.Interface(
    fn=transcrever,
    inputs=gr.Audio(type="filepath", label="Envie seu áudio (.mp3)", format="mp3"),
    outputs=gr.Textbox(label="Transcrição"),
    title="Transcrição de Áudio com Whisper",
    description="Salva o áudio localmente em ./uploads e armazena a transcrição no banco de dados."
).launch()
