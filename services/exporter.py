import os
import json
import logging
from fpdf import FPDF

class AtaPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.set_text_color(31, 78, 121)
        self.cell(0, 10, 'ATA FORMAL DE REUNIÃO OPERACIONAL', border=False, align='C', new_x="LMARGIN", new_y="NEXT")
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, 'Documento Oficial de Registro de Sessao - Transcritor Inteligente v2.0 Enterprise', border=False, align='C', new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(31, 78, 121)
        self.set_line_width(0.5)
        self.line(10, 26, 200, 26)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}} | Documento Auditavel e Homologado', align='C')

def sanitize_pdf(text):
    if not text:
        return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

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

def exportar_pdf_ata_operacional(nome_arquivo, transcricao, resumo=None, meta=None):
    """
    Gera documento formal em PDF no formato Ata de Reunião Operacional pronta para impressão e assinatura.
    Retorna o caminho absoluto do arquivo PDF gerado.
    """
    pdf = AtaPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    meta_info = meta or {}
    data_sessao = meta_info.get("data_upload", "2026-07-28")
    duracao_seg = meta_info.get("duracao_segundos", 0)
    duracao_min = round(duracao_seg / 60, 1) if duracao_seg else "N/A"
    palavras = meta_info.get("quantidade_palavras", len(transcricao.split()))
    usuario = meta_info.get("usuario", "Sistema / Operacional")
    sha256_hash = meta_info.get("hash_sha256", "N/A")

    # 1. QUADRO DE CONTROLE DA REUNIÃO
    pdf.set_font("helvetica", "B", 11)
    pdf.set_fill_color(240, 244, 248)
    pdf.cell(0, 7, sanitize_pdf("1. CONTROLE E METADADOS DA REUNIÃO"), border=1, new_x="LMARGIN", new_y="NEXT", fill=True)
    
    pdf.set_font("helvetica", "", 9)
    pdf.cell(95, 6, sanitize_pdf(f" Arquivo Fonte: {nome_arquivo}"), border=1)
    pdf.cell(95, 6, sanitize_pdf(f" Data da Sessão: {data_sessao}"), border=1, new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(95, 6, sanitize_pdf(f" Duração Estimada: {duracao_min} minutos ({duracao_seg}s)"), border=1)
    pdf.cell(95, 6, sanitize_pdf(f" Total de Palavras: {palavras}"), border=1, new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(95, 6, sanitize_pdf(f" Responsável / Usuário: {usuario}"), border=1)
    pdf.cell(95, 6, sanitize_pdf(f" Hash de Integridade (SHA-256): {sha256_hash[:20]}..."), border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # 2. SÍNTESE EXECUTIVA E PAUTA (RESUMO COM IA)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_fill_color(240, 244, 248)
    pdf.cell(0, 7, sanitize_pdf("2. PAUTA E SÍNTESE EXECUTIVA DA SESSÃO"), border=1, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    
    resumo_texto = resumo or "Síntese automática não solicitada para esta sessão."
    pdf.multi_cell(0, 5, sanitize_pdf(resumo_texto), border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # 3. ENTIDADES IDENTIFICADAS (SE HOUVER)
    entidades_json = meta_info.get("entidades", {})
    if isinstance(entidades_json, str):
        try:
            entidades_json = json.loads(entidades_json)
        except Exception:
            entidades_json = {}

    if entidades_json and isinstance(entidades_json, dict):
        pdf.set_font("helvetica", "B", 11)
        pdf.set_fill_color(240, 244, 248)
        pdf.cell(0, 7, sanitize_pdf("3. ENTIDADES E ELEMENTOS DE CONTROLE IDENTIFICADOS (NER)"), border=1, new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_font("helvetica", "", 9)
        
        entidades_txt = []
        if entidades_json.get("pessoas"):
            entidades_txt.append(f"• Pessoas Mencionadas: {', '.join(entidades_json['pessoas'])}")
        if entidades_json.get("empresas"):
            entidades_txt.append(f"• Organizações/Empresas: {', '.join(entidades_json['empresas'])}")
        if entidades_json.get("datas"):
            entidades_txt.append(f"• Prazos e Datas: {', '.join(entidades_json['datas'])}")
        if entidades_json.get("valores"):
            entidades_txt.append(f"• Valores Mencionados: {', '.join(entidades_json['valores'])}")
        
        pdf.multi_cell(0, 5, sanitize_pdf("\n".join(entidades_txt) if entidades_txt else "Sem entidades específicas mapeadas."), border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

    # 4. TRANSCRIÇÃO ÍNTEGRA
    pdf.set_font("helvetica", "B", 11)
    pdf.set_fill_color(240, 244, 248)
    pdf.cell(0, 7, sanitize_pdf("4. REGISTRO ÍNTEGRO DA TRANSCRIÇÃO"), border=1, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_font("helvetica", "", 8.5)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 4.5, sanitize_pdf(transcricao), border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # 5. TERMO DE HOMOLOGAÇÃO E CAMPO PARA ASSINATURAS
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, sanitize_pdf("5. TERMO DE HOMOLOGAÇÃO E VISTO FORMAL"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "I", 8.5)
    pdf.multi_cell(0, 4, sanitize_pdf("Atesto que o presente documento reflete a transcrição autêntica do arquivo de áudio gravado e processado em conformidade com as diretrizes institucionais."))
    pdf.ln(12)

    # Linhas para Assinatura
    y_pos = pdf.get_y()
    pdf.set_line_width(0.3)
    pdf.line(15, y_pos, 90, y_pos)
    pdf.line(110, y_pos, 185, y_pos)
    
    pdf.set_font("helvetica", "B", 8)
    pdf.text(20, y_pos + 4, sanitize_pdf("ASSINATURA DO SECRETÁRIO / RESPONSÁVEL"))
    pdf.text(120, y_pos + 4, sanitize_pdf("DATA DE HOMOLOGAÇÃO E VISTO"))

    # Salva o arquivo PDF em uploads/
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    nome_pdf = f"Ata_Reuniao_{os.path.splitext(nome_arquivo)[0]}.pdf"
    caminho_pdf = os.path.join(uploads_dir, nome_pdf)
    
    pdf.output(caminho_pdf)
    logging.info(f"Ata PDF gerada com sucesso: {caminho_pdf}")
    return caminho_pdf
