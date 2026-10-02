from servicos.info_hash import infhash
from servicos.url_encoder import url_encode
from servicos.request import request_tracker
from evento import Event
from servicos.p2p import handshake, parse_bitfield, fragmentar_arquivo, validar_peca
from servicos.mensagens import Handshake, Bitfield, Unchoke, Interested, Request, Piece, ErroProtocolo, TAMANHO_BLOCO, bitfield_de_pecas, ler_mensagem
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
        self.qtd_pecas = math.ceil(torrent["info"]["length"] / torrent["info"]["piece length"]) # Arredonda pra cima caso seja quebrado
        self.pecas = {} # Peças que este nó já tem: indice -> bytes
        # Lista de peers daquele arquivo
        self.swarm = [] # Ex: [("19.75.87.9", 8000), ("11.123.43.6", 9080)]
        # Dados retornados pelo Tracker
        self.interval = 0
        self.min_interval = 0
        self.complete = 0
        self.incomplete = 0

    # Atualizar dados interos através da resposta do Tracker
    def atualizar_dados_tracker(self, dados_tracker:dict):
        if "failure_reason" in dados_tracker: # Tracker recusou o announce, nada muda
            return
        self.interval = dados_tracker["interval"]
        self.min_interval = dados_tracker["min_interval"]
        self.complete = dados_tracker["complete"]
        self.incomplete = dados_tracker["incomplete"]
        self.event = Event.ACTIVE
        for peer in dados_tracker["peers"]:
            self.swarm.append(peer)

    def announce(self, porta, peer_id, event): # informações que ficam no Cliente
        url = url_encode(self, porta, peer_id, event)
        print(f"Requisição ao Tracker:\n{url}") # Mostra todo announce, inclusive o stopped do shutdown
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

    # Seeder: lê o arquivo e guarda só as peças que batem com o hash do .torrent
    def carregar_arquivo(self, caminho):
        info = self.torrent["info"]
        for indice, peca in fragmentar_arquivo(caminho, info["piece length"]).items():
            if validar_peca(indice, peca, info["pieces"]):
                self.pecas[indice] = peca
        self.left = info["length"] - sum(len(peca) for peca in self.pecas.values())

    # Caminho do upload -> SEEDER. O peer já mandou o handshake dele
    def upload(self, conexao):
        conexao.sendall(Handshake(self.info_hash, self.peer_id).para_bytes())
        conexao.sendall(Bitfield(bitfield_de_pecas(self.pecas, self.qtd_pecas)).para_bytes()) # Avisa quais peças tem
        while True: # Até o peer desconectar
            mensagem = ler_mensagem(conexao)
            if isinstance(mensagem, Interested):
                conexao.sendall(Unchoke().para_bytes()) # Libera os pedidos
            elif isinstance(mensagem, Request):
                conexao.sendall(self._bloco(mensagem).para_bytes())

    # Recorta o bloco pedido. Pedido fora da peça derruba a conexão
    def _bloco(self, pedido):
        peca = self.pecas.get(pedido.indice)
        if peca is None or pedido.tamanho > TAMANHO_BLOCO or pedido.inicio + pedido.tamanho > len(peca):
            raise ErroProtocolo(f"pedido invalido: {pedido}")
        self.uploaded += pedido.tamanho
        return Piece(pedido.indice, pedido.inicio, peca[pedido.inicio:pedido.inicio + pedido.tamanho])

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
        return self.announce(porta, peer_id, Event.STOPPED)