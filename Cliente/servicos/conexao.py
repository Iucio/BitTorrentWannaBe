import threading


class ConexaoPeer:
    """Um socket TCP com outro peer, com envio seguro entre threads.

    Várias threads podem querer escrever no mesmo socket ao mesmo tempo (ex.: a thread que
    responde um REQUEST e a que avisa um HAVE). Sem o lock, os bytes das duas mensagens se
    misturariam no meio do caminho e o outro lado leria lixo.

    `peer_id` é o do peer do outro lado (bytes). Fica None quando não sabemos (conexões que
    nós abrimos: o handshake que recebemos de volta não traz o peer_id do seeder).
    """

    def __init__(self, sock, peer_id=None):
        self.sock = sock
        self.peer_id = peer_id
        self._lock = threading.Lock()

    def enviar(self, mensagem):
        """`mensagem` é qualquer objeto de servicos.mensagens (Have, Choke, Piece...)."""
        with self._lock:
            self.sock.sendall(mensagem.para_bytes())
