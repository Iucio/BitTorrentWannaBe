import unittest
import urllib.request
import urllib.error
import urllib.parse

class TestTrackerHTTP(unittest.TestCase):
    
    # O C++ de vocês está configurado para a porta 80 por padrão
    TRACKER_URL = "http://localhost:80/announce"

    # 2.1.3 Testes de rejeição de cliente não autorizado
    def test_rejeicao_cliente_nao_autorizado(self):
        # Simula um cliente com info_hash inválido ou não cadastrado no tracker.db
        params = {
            "info_hash": "hash_invalido_ou_nao_autorizado",
            "peer_id": "-PC0001-cliente_falso",
            "port": 6881,
            "uploaded": 0,
            "downloaded": 0,
            "left": 1000,
            "event": "started"
        }
        query_string = urllib.parse.urlencode(params)
        url = f"{self.TRACKER_URL}?{query_string}"
        
        try:
            resposta = urllib.request.urlopen(url)
            conteudo = resposta.read()
            # O protocolo BitTorrent retorna "failure reason" em bencode caso recuse
            self.assertIn(b'failure reason', conteudo.lower())
        except urllib.error.HTTPError as e:
            # Se o C++ de vocês rejeitar direto com código de erro HTTP (ex: 400, 403)
            self.assertIn(e.code, [400, 401, 403, 404])
        except urllib.error.URLError:
            # Pula o teste se o servidor C++ não estiver rodando (ex: no GitHub Actions)
            self.skipTest("Servidor Tracker C++ não está rodando no localhost:80")

    # 2.2.3 Testes do announce request
    def test_announce_request_valido(self):
        # Simula um announce válido
        params = {
            "info_hash": "hash_valido_teste123", # Para testes locais futuros, colocar um hash do tracker.db
            "peer_id": "-PC0001-cliente_real",
            "port": 6881,
            "uploaded": 0,
            "downloaded": 0,
            "left": 1024,
            "event": "started"
        }
        query_string = urllib.parse.urlencode(params)
        url = f"{self.TRACKER_URL}?{query_string}"
        
        try:
            resposta = urllib.request.urlopen(url)
            conteudo = resposta.read()
            # Deve retornar HTTP 200 e a lista de peers no formato Bencode
            self.assertEqual(resposta.getcode(), 200)
            self.assertIn(b'peers', conteudo) 
        except urllib.error.HTTPError as e:
            self.fail(f"Tracker rejeitou um announce válido com erro HTTP {e.code}")
        except urllib.error.URLError:
            self.skipTest("Servidor Tracker C++ não está rodando no localhost:80")

if __name__ == '__main__':
    unittest.main()
