import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.erros import ErroServico
from services.ia import gemini, vetores
from services.ia import sugestao


# Servidor falso que imita o Gemini
class FalsoGemini(BaseHTTPRequestHandler):
    resposta = (200, {})
    recebidos = []

    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length", 0))
        FalsoGemini.recebidos.append(
            {"caminho": self.path, "chave": self.headers.get("x-goog-api-key"),
             "corpo": json.loads(self.rfile.read(tamanho))}
        )
        codigo, corpo = FalsoGemini.resposta
        dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(dados)

    def log_message(self, *args):
        pass


def texto_gemini(texto):
    return {"candidates": [{"content": {"parts": [{"text": texto}]}}]}


class TestCliente(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(("127.0.0.1", 0), FalsoGemini)
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.servidor.server_port}/v1beta"

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()

    def setUp(self):
        FalsoGemini.recebidos = []
        self.ambiente = mock.patch.dict(os.environ, {
            "GEMINI_API_KEY": "chave-secreta", "GEMINI_URL_BASE": self.url,
            "GEMINI_MODELO": "m1", "GEMINI_MODELO_EMBEDDING": "e1",
            "NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1",
        })
        self.ambiente.start()

    def tearDown(self):
        self.ambiente.stop()

    def test_json_normal_e_requisicao(self):
        FalsoGemini.resposta = (200, texto_gemini('{"categoria": "A"}'))
        self.assertEqual(gemini.gerar_json("instr", "texto"), {"categoria": "A"})
        r = FalsoGemini.recebidos[0]
        self.assertEqual(r["chave"], "chave-secreta")
        self.assertTrue(r["caminho"].endswith("/models/m1:generateContent"))
        self.assertEqual(r["corpo"]["generationConfig"]["responseMimeType"], "application/json")

    def test_json_dentro_de_cerca_e_com_lixo(self):
        FalsoGemini.resposta = (200, texto_gemini('```json\n{"a": 1}\n```'))
        self.assertEqual(gemini.gerar_json("i", "t"), {"a": 1})
        FalsoGemini.resposta = (200, texto_gemini('Claro! {"a": 2} pronto'))
        self.assertEqual(gemini.gerar_json("i", "t"), {"a": 2})

    def test_resposta_ruim(self):
        for corpo in ({}, {"candidates": []}, texto_gemini("nada de json"), texto_gemini("[1,2]")):
            FalsoGemini.resposta = (200, corpo)
            with self.assertRaises(ErroServico) as ctx:
                gemini.gerar_json("i", "t")
            self.assertEqual(ctx.exception.status, 502)

    def test_erros_http(self):
        casos = {401: 502, 403: 502, 404: 502, 429: 429, 500: 502, 503: 502}
        for codigo, esperado in casos.items():
            FalsoGemini.resposta = (codigo, {"error": {"message": "chave-secreta vazou"}})
            with self.assertRaises(ErroServico) as ctx:
                gemini.gerar_json("i", "t")
            self.assertEqual(ctx.exception.status, esperado)
            self.assertNotIn("chave-secreta", ctx.exception.mensagem)

    def test_sem_chave(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            with self.assertRaises(ErroServico) as ctx:
                gemini.gerar_json("i", "t")
            self.assertEqual(ctx.exception.status, 503)

    def test_servidor_fora_do_ar(self):
        with mock.patch.dict(os.environ, {"GEMINI_URL_BASE": "http://127.0.0.1:1/v1beta"}):
            with self.assertRaises(ErroServico) as ctx:
                gemini.gerar_json("i", "t")
            self.assertEqual(ctx.exception.status, 502)

    def test_embedding(self):
        FalsoGemini.resposta = (200, {"embedding": {"values": [0.1, 0.2, 0.3]}})
        self.assertEqual(gemini.gerar_embedding("oi", "RETRIEVAL_QUERY"), [0.1, 0.2, 0.3])
        r = FalsoGemini.recebidos[0]
        self.assertTrue(r["caminho"].endswith("/models/e1:embedContent"))
        self.assertEqual(r["corpo"]["taskType"], "RETRIEVAL_QUERY")
        self.assertEqual(r["corpo"]["outputDimensionality"], 768)

    def test_embedding_invalido(self):
        for corpo in ({}, {"embedding": {"values": []}}, {"embedding": {"values": ["x"]}}):
            FalsoGemini.resposta = (200, corpo)
            with self.assertRaises(ErroServico):
                gemini.gerar_embedding("oi", "RETRIEVAL_QUERY")


class TestSugestao(unittest.TestCase):
    CATS = ["Finanças", "Estudos"]
    CAMINHOS = [("Documentos",), ("Documentos", "2024")]

    def test_reaproveita_nomes_existentes(self):
        r = sugestao.interpretar(
            {"categoria": "financas", "pasta": ["documentos", "2024"], "motivo": "m"},
            self.CATS, self.CAMINHOS)
        self.assertEqual(r, {"categoria": "Finanças", "pasta": "Documentos / 2024", "motivo": "m"})

    def test_cria_novos_e_limpa(self):
        r = sugestao.interpretar(
            {"categoria": " Viagens\n", "pasta": ["Documentos", "A/B\\C"], "motivo": "x" * 500},
            self.CATS, self.CAMINHOS)
        self.assertEqual(r["categoria"], "Viagens")
        self.assertEqual(r["pasta"], "Documentos / A B C")
        self.assertEqual(len(r["motivo"]), sugestao.MAX_MOTIVO)

    def test_limites(self):
        r = sugestao.interpretar({"categoria": "x" * 300, "pasta": [str(i) for i in range(20)]}, [], [])
        self.assertEqual(len(r["categoria"]), 100)
        self.assertEqual(len(sugestao.niveis_da_pasta(r["pasta"])), sugestao.MAX_NIVEIS)

    def test_pasta_como_texto_e_tipos_errados(self):
        r = sugestao.interpretar({"categoria": 5, "pasta": "A > B", "motivo": None}, [], [])
        self.assertEqual(r, {"categoria": None, "pasta": "A / B", "motivo": ""})

    def test_vazio_vira_none(self):
        self.assertIsNone(sugestao.interpretar({"categoria": None, "pasta": []}, [], []))
        self.assertIsNone(sugestao.interpretar([], [], []))

    def test_prompt_limita_texto(self):
        texto = sugestao.montar_texto("a.txt", "arquivo", "x" * 50000, self.CATS, self.CAMINHOS)
        self.assertLess(len(texto), 7000)
        self.assertIn("Documentos / 2024", texto)


class TestVetores(unittest.TestCase):
    def test_cosseno_e_ranking(self):
        self.assertAlmostEqual(vetores.cosseno([1, 0], [2, 0]), 1.0)
        self.assertAlmostEqual(vetores.cosseno([1, 0], [0, 1]), 0.0)
        self.assertEqual(vetores.cosseno([1], [1, 2]), 0.0)
        itens = [{"id": 1, "vetor": [0, 1]}, {"id": 2, "vetor": [1, 0.1]}, {"id": 3, "vetor": [1, 1]}]
        r = vetores.ranquear([1, 0], itens, 0.5, 10)
        self.assertEqual([i for i, _ in r], [2, 3])
        self.assertEqual(len(vetores.ranquear([1, 0], itens, 0.0, 1)), 1)

    def test_serializacao(self):
        self.assertEqual(vetores.ler(vetores.serializar([0.5, 1])), [0.5, 1.0])
        self.assertIsNone(vetores.ler("lixo"))


if __name__ == "__main__":
    unittest.main()
