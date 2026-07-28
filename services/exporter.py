import os
import json

def exportar_txt(nome_arquivo, transcricao, resumo=None, meta=None):
    """Gera exportação em formato TXT simples."""
    conteudo = [
        f"==================================================",
        f" RELATÓRIO DE TRANSCRIÇÃO: {nome_arquivo}",
        f"==================================================\n",
        f"METADADOS:",
        f"• Data: {meta.get('data_upload', 'N/A') if meta else 'N/A'}",
        f"• Duração: {meta.get('duracao_segundos', 0) if meta else 0}s",
        f"• Palavras: {meta.get('quantidade_palavras', 0) if meta else 0}",
        f"• Usuário: {meta.get('usuario', 'sistema') if meta else 'sistema'}\n",
        f"--------------------------------------------------",
        f"RESUMO COM IA:",
        f"--------------------------------------------------",
        f"{resumo or 'Sem resumo'}\n",
        f"--------------------------------------------------",
        f"TRANSCRIÇÃO COMPLETA:",
        f"--------------------------------------------------",
        f"{transcricao}\n"
    ]
    return "\n".join(conteudo)

def exportar_markdown(nome_arquivo, transcricao, resumo=None, meta=None):
    """Gera exportação em formato Markdown (.md)."""
    conteudo = [
        f"# 🎙️ Relatório de Transcrição: `{nome_arquivo}`\n",
        f"## 📋 Metadados do Processamento",
        f"- **Data de Upload**: `{meta.get('data_upload', 'N/A') if meta else 'N/A'}`",
        f"- **Tempo de Processamento**: `{meta.get('tempo_total', 0) if meta else 0}s`",
        f"- **Total de Palavras**: `{meta.get('quantidade_palavras', 0) if meta else 0}`",
        f"- **Modelo Whisper**: `{meta.get('modelo_whisper', 'base') if meta else 'base'}`",
        f"- **Modelo Ollama**: `{meta.get('modelo_llama', 'llama3') if meta else 'llama3'}`\n",
        f"## 🤖 Resumo com Inteligência Artificial",
        f"{resumo or '*Nenhum resumo gerado.*'}\n",
        f"## 📄 Transcrição Íntegra",
        f"```text\n{transcricao}\n```"
    ]
    return "\n".join(conteudo)

def exportar_html(nome_arquivo, transcricao, resumo=None, meta=None):
    """Gera exportação em formato HTML estilizado."""
    resumo_html = (resumo or "Sem resumo").replace("\n", "<br>")
    transcricao_html = transcricao.replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatório - {nome_arquivo}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; color: #1a202c; background: #f7fafc; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        h1 {{ color: #2b6cb0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
        h2 {{ color: #2d3748; margin-top: 30px; }}
        .meta-card {{ background: #ebf8ff; border-left: 4px solid #3182ce; padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .section-box {{ background: #f7fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Relatório: {nome_arquivo}</h1>
        <div class="meta-card">
            <strong>Data:</strong> {meta.get('data_upload', 'N/A') if meta else 'N/A'} |
            <strong>Palavras:</strong> {meta.get('quantidade_palavras', 0) if meta else 0} |
            <strong>Tempo Total:</strong> {meta.get('tempo_total', 0) if meta else 0}s
        </div>
        <h2>🤖 Resumo Inteligente (IA)</h2>
        <div class="section-box">{resumo_html}</div>
        <h2>📄 Transcrição Completa</h2>
        <div class="section-box">{transcricao_html}</div>
    </div>
</body>
</html>"""
