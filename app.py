import whisper
import gradio as gr

# Carrega o modelo apenas uma vez
model = whisper.load_model("base")  # use "small", "medium", ou "large" se quiser mais precisão

def transcrever(audio):
    if audio is None:
        return "Nenhum áudio enviado."
    result = model.transcribe(audio, language="pt")
    return result["text"]

gr.Interface(
    fn=transcrever,
    
    inputs=gr.Audio(type="filepath", label="Envie seu áudio", format="mp3"),

    outputs=gr.Textbox(label="Transcrição"),
    title="Transcrição de Áudio com Whisper",
    description="Envie um arquivo de áudio (.mp3, .wav, etc.) e receba a transcrição em texto.",
    theme="default"
).launch()
