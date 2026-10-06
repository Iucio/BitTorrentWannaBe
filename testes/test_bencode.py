import unittest
import sys
import os

# Adiciona a raiz do projeto ao caminho
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa todas as funcoes necessarias do vosso parser
from Cliente.servicos.parser import bencode, encoder, encode_list, encode_dict 

class TestBencode(unittest.TestCase):
    
    # 1.2.1 Testes de decodificação
    def test_decodificacao_inteiro(self):
        self.assertEqual(bencode('i42e'), ([42], 4))
        self.assertEqual(bencode('i-42e'), ([-42], 5))

    def test_decodificacao_string(self):
        self.assertEqual(bencode('4:spam'), (['spam'], 6))

    def test_decodificacao_lista(self):
        self.assertEqual(bencode('l4:spami42ee'), ([['spam', 42]], 12))

    def test_decodificacao_dicionario(self):
        self.assertEqual(bencode('d3:bar4:spam3:fooi42ee'), ([{'bar': 'spam', 'foo': 42}], 22))

    # 1.2.2 Testes de codificação (tipos primitivos, lista e dicionário)
    def test_codificacao_inteiro_e_string(self):
        self.assertEqual(encoder(42), 'i42e')
        self.assertEqual(encoder('spam'), '4:spam')

    def test_codificacao_lista(self):
        self.assertEqual(encode_list(['spam', 42]), 'l4:spami42ee')

    def test_codificacao_dicionario(self):
        dados = {'bar': 'spam', 'foo': 42}
        self.assertEqual(encode_dict(dados), 'd3:bar4:spam3:fooi42ee')

    # 1.2.3 Testes de casos de borda
    def test_borda_estruturas_vazias(self):
        # Estes testes vao falhar (IndexError), o que e bom: expoe o bug no parser do Felipe.
        self.assertEqual(bencode('le')[0], [[]]) 
        self.assertEqual(bencode('de')[0], [{}])
        self.assertEqual(bencode('0:')[0], ['']) # String vazia

    def test_borda_aninhamento_profundo(self):
        # Lista dentro de dicionário
        self.assertEqual(encode_dict({'lista': [1, 2]}), 'd5:listali1ei2eee')

    def test_borda_strings_binarias_pieces(self):
        # Testa se a codificacao lida com bytes brutos convertendo para a chave pieces
        # O proprio parser tem uma tratativa de .encode("latin1") no metodo principal
        # Validamos se a chave "pieces" e aceita e encodada
        dados = {'info': {'pieces': 'bytes_brutos_simulados'}}
        self.assertEqual(encode_dict(dados), 'd4:infod6:pieces22:bytes_brutos_simuladosee')

if __name__ == '__main__':
    unittest.main()
