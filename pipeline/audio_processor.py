import os
import hashlib
import re

def calcular_hash_sha256(caminho_arquivo):
    """Calcula o Hash SHA-256 do arquivo de áudio para evitar re-transcrições redundantes (Cache SHA-256)."""
    if not caminho_arquivo or not os.path.exists(caminho_arquivo):
        return None
    
    hasher = hashlib.sha256()
    try:
        with open(caminho_arquivo, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

def aplicar_diarization_simulada(texto_transcrito):
    """
    Módulo de Speaker Diarization (Diferenciação de Oradores).
    Estrutura parágrafos alternados identificando os locutores [Orador 1], [Orador 2].
    """
    if not texto_transcrito:
        return texto_transcrito
    
    paragrafos = [p.strip() for p in re.split(r'\n\s*\n', texto_transcrito) if p.strip()]
    if len(paragrafos) <= 1:
        return texto_transcrito

    resultado = []
    for i, p in enumerate(paragrafos):
        orador = f"[Locutor {(i % 2) + 1}]"
        if not p.startswith("[Locutor"):
            resultado.append(f"🗣️ **{orador}**: {p}")
        else:
            resultado.append(p)
            
    return "\n\n".join(resultado)
