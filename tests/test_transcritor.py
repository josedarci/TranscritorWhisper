import os
import sys
import unittest

# Adiciona raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.exporter import exportar_txt, exportar_markdown, exportar_html
from services.vector_store import VectorStore

class TestTranscritorServices(unittest.TestCase):

    def test_exporter_txt(self):
        nome = "audio_teste.mp3"
        texto = "Este é um teste de transcrição em áudio."
        resumo = "Resumo em teste."
        meta = {"quantidade_palavras": 8, "data_upload": "2026-07-28"}

        res = exportar_txt(nome, texto, resumo, meta)
        self.assertIn("RELATÓRIO DE TRANSCRIÇÃO", res)
        self.assertIn(texto, res)
        self.assertIn(resumo, res)

    def test_exporter_markdown(self):
        nome = "audio_teste.mp3"
        texto = "Texto para validação de formato markdown."
        resumo = "Tópico 1\nTópico 2"
        meta = {"quantidade_palavras": 6}

        res = exportar_markdown(nome, texto, resumo, meta)
        self.assertIn("# 🎙️ Relatório de Transcrição", res)
        self.assertIn(texto, res)

    def test_vector_store_index_and_search(self):
        vs = VectorStore()
        nome = "test_reuniao_azure.mp3"
        texto = "Nesta reunião discutimos a migração dos serviços para a nuvem da Azure e otimização de custos."

        vs.adicionar_transcricao(nome, texto)
        resultados = vs.buscar_semantica("Azure", top_k=1)

        self.assertTrue(len(resultados) > 0)
        self.assertEqual(resultados[0]["nome_arquivo"], nome)

if __name__ == "__main__":
    unittest.main()
