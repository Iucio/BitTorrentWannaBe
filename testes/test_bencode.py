import unittest
import sys
import os

# Adiciona a raiz do projeto ao caminho
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Cliente.servicos.parser import bencode, encoder, encode_list, encode_dict

class TestBencode(unittest.TestCase):

    # 1.2.1 Testes de decodificação
    # bencode(texto) devolve o valor já decodificado
    def test_decodificacao_inteiro(self):
        self.assertEqual(bencode('i42e'), 42)
        self.assertEqual(bencode('i-42e'), -42)
        self.assertEqual(bencode('i0e'), 0)

    def test_decodificacao_string(self):
        self.assertEqual(bencode('4:spam'), 'spam')

    def test_decodificacao_lista(self):
        self.assertEqual(bencode('l4:spami42ee'), ['spam', 42])

    def test_decodificacao_dicionario(self):
        self.assertEqual(bencode('d3:bar4:spam3:fooi42ee'), {'bar': 'spam', 'foo': 42})

    # 1.2.2 Testes de codificação
    def test_codificacao_inteiro_e_string(self):
        self.assertEqual(encoder(42), 'i42e')
        self.assertEqual(encoder(-42), 'i-42e')
        self.assertEqual(encoder('spam'), '4:spam')

    def test_codificacao_lista(self):
        self.assertEqual(encode_list(['spam', 42]), 'l4:spami42ee')

    def test_codificacao_dicionario(self):
        self.assertEqual(bencode({'bar': 'spam', 'foo': 42}), 'd3:bar4:spam3:fooi42ee')

    # 1.2.3 Testes de casos de borda
    def test_borda_estruturas_vazias(self):
        # Falha hoje: o parser quebra com lista vazia e string vazia (IndexError).
        # O teste está certo; quem precisa de correção é o parser.
        self.assertEqual(bencode('de'), {})
        self.assertEqual(bencode('le'), [])
        self.assertEqual(bencode('0:'), '')

    def test_borda_aninhamento(self):
        # codificar e decodificar estruturas dentro de estruturas
        self.assertEqual(encode_dict({'lista': [1, 2]}), 'd5:listali1ei2eee')
        self.assertEqual(bencode('d5:listali1ei2eee'), {'lista': [1, 2]})
        self.assertEqual(bencode('d1:ad1:bl1:ceee'), {'a': {'b': ['c']}})

    def test_borda_string_binaria_pieces(self):
        # O campo pieces tem bytes de 0 a 255 (hashes SHA-1). O parser trabalha com
        # texto latin1, em que cada caractere é exatamente um byte.
        pieces = bytes(range(256)).decode('latin1')
        codificado = encode_dict({'info': {'pieces': pieces}})
        self.assertTrue(codificado.startswith('d4:infod6:pieces256:'))
        # ao decodificar, o parser devolve pieces como bytes
        self.assertEqual(bencode(codificado)['info']['pieces'], bytes(range(256)))


if __name__ == '__main__':
    unittest.main()
