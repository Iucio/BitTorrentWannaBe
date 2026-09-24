import random, string
import Sessao
import socket

class Cliente:
    def __init__(self):

        self.peer_id = self._gerar_peer_id()
        self.servidor = self._gerar_servidor()
        self.host, self.porta = self.servidor.getsockname() 
        self.sessoes = {}

    # Método privado da classe
    def _gerar_peer_id(self): # Ainda não sei onde que vai ficar essa função.
        prefixo = "-UF0001-" # Identificao utilizada no protocolo, mas criei uma, pois é um trabalho de faculdade.
        randon_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=12))
        return prefixo + randon_bytes

    # Método privado da classe
    def _gerar_servidor(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip_local = socket.gethostbyname(socket.gethostname())
        server.bind((ip_local, 0)) # 0 fala para pegar qualquer porta disponível da máquina, ou seja, efêmera e aleatória.
        return server

    def adicionar_sessao(self, arquivo:dict):
        nova_sessao = Sessao.Sessao(arquivo, self.peer_id)
        self.sessoes[nova_sessao.info_hash] = nova_sessao
        return nova_sessao

    def get_sessoes(self):
        return self.sessoes