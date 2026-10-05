import unittest

# IMPORTANTE: Substitua "seu_modulo_tracker" pelo nome correto do arquivo do seu Tracker no projeto
import seu_modulo_tracker as tracker 

class TestTracker(unittest.TestCase):
    
    # 2.1.3 Testes de rejeição de cliente não autorizado
    def test_rejeicao_cliente_nao_autorizado(self):
        # Simulação de um cliente a tentar ligar-se com credenciais erradas ou sem registo
        dados_invalidos = {"peer_id": "cliente_desconhecido", "info_hash": "invalido"}
        
        # Substitua "processar_requisicao" pela função real do seu Tracker
        resposta = tracker.processar_requisicao(dados_invalidos) 
        
        # Verifica se o Tracker recusa a ligação corretamente
        self.assertEqual(resposta.get('status'), 'erro')
        self.assertIn('rejeitado', resposta.get('mensagem', '').lower())

    # 2.2.3 Testes do announce request
    def test_announce_request_valido(self):
        # Simulação de um announce request correto que um cliente enviaria
        dados_announce = {
            "peer_id": "-PC0001-123456789012",
            "port": 6881,
            "uploaded": 0,
            "downloaded": 0,
            "left": 1024,
            "event": "started"
        }
        
        # Substitua "processar_announce" pela função real do seu Tracker
        resposta = tracker.processar_announce(dados_announce)
        
        # Verifica se o Tracker responde com sucesso e devolve a lista de peers
        self.assertEqual(resposta.get('status'), 'sucesso')
        self.assertIn('peers', resposta)

if __name__ == '__main__':
    unittest.main()
