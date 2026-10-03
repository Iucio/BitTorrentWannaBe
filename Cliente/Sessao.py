import threading, socket as s, time, math, progressbar
from servicos.info_hash import infhash
from servicos.url_encoder import url_encode
from servicos.request import request_tracker
from servicos.mensagens import (
    TAMANHO_HANDSHAKE, Bitfield, Choke, ErroProtocolo, Handshake, Have, Interested,
    NotInterested, Piece, Request, Unchoke, bitfield_de_pecas, ler_handshake, ler_mensagem, pecas_do_bitfield,
)
from GerenciadorDownload import GerenciadorDownload

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
        self.swarm = [("127.0.0.1", 6881)] # Ex: [("19.75.87.9", 8000), ("11.123.43.6", 9080)]
        # Dados retornados pelo Tracker
        self.interval = 0
        self.min_interval = 0
        self.complete = 0
        self.incomplete = 0

    # Atualizar dados interos através da resposta do Tracker
    def _atualizar_dados_tracker(self, dados_tracker:dict):
        self.interval = dados_tracker["interval"]
        self.min_interval = dados_tracker["min_interval"]
        self.complete = dados_tracker["complete"]
        self.incomplete = dados_tracker["incomplete"]
        self.event = "" # Omite o campo event nas próximas requisições o tracker
        for peer in dados_tracker["peer_list"]:
            self.swarm.append(peer)

    def announce(self, porta, peer_id, event): # informações que ficam no Cliente
        url = url_encode(self.info_hash, porta, peer_id, event)
        dados_tracker = request_tracker(url) # Dicionário contendo a resposta do Tracker 
        self._atualizar_dados_tracker(dados_tracker)

    # Caminho do download -> LEECHER
    def download(self):
        
        gerenciador = GerenciadorDownload(self.torrent["info"], self.info_hash, self.peer_id, self.swarm)
        gerenciador.instanciar_mini_leechers(self.swarm)
        time.sleep(3)

        thread_orquestador = threading.Thread(target=gerenciador.orquestrador, daemon=True)
        thread_orquestador.start()

        barra = progressbar.ProgressBar(max_value=gerenciador.total_pecas)
        while len(gerenciador.pecas_baixadas) < gerenciador.total_pecas:
            barra.update(len(gerenciador.pecas_baixadas))
            time.sleep(0.25)

        barra.finish()
        print(f"\n DOWNLOAD CONCLUÍDO COM SUCESSO!")
        self.event = "completed"

        
    # Caminho do upload -> SEEDER
    def upload(self, socket):
        pass

    # Envia event=stopped para o tracker, sinalizando o término da sessao
    def shutdown(self, porta, peer_id):
        print(f"DESLIGANDO SESSAO...  {self.event}")
        #return self.announce(self.info_hash, porta, peer_id, "stopped")