import random, string, socket, Sessao, threading as t
from servicos.request import request_tracker

class Cliente:
    def __init__(self):
        self.peer_id = self._gerar_peer_id()
        self.server = self._gerar_servidor()
        self.host, self.porta = self.server.getsockname()
        self.sessoes = {}
        self._interface()

    # Método privado da classe
    def _gerar_peer_id(self): # Ainda não sei onde que vai ficar essa função.
        prefixo = "-UF0001-" # Identificao utilizada no protocolo, mas criei uma, pois é um trabalho de faculdade.
        randon_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=12))
        return (prefixo + randon_bytes).encode("latin1")

    # Método privado da classe para instaciar o servidor para comunicações.
    def _gerar_servidor(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip_local = socket.gethostbyname(socket.gethostname())
        server.bind((ip_local, 0)) # 0 fala para pegar qualquer porta disponível da máquina, ou seja, efêmera e aleatória.
        return server

    # Salva a sessão por info_hash como chave de busca
    def instanciar_sessao(self, torrent):
        nova_sessao = Sessao.Sessao(torrent, self.peer_id)
        self.sessoes[nova_sessao.info_hash] = nova_sessao
        thread_sessao = t.Thread(target=nova_sessao.gerenciador_sessao, args=(self.server))
        return nova_sessao.info_hash # retorna o Identificador da sessao

    # Announce de uma sessao com o event atual dela. Retorna a resposta do Tracker
    def announce(self, info_hash):
        sessao = self.sessoes[info_hash]
        resposta = sessao.announce(self.porta, self.peer_id, sessao.event)
        sessao.atualizar_dados_tracker(resposta)
        return resposta

    def shutdown(self):
        print(f"\nDesligando...")
        for sessao in self.sessoes.values():
            sessao.shutdown(self.porta, self.peer_id)
        self.server.close() # Libera recursos

    def _interface(self):
        print(f"+-------------------+\n| BitTorrentWannaBe |\n+-------------------+")
             