import threading, time, math, progressbar
from servicos.info_hash import infhash
from servicos.url_encoder import url_encode
from servicos.request import request_tracker
from GerenciadorDownload import GerenciadorDownload
from servicos.p2p import fragmentar_arquivo
from servicos.conexao import ConexaoPeer
from servicos.mensagens import (
    Bitfield, Choke, ErroProtocolo, Have, Interested, Piece, Request, Unchoke,
    bitfield_de_pecas, ler_mensagem,
)
from servicos.evento import Event

class Sessao:
    def __init__(self, torrent, peer_id, uploaded=0, downloaded=0, left=None, event="started"):
        self.info_hash = infhash(torrent) # Extrai o info_hash do torrent
        self.tracker = torrent["announce"] # Endereço do Tracker
        self.private = torrent["private"] # Define se o arquivo é privado ou não
        self.torrent = torrent # Dicionário do .torrent 
        self.peer_id = peer_id # Identificador do nó na rede
        self.uploaded = uploaded # Quantos bytes foram compartilhados na rede pelo nó
        self.downloaded = downloaded # Bytes baixados E validados (SHA-1). Calculado por este cliente (leecher)
        # Quantos bytes faltam para completar o arquivo (tamanho - downloaded). Também calculado pelo cliente.
        # Começa com o arquivo todo e diminui a cada peça validada (ver _peca_validada).
        
        if left is None:
            self.left = torrent["info"]["length"] 
        else:
            self.left = left
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

        # HAVE e CHOKE
        self.lock = threading.RLock() # Protege pecas, downloaded, left, conexoes_upload e bloqueados
        self.conexoes_upload = [] # ConexaoPeer dos peers que se conectaram em nós (a gente é o seeder deles)
        self.bloqueados = set() # peer_ids (bytes) em lockdown: o upload pra eles é negado com CHOKE
        self.gerenciador = None # GerenciadorDownload da sessão, só existe depois de download()
        self.ao_completar = None # Função chamada quando o download termina (o Cliente usa pra avisar o Tracker)

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
            self.swarm.append((peer["ip"], peer["port"]))

    def announce(self, porta, peer_id, event): # informações que ficam no Cliente
        url = url_encode(self, porta, peer_id, event)
        return request_tracker(url) # Dicionário contendo a resposta do Tracker

    # Caminho do download -> LEECHER
    # Retorna True se baixou o arquivo todo. Retorna False se ficou `timeout_sem_progresso` segundos
    # sem validar nenhuma peça nova (ex.: todos os seeders deram CHOKE nesse leecher)
    def download(self, timeout_sem_progresso=60):
        gerenciador = GerenciadorDownload(self.torrent["info"], self.info_hash, self.peer_id, self.swarm,
                                          ao_validar=self._peca_validada)
        self.gerenciador = gerenciador
        gerenciador.instanciar_mini_leechers(self.swarm)
        thread_orquestador = threading.Thread(target=gerenciador.orquestrador, daemon=True)
        thread_orquestador.start()
        
        barra = progressbar.ProgressBar(max_value=gerenciador.total_pecas)
        baixadas = 0
        ultimo_progresso = time.time()
        while baixadas < gerenciador.total_pecas:
            atual = len(gerenciador.pecas_baixadas)
            if atual != baixadas:
                baixadas = atual
                ultimo_progresso = time.time()
            elif time.time() - ultimo_progresso > timeout_sem_progresso:
                gerenciador.parar()
                print(f"\n DOWNLOAD PARADO: {baixadas}/{gerenciador.total_pecas} peças, nenhum peer está enviando.")
                return False
            barra.update(baixadas)
            time.sleep(0.25)

        barra.finish()
        gerenciador.parar() # Fecha as conexões que abrimos
        print(f"\n DOWNLOAD CONCLUÍDO COM SUCESSO! left={self.left} downloaded={self.downloaded}")
        self.event = Event.COMPLETED
        if self.ao_completar:
            self.ao_completar() # announce event=completed, já com left=0 e downloaded=tamanho do arquivo
        return True

    # Chamado pelo GerenciadorDownload toda vez que uma peça é baixada E validada pelo hash.
    # É aqui que o leecher calcula downloaded e left, e avisa os vizinhos com HAVE.
    def _peca_validada(self, indice, peca):
        with self.lock:
            if indice in self.pecas: # Peça repetida (duas threads baixaram a mesma), nada muda
                return
            self.pecas[indice] = bytes(peca) # Agora este nó também pode servir essa peça pra outros
            self.downloaded = sum(len(p) for p in self.pecas.values())
            self.left = self.torrent["info"]["length"] - self.downloaded
            conexoes = list(self.conexoes_upload)
        for conexao in conexoes: # HAVE para quem se conectou em nós
            try:
                conexao.enviar(Have(indice))
            except OSError: # O peer saiu, a thread dele já se encarrega de limpar
                pass
        
    # Seeder: lê o arquivo e guarda só as peças que batem com o hash do .torrent
    def carregar_arquivo(self, caminho):
        info = self.torrent["info"]
        self.pecas = fragmentar_arquivo(caminho, info["piece length"])
        self.left = info["length"] - sum(len(peca) for peca in self.pecas.values())

    # Caminho do upload -> SEEDER. O peer já mandou o handshake dele.
    # `peer_id` (bytes) é quem decide se ele está em lockdown.
    def upload(self, conexao, peer_id=None):
        peer = ConexaoPeer(conexao, peer_id)
        with self.lock: # Registrar e mandar o bitfield no mesmo lock: nenhum HAVE chega antes dele
            self.conexoes_upload.append(peer)
            peer.enviar(Bitfield(bitfield_de_pecas(list(self.pecas), self.qtd_pecas))) # Avisa quais peças tem
        try:
            while True: # Até o peer desconectar
                mensagem = ler_mensagem(conexao)

                if isinstance(mensagem, Request):
                    if self.esta_bloqueado(peer_id): # Lockdown: nega o upload dessa peça pra esse leecher
                        print(f"[Seeder] CHOKE: pedido de {self._nome(peer_id)} negado (lockdown)")
                        peer.enviar(Choke())
                        continue
                    bloco = self._bloco(mensagem)
                    print(f"[Seeder] Mandando peca {mensagem.indice}")
                    peer.enviar(bloco)
                # Libera os pedidos (ou nega, se ele estiver em lockdown)
                elif isinstance(mensagem, Interested):
                    if self.esta_bloqueado(peer_id):
                        print(f"[Seeder] Mandando choke para {self._nome(peer_id)} (lockdown)")
                        peer.enviar(Choke())
                    else:
                        print("[Seeder] Mandando unchoke...")
                        peer.enviar(Unchoke())
                # Have, NotInterested etc.: o seeder não precisa fazer nada com eles
        finally:
            with self.lock:
                self.conexoes_upload.remove(peer)

    # Recorta o bloco pedido. Pedido de peça que não temos derruba a conexão
    def _bloco(self, pedido):
        peca = self.pecas.get(pedido.indice)
        if peca is None:
            raise ErroProtocolo(f"pediu a peça {pedido.indice}, que este nó não tem")
        self.uploaded += pedido.tamanho
        return Piece(pedido.indice, pedido.inicio, peca[pedido.inicio:pedido.inicio + pedido.tamanho])

    # ---------------------------------------------------------------------------
    # Lockdown (CHOKE)
    # ---------------------------------------------------------------------------

    @staticmethod
    def _normalizar(peer_id):
        return peer_id.encode("latin1") if isinstance(peer_id, str) else bytes(peer_id)

    @staticmethod
    def _nome(peer_id):
        return peer_id.decode("latin1") if peer_id else "?"

    def esta_bloqueado(self, peer_id):
        with self.lock:
            return peer_id in self.bloqueados

    # Seeder nega o upload para ESSE leecher (os outros continuam sendo atendidos).
    # Se ele já está conectado, recebe o CHOKE agora. Se conectar depois, recebe CHOKE no INTERESTED.
    def bloquear(self, peer_id):
        peer_id = self._normalizar(peer_id)
        with self.lock:
            self.bloqueados.add(peer_id)
            alvos = [c for c in self.conexoes_upload if c.peer_id == peer_id]
        for conexao in alvos:
            try:
                conexao.enviar(Choke())
            except OSError:
                pass
        print(f"[Seeder] LOCKDOWN em {self._nome(peer_id)}")

    # Desfaz o lockdown: o leecher recebe UNCHOKE e volta a poder pedir
    def desbloquear(self, peer_id):
        peer_id = self._normalizar(peer_id)
        with self.lock:
            self.bloqueados.discard(peer_id)
            alvos = [c for c in self.conexoes_upload if c.peer_id == peer_id]
        for conexao in alvos:
            try:
                conexao.enviar(Unchoke())
            except OSError:
                pass
        print(f"[Seeder] Lockdown removido de {self._nome(peer_id)}")

    # peer_ids (bytes) de quem está conectado em nós agora
    def peers_conectados(self):
        with self.lock:
            return [c.peer_id for c in self.conexoes_upload]

    # Envia event=stopped para o tracker, sinalizando o término da sessao
    def shutdown(self, porta, peer_id):
        print(f"[BitTorrentWannaBe] DESLIGANDO SESSAO...  {self.event}")
        # avisar pro trackeer que acabou, senão só sai por timeout
        return self.announce(porta, peer_id, Event.STOPPED)
