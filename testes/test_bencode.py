import unittest

# IMPORTANTE: Altere "seu_modulo_bencode" para o nome correto do arquivo bencode que vocês criaram no projeto.
import seu_modulo_bencode as bencode 

class TestBencode(unittest.TestCase):
    
    # 1.2.1 Testes de decodificação
    def test_decodificacao_inteiro(self):
        self.assertEqual(bencode.decode(b'i42e'), 42)
        self.assertEqual(bencode.decode(b'i-42e'), -42)

    def test_decodificacao_string(self):
        self.assertEqual(bencode.decode(b'4:spam'), b'spam')

    def test_decodificacao_lista(self):
        self.assertEqual(bencode.decode(b'l4:spami42ee'), [b'spam', 42])

    def test_decodificacao_dicionario(self):
        self.assertEqual(bencode.decode(b'd3:bar4:spam3:fooi42ee'), {b'bar': b'spam', b'foo': 42})

    # 1.2.2 Testes de codificação (dicionário -> bencode)
    def test_codificacao_dicionario(self):
        dados = {b'bar': b'spam', b'foo': 42}
        self.assertEqual(bencode.encode(dados), b'd3:bar4:spam3:fooi42ee')

    # 1.2.3 Testes de casos de borda
    def test_borda_estruturas_vazias(self):
        self.assertEqual(bencode.decode(b'le'), []) # lista vazia
        self.assertEqual(bencode.decode(b'de'), {}) # dicionário vazio
        self.assertEqual(bencode.encode({}), b'de')

if __name__ == '__main__':
    unittest.main()
