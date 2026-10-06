"""Testes das mensagens do Peer Wire Protocol (tarefas 1.3.1 a 1.3.3).

Rodar de dentro da pasta Cliente:
    python -m unittest discover -s testes -v
"""

import socket
import threading
import unittest

from servicos.mensagens import (
    TAMANHO_HANDSHAKE, Bitfield, Choke, ErroProtocolo, Handshake, Have, Interested,
    NotInterested, Piece, Request, Unchoke, bitfield_de_pecas, decodificar,
    decodificar_handshake, ler_handshake, ler_mensagem, pecas_do_bitfield, recv_exato,
)

INFO_HASH = bytes(range(20))
PEER_ID = "-UF0001-abcdefghijkl"


def ida_e_volta(mensagem):
    """Monta os bytes e lê de volta (sem os 4 bytes de tamanho)."""
    return decodificar(mensagem.para_bytes()[4:])


class TesteHandshake(unittest.TestCase):
    def test_tem_68_bytes_no_formato_do_protocolo(self):
        dados = Handshake(INFO_HASH, PEER_ID).para_bytes()
        self.assertEqual(len(dados), TAMANHO_HANDSHAKE)
        self.assertEqual(dados[0], 19)
        self.assertEqual(dados[1:20], b"BitTorrent protocol")
        self.assertEqual(dados[20:28], bytes(8))
        self.assertEqual(dados[28:48], INFO_HASH)
        self.assertEqual(dados[48:68], PEER_ID.encode())

    def test_ida_e_volta(self):
        original = Handshake(INFO_HASH, PEER_ID)
        self.assertEqual(decodificar_handshake(original.para_bytes()), original)

    def test_peer_id_em_str_ou_bytes_da_no_mesmo(self):
        self.assertEqual(Handshake(INFO_HASH, PEER_ID), Handshake(INFO_HASH, PEER_ID.encode()))

    def test_rejeita_tamanhos_errados(self):
        with self.assertRaises(ValueError):
            Handshake(INFO_HASH[:19], PEER_ID)
        with self.assertRaises(ValueError):
            Handshake(INFO_HASH, "curto")
        with self.assertRaises(ErroProtocolo):
            decodificar_handshake(Handshake(INFO_HASH, PEER_ID).para_bytes()[:-1])

    def test_rejeita_outro_protocolo(self):
        dados = bytearray(Handshake(INFO_HASH, PEER_ID).para_bytes())
        dados[1:20] = b"OutroProtocolo12345"
        with self.assertRaises(ErroProtocolo):
            decodificar_handshake(bytes(dados))


class TesteBytesExatos(unittest.TestCase):
    """Confere byte a byte contra o formato da especificação."""

    def test_mensagens_sem_conteudo(self):
        self.assertEqual(Choke().para_bytes(), bytes.fromhex("00000001 00"))
        self.assertEqual(Unchoke().para_bytes(), bytes.fromhex("00000001 01"))
        self.assertEqual(Interested().para_bytes(), bytes.fromhex("00000001 02"))
        self.assertEqual(NotInterested().para_bytes(), bytes.fromhex("00000001 03"))

    def test_have(self):
        self.assertEqual(Have(3).para_bytes(), bytes.fromhex("00000005 04 00000003"))

    def test_request(self):
        self.assertEqual(Request(0, 0, 12).para_bytes(),
                         bytes.fromhex("0000000d 06 00000000 00000000 0000000c"))

    def test_piece(self):
        self.assertEqual(Piece(1, 16384, b"oi").para_bytes(),
                         bytes.fromhex("0000000b 07 00000001 00004000") + b"oi")


class TesteIdaEVolta(unittest.TestCase):
    """Tarefa 1.3.3: montar e ler de volta tem que dar a mesma mensagem."""

    def test_todas_as_mensagens(self):
        exemplos = [
            Choke(), Unchoke(), Interested(), NotInterested(),
            Have(0), Have(2**32 - 1),
            Bitfield(bytes.fromhex("c040")),
            Request(7, 32768, 16384),
            Piece(7, 32768, bytes(range(256)) * 64),
            Piece(0, 0, b""),
        ]
        for mensagem in exemplos:
            with self.subTest(mensagem=type(mensagem).__name__):
                self.assertEqual(ida_e_volta(mensagem), mensagem)

    def test_conteudo_com_tamanho_errado(self):
        for conteudo in [b"\x00\x00", b"\x04\x00\x00\x00", b"\x06" + bytes(11), b"\x07" + bytes(7)]:
            with self.subTest(conteudo=conteudo.hex()):
                with self.assertRaises(ErroProtocolo):
                    decodificar(conteudo)

    def test_id_desconhecido_ou_mensagem_vazia(self):
        for conteudo in [b"\x14", b""]:
            with self.subTest(conteudo=conteudo.hex()):
                with self.assertRaises(ErroProtocolo):
                    decodificar(conteudo)


class TesteBitfield(unittest.TestCase):
    def test_exemplo_da_explicacao(self):
        # peças 0, 1 e 9 de 10 → 11000000 01000000
        self.assertEqual(bitfield_de_pecas({0, 1, 9}, 10), bytes.fromhex("c040"))
        self.assertEqual(pecas_do_bitfield(bytes.fromhex("c040"), 10), {0, 1, 9})

    def test_bordas(self):
        self.assertEqual(bitfield_de_pecas([], 8), b"\x00")
        self.assertEqual(bitfield_de_pecas(range(8), 8), b"\xff")
        self.assertEqual(bitfield_de_pecas([8], 9), b"\x00\x80")
        self.assertEqual(bitfield_de_pecas([0], 1), b"\x80")

    def test_ida_e_volta_pela_mensagem(self):
        pecas = {0, 3, 7, 8, 15, 16, 22}
        recebido = ida_e_volta(Bitfield(bitfield_de_pecas(pecas, 23)))
        self.assertEqual(pecas_do_bitfield(recebido.bits, 23), pecas)

    def test_rejeita_tamanho_errado(self):
        with self.assertRaises(ErroProtocolo):
            pecas_do_bitfield(b"\xff", 9)  # 9 peças precisam de 2 bytes

    def test_rejeita_bits_de_sobra_ligados(self):
        with self.assertRaises(ErroProtocolo):
            pecas_do_bitfield(b"\xc1", 7)  # bit da "peça 7", que não existe

    def test_rejeita_peca_fora_do_arquivo_ao_montar(self):
        with self.assertRaises(ValueError):
            bitfield_de_pecas([10], 10)


class TesteSocket(unittest.TestCase):
    """Leitura de verdade, com um par de sockets conectados."""

    def setUp(self):
        self.a, self.b = socket.socketpair()
        self.a.settimeout(5)
        self.b.settimeout(5)

    def tearDown(self):
        self.a.close()
        self.b.close()

    def test_recv_exato_junta_pedacos(self):
        def enviar_aos_poucos():
            for byte in b"abcdefgh":
                self.a.sendall(bytes([byte]))

        t = threading.Thread(target=enviar_aos_poucos)
        t.start()
        self.assertEqual(recv_exato(self.b, 8), b"abcdefgh")
        t.join()

    def test_mensagem_chegando_picada(self):
        dados = Piece(2, 0, b"x" * 1000).para_bytes() + Have(5).para_bytes()

        def enviar_aos_poucos():
            for i in range(0, len(dados), 7):
                self.a.sendall(dados[i:i + 7])

        t = threading.Thread(target=enviar_aos_poucos)
        t.start()
        self.assertEqual(ler_mensagem(self.b), Piece(2, 0, b"x" * 1000))
        self.assertEqual(ler_mensagem(self.b), Have(5))
        t.join()

    def test_varias_mensagens_coladas(self):
        self.a.sendall(Interested().para_bytes() + Unchoke().para_bytes())
        self.assertEqual(ler_mensagem(self.b), Interested())
        self.assertEqual(ler_mensagem(self.b), Unchoke())

    def test_handshake_pelo_socket(self):
        self.a.sendall(Handshake(INFO_HASH, PEER_ID).para_bytes())
        self.assertEqual(ler_handshake(self.b), Handshake(INFO_HASH, PEER_ID))

    def test_conexao_fechada_no_meio_da_mensagem(self):
        self.a.sendall(Request(0, 0, 10).para_bytes()[:9])
        self.a.close()
        with self.assertRaises(ConnectionError):
            ler_mensagem(self.b)


if __name__ == "__main__":
    unittest.main()
