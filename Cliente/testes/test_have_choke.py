"""Testes de HAVE, CHOKE (lockdown) e do cálculo de left/downloaded pelo leecher.

Rodar de dentro da pasta Cliente:
    python -m unittest discover -s testes -v
"""

import json
import os
import shutil
import socket
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import Cliente as modulo_cliente
from Sessao import Sessao
from servicos.gerador_torrent import gerar_torrent
from servicos.mensagens import (
    Bitfield, Choke, ErroProtocolo, Handshake, Have, Interested, Piece, Request, Unchoke,
    bitfield_de_pecas, ler_handshake, ler_mensagem,
)
from servicos.torrent_reader import ler_torrent

TAM_PECA = 20000
N_PECAS = 8
TAMANHO = TAM_PECA * N_PECAS - 1234  # última peça menor, como num arquivo de verdade
CONTEUDO = os.urandom(TAMANHO)


# ---------------------------------------------------------------------------
# Apoio
# ---------------------------------------------------------------------------

class TrackerFalso:
    """Tracker HTTP mínimo (JSON, como o Cliente espera) que guarda os announces recebidos."""

    def __init__(self):
        self.announces = []
        self.swarm = {}
        tracker = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query, encoding="latin1").items()}
                tracker.announces.append(q)
                peers = tracker.swarm.setdefault(q["info_hash"], {})
                if q.get("event") == "stopped":
                    peers.pop(q["peer_id"], None)
                else:
                    peers[q["peer_id"]] = (self.client_address[0], int(q["port"]), int(q["left"]))
                corpo = json.dumps({
                    "interval": 5, "min_interval": 0,
                    "complete": sum(1 for p in peers.values() if p[2] == 0),
                    "incomplete": sum(1 for p in peers.values() if p[2] > 0),
                    "peers": [{"ip": p[0], "port": p[1]} for pid, p in peers.items() if pid != q["peer_id"]],
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(corpo)

        self.servidor = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.servidor.server_address[1]}"
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()

    def parar(self):
        self.servidor.shutdown()
        self.servidor.server_close()


def torrent_de_teste(pasta, tracker_url):
    arquivo = Path(pasta) / "origem.bin"
    arquivo.write_bytes(CONTEUDO)
    caminho_torrent = gerar_torrent(arquivo, tracker_url, TAM_PECA)
    return ler_torrent(caminho_torrent), arquivo


def sessao_seeder(pasta):
    torrent, arquivo = torrent_de_teste(pasta, "http://127.0.0.1:1")
    sessao = Sessao(torrent, b"-UF0001-seeder000000")
    sessao.carregar_arquivo(arquivo)
    return sessao


def _atender(sessao, conexao, peer_id):
    try:
        sessao.upload(conexao, peer_id)
    except (OSError, ErroProtocolo):  # o Cliente também ignora: o peer só fechou a conexão
        pass


def conectar_ao_seeder(sessao, peer_id=b"-UF0001-leecher00000"):
    """Liga um socket ao Sessao.upload(), como o Cliente faria. Retorna o lado do 'leecher'."""
    nosso, deles = socket.socketpair()
    nosso.settimeout(5)
    threading.Thread(target=_atender, args=(sessao, deles, peer_id), daemon=True).start()
    return nosso


# ---------------------------------------------------------------------------
# left e downloaded (calculados pelo leecher)
# ---------------------------------------------------------------------------

class TesteLeftDownloaded(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.pasta, True)
        torrent, _ = torrent_de_teste(self.pasta, "http://127.0.0.1:1")
        self.sessao = Sessao(torrent, b"-UF0001-leecher00000")

    def test_comeca_com_o_arquivo_todo_faltando(self):
        self.assertEqual(self.sessao.downloaded, 0)
        self.assertEqual(self.sessao.left, TAMANHO)

    def test_cada_peca_validada_atualiza_os_dois(self):
        self.sessao._peca_validada(0, CONTEUDO[:TAM_PECA])
        self.assertEqual(self.sessao.downloaded, TAM_PECA)
        self.assertEqual(self.sessao.left, TAMANHO - TAM_PECA)

    def test_peca_repetida_nao_conta_duas_vezes(self):
        self.sessao._peca_validada(0, CONTEUDO[:TAM_PECA])
        self.sessao._peca_validada(0, CONTEUDO[:TAM_PECA])
        self.assertEqual(self.sessao.downloaded, TAM_PECA)

    def test_sessao_completa_tem_left_zero_e_downloaded_do_tamanho_do_arquivo(self):
        for i in range(N_PECAS):
            self.sessao._peca_validada(i, CONTEUDO[i * TAM_PECA:(i + 1) * TAM_PECA])
        self.assertEqual(self.sessao.left, 0)
        self.assertEqual(self.sessao.downloaded, TAMANHO)


# ---------------------------------------------------------------------------
# HAVE e CHOKE na ponta que atende (Sessao.upload)
# ---------------------------------------------------------------------------

class TesteUploadChoke(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.pasta, True)
        self.seeder = sessao_seeder(self.pasta)
        self.peer = conectar_ao_seeder(self.seeder)
        self.addCleanup(self.peer.close)
        self.assertIsInstance(ler_mensagem(self.peer), Bitfield)

    def pedir(self, indice=0):
        self.peer.sendall(Request(indice, 0, 100).para_bytes())

    def test_sem_lockdown_responde_unchoke_e_atende(self):
        self.peer.sendall(Interested().para_bytes())
        self.assertIsInstance(ler_mensagem(self.peer), Unchoke)
        self.pedir()
        piece = ler_mensagem(self.peer)
        self.assertIsInstance(piece, Piece)
        self.assertEqual(piece.bloco, CONTEUDO[:100])

    def test_lockdown_antes_do_interested_responde_choke(self):
        self.seeder.bloquear(b"-UF0001-leecher00000")
        self.assertIsInstance(ler_mensagem(self.peer), Choke)  # o CHOKE chega sem ele pedir nada
        self.peer.sendall(Interested().para_bytes())
        self.assertIsInstance(ler_mensagem(self.peer), Choke)

    def test_lockdown_nega_o_request_com_choke_e_nao_manda_peca(self):
        self.peer.sendall(Interested().para_bytes())
        self.assertIsInstance(ler_mensagem(self.peer), Unchoke)
        self.seeder.bloquear("-UF0001-leecher00000")  # aceita str também
        self.assertIsInstance(ler_mensagem(self.peer), Choke)
        self.pedir()
        self.assertIsInstance(ler_mensagem(self.peer), Choke)  # e não um Piece
        self.assertEqual(self.seeder.uploaded, 0)

    def test_lockdown_so_vale_para_o_peer_bloqueado(self):
        self.seeder.bloquear(b"-UF0001-outro0000000")
        self.peer.sendall(Interested().para_bytes())
        self.assertIsInstance(ler_mensagem(self.peer), Unchoke)

    def test_desbloquear_manda_unchoke_e_volta_a_atender(self):
        self.seeder.bloquear(b"-UF0001-leecher00000")
        self.assertIsInstance(ler_mensagem(self.peer), Choke)
        self.seeder.desbloquear(b"-UF0001-leecher00000")
        self.assertIsInstance(ler_mensagem(self.peer), Unchoke)
        self.pedir()
        self.assertIsInstance(ler_mensagem(self.peer), Piece)

    def test_peers_conectados_mostra_o_peer_id(self):
        self.assertIn(b"-UF0001-leecher00000", self.seeder.peers_conectados())


# ---------------------------------------------------------------------------
# HAVE na ponta que atende
# ---------------------------------------------------------------------------

class TesteUploadHave(unittest.TestCase):
    def test_peca_validada_manda_have_para_quem_esta_conectado(self):
        pasta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, pasta, True)
        torrent, _ = torrent_de_teste(pasta, "http://127.0.0.1:1")
        leecher = Sessao(torrent, b"-UF0001-leecher00000")  # ainda sem nenhuma peça
        peer = conectar_ao_seeder(leecher, b"-UF0001-vizinho000000")
        self.addCleanup(peer.close)
        bitfield = ler_mensagem(peer)
        self.assertIsInstance(bitfield, Bitfield)
        self.assertEqual(bitfield.bits, bitfield_de_pecas([], N_PECAS))  # vazio

        leecher._peca_validada(3, CONTEUDO[3 * TAM_PECA:4 * TAM_PECA])
        self.assertEqual(ler_mensagem(peer), Have(3))

        # a peça já pode ser pedida a este nó (vira seeder dela)
        peer.sendall(Request(3, 0, 50).para_bytes())
        peer.sendall(Interested().para_bytes())
        self.assertEqual(ler_mensagem(peer).bloco, CONTEUDO[3 * TAM_PECA:3 * TAM_PECA + 50])

    def test_have_nao_e_enviado_duas_vezes_para_a_mesma_peca(self):
        pasta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, pasta, True)
        torrent, _ = torrent_de_teste(pasta, "http://127.0.0.1:1")
        leecher = Sessao(torrent, b"-UF0001-leecher00000")
        peer = conectar_ao_seeder(leecher)
        self.addCleanup(peer.close)
        ler_mensagem(peer)
        leecher._peca_validada(1, CONTEUDO[TAM_PECA:2 * TAM_PECA])
        leecher._peca_validada(1, CONTEUDO[TAM_PECA:2 * TAM_PECA])
        leecher._peca_validada(2, CONTEUDO[2 * TAM_PECA:3 * TAM_PECA])
        self.assertEqual(ler_mensagem(peer), Have(1))
        self.assertEqual(ler_mensagem(peer), Have(2))  # o segundo HAVE(1) não existiu


# ---------------------------------------------------------------------------
# Ponta a ponta: Clientes de verdade + Tracker falso
# ---------------------------------------------------------------------------

class SeederFalso(threading.Thread):
    """Seeder escrito na mão: atende `atendidas` peças e depois manda CHOKE e ignora tudo."""

    def __init__(self, atendidas):
        super().__init__(daemon=True)
        self.atendidas = atendidas
        self.servidas = 0
        self.servidor = socket.socket()
        self.servidor.bind(("127.0.0.1", 0))
        self.servidor.listen()
        self.porta = self.servidor.getsockname()[1]
        self.start()

    def run(self):
        conexao, _ = self.servidor.accept()
        ler_handshake(conexao)
        conexao.sendall(Bitfield(bitfield_de_pecas(range(N_PECAS), N_PECAS)).para_bytes())
        try:
            while True:
                msg = ler_mensagem(conexao)
                if isinstance(msg, Interested):
                    conexao.sendall(Unchoke().para_bytes())
                elif isinstance(msg, Request):
                    if self.servidas >= self.atendidas:
                        conexao.sendall(Choke().para_bytes())  # CHOKE no meio do download
                        continue
                    ini = msg.indice * TAM_PECA + msg.inicio
                    conexao.sendall(Piece(msg.indice, msg.inicio, CONTEUDO[ini:ini + msg.tamanho]).para_bytes())
                    if msg.inicio + msg.tamanho >= min(TAM_PECA, TAMANHO - msg.indice * TAM_PECA):
                        self.servidas += 1
        except OSError:
            pass


class TesteEndToEnd(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.pasta = tempfile.mkdtemp()
        self.tracker = TrackerFalso()
        self.clientes = []
        self.torrent, self.arquivo = torrent_de_teste(self.pasta, self.tracker.url)

        def limpar():
            os.chdir(self.cwd)
            for c in self.clientes:
                try:
                    c.shutdown()
                except Exception:
                    pass
            self.tracker.parar()
            shutil.rmtree(self.pasta, True)
        self.addCleanup(limpar)

    def novo_cliente(self):
        cliente = modulo_cliente.Cliente()
        self.clientes.append(cliente)
        return cliente

    def seeder(self):
        cliente = self.novo_cliente()
        cliente.instanciar_sessao(self.torrent, self.arquivo, self.tracker.url)
        return cliente

    def leecher(self, nome="l"):
        cliente = self.novo_cliente()
        pasta = os.path.join(self.pasta, nome)
        os.makedirs(pasta)
        os.chdir(pasta)  # o GerenciadorDownload grava arquivo_final.bin na pasta atual
        return cliente, cliente.instanciar_sessao(self.torrent, tracker=self.tracker.url), pasta

    def baixado(self, pasta):
        return (Path(pasta) / "arquivo_final.bin").read_bytes() == CONTEUDO

    def test_download_completo_fecha_left_zero_e_avisa_o_tracker(self):
        self.seeder()
        cliente, sessao, pasta = self.leecher()
        self.assertTrue(sessao.download(timeout_sem_progresso=10))
        self.assertEqual(sessao.left, 0)
        self.assertEqual(sessao.downloaded, TAMANHO)
        self.assertTrue(self.baixado(pasta))
        completos = [a for a in self.tracker.announces if a.get("event") == "completed"]
        self.assertEqual(len(completos), 1)
        self.assertEqual((completos[0]["left"], completos[0]["downloaded"]), ("0", str(TAMANHO)))

    def test_seeder_em_lockdown_nega_e_o_leecher_nao_baixa_nada(self):
        seeder = self.seeder()
        cliente, sessao, pasta = self.leecher()
        seeder.bloquear(cliente.peer_id)
        self.assertFalse(sessao.download(timeout_sem_progresso=2))
        self.assertEqual(sessao.downloaded, 0)
        self.assertEqual(sessao.left, TAMANHO)
        self.assertEqual(seeder.sessoes[sessao.info_hash].uploaded, 0)

    def test_com_dois_seeders_o_lockdown_de_um_nao_impede_o_download(self):
        bloqueador = self.seeder()
        self.seeder()
        cliente, sessao, pasta = self.leecher()
        bloqueador.bloquear(cliente.peer_id)
        self.assertTrue(sessao.download(timeout_sem_progresso=10))
        self.assertTrue(self.baixado(pasta))
        self.assertEqual((sessao.left, sessao.downloaded), (0, TAMANHO))

    def test_choke_no_meio_do_download_redistribui_as_pecas(self):
        falso = SeederFalso(atendidas=1)  # serve 1 peça e depois dá CHOKE
        self.seeder()
        cliente, sessao, pasta = self.leecher()
        sessao.add_peer_demo(("127.0.0.1", falso.porta))
        self.assertTrue(sessao.download(timeout_sem_progresso=10))
        self.assertTrue(self.baixado(pasta))
        self.assertEqual((sessao.left, sessao.downloaded), (0, TAMANHO))

    def test_leecher_que_terminou_vira_seeder_para_outro(self):
        seeder = self.seeder()
        _, sessao1, pasta1 = self.leecher("l1")
        self.assertTrue(sessao1.download(timeout_sem_progresso=10))
        seeder.shutdown()  # o seeder original sai da rede
        self.clientes.remove(seeder)

        _, sessao2, pasta2 = self.leecher("l2")
        sessao2.swarm = [s for s in sessao2.swarm if s[1] == self.clientes[0].porta]  # só o l1
        self.assertEqual(len(sessao2.swarm), 1)
        self.assertTrue(sessao2.download(timeout_sem_progresso=10))
        self.assertTrue(self.baixado(pasta2))


if __name__ == "__main__":
    unittest.main()
