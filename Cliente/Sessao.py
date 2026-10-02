from servicos.info_hash import infhash
from servicos.url_encoder import url_encode
from servicos.request import request_tracker
from evento import Event
from servicos.p2p import handshake, parse_bitfield
import threading, math

class Sessao:
    def __init__(self, torrent, peer_id, uploaded=0, downloaded=0, left=0, event="started"):
        self.info_hash = infhash(torrent) # Extrai o info_hash do torrent
        self.tracker = torrent["announce"] # Endereço do Tracker
        self.private = torrent["private"] # Define se o arquivo é privado ou não
        self.torrent = torrent # Dicionário do .torrent 
        self.peer_id = peer_id # Identificador do nó na rede
        self.uploaded = uploaded # Quantos bytes foram compartilhados na rede pelo nó
        self.downloaded = downloaded # Quantos bytes o nó baixou da rede
        self.left = left # Quantos bytes faltam para baixar do arquivo espeficicado pelo info_hash
        self.event = event
        # Lista de peers daquele arquivo
        self.swarm = [] # Ex: [("19.75.87.9", 8000), ("11.123.43.6", 9080)]
        # Dados retornados pelo Tracker
        self.interval = 0
        self.min_interval = 0
        self.complete = 0
        self.incomplete = 0

    # Atualizar dados interos através da resposta do Tracker
    def atualizar_dados_tracker(self, dados_tracker:dict):
        self.interval = dados_tracker["interval"]
        self.min_interval = dados_tracker["min_interval"]
        self.complete = dados_tracker["complete"]
        self.incomplete = dados_tracker["incomplete"]
        self.event = Event.ACTIVE
        for peer in dados_tracker["peers"]:
            self.swarm.append(peer)

    def announce(self, porta, peer_id, event): # informações que ficam no Cliente
        url = url_encode(self, porta, peer_id, event)
        return request_tracker(url) # Dicionário contendo a resposta do Tracker 

    # Caminho do download -> LEECHER
    def download(self, socket):
        resposta_tracker = self.announce(self.porta, self.peer_id, self.event)
        self.atualizar_dados_tracker(resposta_tracker)
        qtd_pecas = math.ceil(self.torrent["info"]["length"] / self.torrent["info"]["piece length"]) # Arredonda pra cima caso seja quebrado
        map_peca_peer = {}

        for peer in self.swarm:
            bitfield = handshake(self.info_hash, peer, self.peer_id, socket)
            pecas_desejadas = parse_bitfield(bitfield, qtd_pecas)
            map_peca_peer.update({peer : pecas_desejadas}) # Mapeio quais peças cada peer que contatei têm. Depois posso pedir cada peça para um peer diferente, dependendo da disponibilidade

        # Depois desse for, tendo as peças mapeadas por peer. Só preciso mandar os requests para cada peer.
        # As peças que chegarem devem ser validadas usando a função validar_peca(indice:int, peca:bytes, pieces:campo pieces do .torrent)

    # Caminho do upload -> SEEDER
    def upload(self, socket):
        pass

    # Decide se vai ser upload ou download, além de outras coisas.
    def gerenciador_sessao(self, socket):
        if self.tipo == "seeder":
            retorno = self.upload(socket)
        else:
            retorno = self.download(socket)
        if retorno:
            print(retorno)

    # Envia event=stopped para o tracker, sinalizando a saída do nó da rede.
    def shutdown(self, porta, peer_id):
        return self.announce(self.info_hash, porta, peer_id, Event.STOPPED)