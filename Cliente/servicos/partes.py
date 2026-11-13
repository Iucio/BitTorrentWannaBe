"""
Partes da chave (Shamir) pela rede

Todo cliente pode ser guardião, mas só vira guardião de um arquivo quando o
seeder o escolhe no announce. Aí guarda a parte e só entrega pra quem o Tracker
diz que está no swarm do arquivo.
Seeder e leecher usam as funções do fim pra entregar e pedir as partes.
"""

import hashlib, socket, threading
from urllib.parse import urlencode

from servicos.mensagens import ErroProtocolo, GuardarParte, Handshake, Parte, PedirParte, ler_mensagem
from servicos.request import request_tracker

# Swarm de todos os clientes ligados. Não é de arquivo nenhum: é onde o seeder vê
# quem pode escolher e onde o Tracker acha o endereço atual de cada um
SALA = hashlib.sha1(b"BitTorrentWannaBe sala").digest()


def consultar(tracker, rota, info_hash, chave):
    """GET /peers ou /guardioes. Lista de {peer_id, ip, port}, vazia se o Tracker recusar."""
    resposta = request_tracker(f"{tracker}/{rota}?" + urlencode({"info_hash": info_hash, "chave": chave}))
    return resposta.get("peers", resposta.get("guardioes", []))


def _esta_em(lista, peer_id, ip):
    return any(p["peer_id"] == peer_id.decode("latin1") and p["ip"] == ip for p in lista)


class Guardiao:
    def __init__(self, cliente, tracker):
        self.cliente = cliente # peer_id, porta e chave
        self.tracker = tracker
        self.partes = {} # info_hash -> (x, y). Só na memória: o peer_id muda a cada execução
        self.lock = threading.Lock()

    # Entra (ou sai, com stopped) da SALA
    def anunciar(self, evento=""):
        params = {"info_hash": SALA, "peer_id": self.cliente.peer_id, "port": self.cliente.porta,
                  "left": 0, "chave": self.cliente.chave}
        if evento:
            params["event"] = evento
        return request_tracker(f"{self.tracker}/announce?" + urlencode(params), False)

    # Única regra de quem recebe a parte. Regras personalizadas entram aqui
    def pode_entregar(self, info_hash, peer_id, ip):
        return _esta_em(consultar(self.tracker, "peers", info_hash, self.cliente.chave), peer_id, ip)

    # Conexão com o bit de partes ligado no handshake
    def atender(self, conexao, handshake, ip):
        info_hash, peer_id = handshake.info_hash, handshake.peer_id
        try:
            mensagem = ler_mensagem(conexao)
            if isinstance(mensagem, GuardarParte):
                parte = (mensagem.x, mensagem.y)
                if self._guardar(info_hash, peer_id, ip, parte):
                    conexao.sendall(Parte(*parte).para_bytes()) # confirma devolvendo a parte
                    print(f"[Guardião] guardando parte de {info_hash.hex()[:8]}")
            elif isinstance(mensagem, PedirParte):
                parte = self.partes.get(info_hash)
                if parte and self.pode_entregar(info_hash, peer_id, ip):
                    conexao.sendall(Parte(*parte).para_bytes())
                    print(f"[Guardião] parte de {info_hash.hex()[:8]} entregue para {ip}")
            # Recusa ou mensagem de outro tipo: fecha sem responder
        finally:
            conexao.close()

    # Só guarda se quem manda está no swarm e o dono do arquivo me escolheu.
    # Parte que já existe não é trocada, só confirmada se for a mesma
    def _guardar(self, info_hash, peer_id, ip, parte):
        chave = self.cliente.chave
        if not _esta_em(consultar(self.tracker, "peers", info_hash, chave), peer_id, ip):
            return False
        guardioes = consultar(self.tracker, "guardioes", info_hash, chave)
        if not any(g["peer_id"] == self.cliente.peer_id.decode("latin1") for g in guardioes):
            return False
        with self.lock:
            return self.partes.setdefault(info_hash, parte) == parte


def _conectar(endereco, info_hash, peer_id):
    sock = socket.create_connection(endereco, timeout=5)
    sock.sendall(Handshake(info_hash, peer_id, partes=True).para_bytes())
    return sock


def entregar_parte(endereco, info_hash, peer_id, parte):
    """Seeder: manda a parte pro guardião. True se ele confirmou com a mesma parte."""
    try:
        with _conectar(endereco, info_hash, peer_id) as sock:
            sock.sendall(GuardarParte(*parte).para_bytes())
            resposta = ler_mensagem(sock)
        return isinstance(resposta, Parte) and (resposta.x, resposta.y) == tuple(parte)
    except (OSError, ErroProtocolo):
        return False


def pedir_parte(endereco, info_hash, peer_id):
    """Leecher: pede a parte que o guardião guarda. None se ele recusar ou não tiver."""
    try:
        with _conectar(endereco, info_hash, peer_id) as sock:
            sock.sendall(PedirParte().para_bytes())
            resposta = ler_mensagem(sock)
        return (resposta.x, resposta.y) if isinstance(resposta, Parte) else None
    except (OSError, ErroProtocolo):
        return None
