import random, string, socket, Sessao, time, threading as t
from enum import StrEnum
from servicos.url_encoder import url_encode
from servicos.request import request

class Event(StrEnum):
    STARTED = "started" # Início da aplicação (primeiro announce)
    COMPLETED = "completed" # Download completo de um arquivo
    STOPPED = "stopped" # Término da aplicação (ultimo announce)
    ACTIVE = "" # Omição do event na url. (Nenum arquivo foi baixado por completo e o cliente não saiu da rede)

class Cliente:
    def __init__(self):
        self.peer_id = self._gerar_peer_id()
        self.servidor = self._gerar_servidor()
        self.host, self.porta = self.servidor.getsockname()
        self.event = Event.STARTED
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

    # Salva a sessão por info_hash como chave de busca
    def adicionar_sessao(self, arquivo:dict):
        nova_sessao = Sessao.Sessao(arquivo)
        self.sessoes[nova_sessao.info_hash] = nova_sessao
        thread = t.Thread(target=self._ativar_sessao, args=nova_sessao)
        return nova_sessao.info_hash # retorna o Identificador da sessao

    # Requisição ao Tracker
    # Falta enviar pra rede (urllib3) e receber respostas
    def announce(self, info_hash): 
        url = url_encode(self.sessoes[info_hash], self.porta, self.peer_id, self.event)
        # resposta = request(url)
        self.event = Event.ACTIVE
        
        return url # apenas para demonstração

    def _ativar_sessao(self, sessao:Sessao):
        while sessao.event != Event.STOPPED:
            
            pass

    def shutdown(self):
        self.event = Event.STOPPED
        for sessao in self.sessoes.keys():
            self.announce(sessao)
        try:
            print(f"\nDesligando...")
            self.servidor.shutdown(socket.SHUT_RDWR) # Finaliza a sessao
            time.sleep(5)
            self.servidor.close() # Libera recursos 
            time.sleep(5)
        except Exception as e:
            print()