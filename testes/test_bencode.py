import unittest
import sys
import os

# Adiciona a raiz do projeto ao caminho para conseguir importar a pasta Cliente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa a função bencode do ficheiro parser da vossa equipa
from Cliente.servicos.parser import bencode 

class TestBencode(unittest.TestCase):
    
    # 1.2.1 Testes de decodificação
    def test_decodificacao_inteiro(self):
        self.assertEqual(bencode('i42e'), 42)
        self.assertEqual(bencode('i-42e'), -42)

    def test_decodificacao_string(self):
        self.assertEqual(bencode('4:spam'), 'spam')

    def test_decodificacao_lista(self):
        self.assertEqual(bencode('l4:spami42ee'), ['spam', 42])

    def test_decodificacao_dicionario(self):
        self.assertEqual(bencode('d3:bar4:spam3:fooi42ee'), {'bar': 'spam', 'foo': 42})

    # 1.2.2 Testes de codificação (dicionário -> bencode)
    def test_codificacao_dicionario(self):
        dados = {'bar': 'spam', 'foo': 42}
        self.assertEqual(bencode(dados), 'd3:bar4:spam3:fooi42ee')

    # 1.2.3 Testes de casos de borda
    def test_borda_estruturas_vazias(self):
        self.assertEqual(bencode('le'), []) # lista vazia
        self.assertEqual(bencode('de'), {}) # dicionário vazio
        self.assertEqual(bencode({}), 'de')

if __name__ == '__main__':
    unittest.main()
