import threading, time, math, progressbar
from servicos.info_hash import infhash
from servicos.url_encoder import url_encode
from servicos.request import request_tracker
from GerenciadorDownload import GerenciadorDownload
from servicos.p2p import fragmentar_arquivo
from servicos.mensagens import Bitfield, Unchoke, Interested, Request, Piece, bitfield_de_pecas, ler_mensagem
from servicos.evento import Event

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

    def add_peer_demo(self, peer):
        self.swarm.append(peer)

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

        
    # Seeder: lê o arquivo e guarda só as peças que batem com o hash do .torrent
    def carregar_arquivo(self, caminho):
        info = self.torrent["info"]
        self.pecas = fragmentar_arquivo(caminho, info["piece length"])
        self.left = info["length"] - sum(len(peca) for peca in self.pecas.values())

    # Caminho do upload -> SEEDER. O peer já mandou o handshake dele
    def upload(self, conexao):
        bitfield = Bitfield(bitfield_de_pecas(self.pecas, self.qtd_pecas))
        conexao.sendall(bitfield.para_bytes()) # Avisa quais peças tem
        while True: # Até o peer desconectar
            mensagem = ler_mensagem(conexao)

            if isinstance(mensagem, Request):
                bloco = self._bloco(mensagem)
                print(f"[Seeder] Mandando peca {mensagem.indice}")
                conexao.sendall(bloco.para_bytes())
            # Libera os pedidos
            elif isinstance(mensagem, Interested):
                print("[Seeder] Mandando unchoke...")
                conexao.sendall(Unchoke().para_bytes())

    # Recorta o bloco pedido. Pedido fora da peça derruba a conexão
    def _bloco(self, pedido):
        peca = self.pecas.get(pedido.indice)
        self.uploaded += pedido.tamanho
        return Piece(pedido.indice, pedido.inicio, peca[pedido.inicio:pedido.inicio + pedido.tamanho])

    # Envia event=stopped para o tracker, sinalizando o término da sessao
    def shutdown(self, porta, peer_id):
        print(f"[BitTorrentWannaBe] DESLIGANDO SESSAO...  {self.event}")
        #return self.announce(self.info_hash, porta, peer_id, "stopped")