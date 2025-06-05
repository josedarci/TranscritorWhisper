import whisper
import gradio as gr
import requests
import os
import uuid
import shutil

# Configurações da pasta pública e backend
UPLOADS_PUBLICAS = "/var/www/josedarci.com/uploads"
URL_BASE = "https://josedarci.com/uploads"
API_BACKEND = "http://localhost:3001/api/salvar"

# Garante que a pasta de uploads exista
os.makedirs(UPLOADS_PUBLICAS, exist_ok=True)

# Carrega o modelo Whisper uma vez
model = whisper.load_model("base")

def transcrever(audio_path):
    if audio_path is None:
        return "Nenhum áudio enviado."

    # Gera nome único para o arquivo
    nome_arquivo = f"{uuid.uuid4().hex}.mp3"
    caminho_destino = os.path.join(UPLOADS_PUBLICAS, nome_arquivo)

    # Copia o arquivo para a pasta pública
    shutil.copy(audio_path, caminho_destino)

    # Transcreve o áudio
    result = model.transcribe(caminho_destino, language="pt")
    texto = result["text"]

    # Monta a URL pública
    url_publica = f"{URL_BASE}/{nome_arquivo}"

    # Envia para o backend Node
    try:
        requests.post(API_BACKEND, json={
            "nome_arquivo": nome_arquivo,
            "url": url_publica,
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
    description="O áudio será salvo em josedarci.com/uploads e a transcrição armazenada no banco."
).launch()
