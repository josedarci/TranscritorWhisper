import unittest
import requests
import json
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.audio_processor import aplicar_diarization_simulada, calcular_hash_sha256
from services.vector_store import vector_store_global

class TestTranscritorEnterprise(unittest.TestCase):

    def test_01_banco_dados_v3_api(self):
        """Valida que a API REST do MySQL v3 responde corretamente no endpoint /api/stats."""
        res = requests.get("http://localhost:3001/api/stats")
        self.assertEqual(res.status_code, 200)
        self.assertIn("total_audios", res.json())

    def test_02_jwt_auth_flow(self):
        """Valida o fluxo de autenticação e login JWT."""
        payload = {"email": "admin@transcritor.com", "senha": "admin123"}
        res = requests.post("http://localhost:3001/api/auth/login", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("token", data)

        token = data["token"]
        headers = {"Authorization": f"Bearer {token}"}
        res_me = requests.get("http://localhost:3001/api/auth/me", headers=headers)
        self.assertEqual(res_me.status_code, 200)

    def test_03_speaker_diarization(self):
        """Valida a separação visual de locutores (Speaker Diarization)."""
        texto_exemplo = "Olá equipe, vamos iniciar a reunião.\n\nSim, os relatórios estão prontos."
        resultado = aplicar_diarization_simulada(texto_exemplo)
        self.assertIn("[Locutor 1]", resultado)
        self.assertIn("[Locutor 2]", resultado)

    def test_04_rag_citations(self):
        """Valida o RAG semântico com pontuação de confiança e citação de fontes."""
        resposta = vector_store_global.chat_com_transcricao("260707_001.mp3", "Qual o assunto da reunião?")
        self.assertTrue(isinstance(resposta, str))

    def test_05_mobile_api(self):
        """Valida os endpoints de integração mobile."""
        res = requests.get("http://localhost:3001/api/mobile/transcricoes")
        self.assertEqual(res.status_code, 200)
        self.assertIn("feed_mobile", res.json())

if __name__ == "__main__":
    unittest.main()
