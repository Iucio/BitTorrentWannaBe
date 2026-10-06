import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa a funcao exata que voce me mandou
from Cliente.servicos.url_encoder import url_encode

# Criamos uma Sessao falsa (Mock) apenas para injetar dados no teste
class MockSessao:
    def __init__(self):
        self.tracker = "http://localhost:6969"
        self.info_hash = b'\x12\x34\x56\x78\x9a\xbc\xde\xf0\x12\x34\x56\x78\x9a\xbc\xde\xf0\x12\x34\x56\x78'
        self.uploaded = 0
        self.downloaded = 0
        self.left = 1024
        self.private = 0

class TestTrackerCliente(unittest.TestCase):
    
    # 2.1.3 Testes de rejeição de cliente não autorizado
    @unittest.skip("Aguardando a implementacao da issue 2.1.2 (Autorizacao ainda nao existe no Tracker)")
    def test_rejeicao_cliente_nao_autorizado(self):
        import urllib.request
        import urllib.error
        import urllib.parse
        
        TRACKER_URL = "http://localhost:6969/announce" 
        
        # Info_hash e peer_id com EXATAMENTE 20 bytes para passar na validacao de tamanho
        params = {
            "info_hash": "a" * 20, 
            "peer_id": "b" * 20,
            "port": 6881,
            "uploaded": 0,
            "downloaded": 0,
            "left": 1000,
            "event": "started"
        }
        query_string = urllib.parse.urlencode(params)
        url = f"{TRACKER_URL}?{query_string}"
        
        try:
            resposta = urllib.request.urlopen(url)
            conteudo = resposta.read().decode('utf-8')
            self.fail("O Tracker deveria ter recusado a conexao, mas aceitou.")
        except urllib.error.HTTPError as e:
            conteudo_erro = e.read().decode('utf-8')
            # Tracker responde em JSON com a chave failure_reason
            self.assertIn("failure_reason", conteudo_erro) 
        except urllib.error.URLError:
            self.fail("Servidor Tracker C++ precisa estar rodando na porta 6969 para este teste")

    # 2.2.3 Testes do announce request (Valida o modulo url_encoder.py do Cliente)
    def test_announce_request_montagem_url(self):
        # Prepara os dados simulados
        sessao_falsa = MockSessao()
        peer_id = "-PC0001-123456789012"
        porta = 6881
        evento = "started"
        
        # Chama a funcao real do seu grupo
        url_gerada = url_encode(sessao_falsa, porta, peer_id, evento)
        
        # Verifica se a string gerada comeca corretamente com o endereco do tracker
        self.assertTrue(url_gerada.startswith("http://localhost:6969/announce?"))
        
        # Verifica se os parametros estao presentes na URL gerada
        self.assertIn(f"peer_id={peer_id}", url_gerada)
        self.assertIn(f"port={porta}", url_gerada)
        self.assertIn("event=started", url_gerada)
        self.assertIn("uploaded=0", url_gerada)
        self.assertIn("left=1024", url_gerada)
        self.assertIn("private=0", url_gerada)

if __name__ == '__main__':
    unittest.main()
