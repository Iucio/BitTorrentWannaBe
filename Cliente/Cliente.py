import random, string, socket, Sessao, time, threading as t
from enum import StrEnum
from servicos.request import request_tracker

class Event(StrEnum):
    STARTED = "started" # Início da aplicação (primeiro announce)
    COMPLETED = "completed" # Download completo de um arquivo
    STOPPED = "stopped" # Término da aplicação (ultimo announce)
    # Sessao de donwload
    ACTIVE = "" # Omição do event na url. (Nenum arquivo foi baixado por completo e o cliente não saiu da rede) 
    # Sessao de Upload
    SEEDER = "seeder" 

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
        #nova_sessao.announce(self.porta, self.peer_id)
        return nova_sessao 

    def shutdown(self):
        self.event = Event.STOPPED
        for sessao in self.sessoes.values():
            sessao.shutdown(self.porta, self.peer_id)
        try:
            print(f"\nDesligando cliente...")
            self.server.shutdown(socket.SHUT_RDWR) # Finaliza a sessao
            time.sleep(5)
            self.server.close() # Libera recursos 
            time.sleep(5)
        except Exception as e:
            print()

    def _interface(self):
        print(f"+-------------------+\n| BitTorrentWannaBe |\n+-------------------+")
             