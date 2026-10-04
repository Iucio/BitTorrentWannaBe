
# Instanciar as threads para a comunicação p2p
# Cada thread vai ficar responsável por se comunicar com um peer diferente
import threading, queue, socket, math, progressbar, time
from servicos.mensagens import(
    Handshake, ler_mensagem, pecas_do_bitfield, Request, Interested, Unchoke, ler_handshake
)
from servicos.p2p import validar_peca

class GerenciadorDownload:
    def __init__(self, info:dict, info_hash:bytes, peer_id:bytes, swarm:list):
        self.mini_leechers_ativos = {} # Dicionário de leechers ativos
        self.mapa_peca_peers = {} # Mapa de peers por peça: {peca1 : {peer1, peer2, peer4}, peca2 : {peer2, peer20, peer3}, ...}
        self.lock_mini_leechers_ativos = threading.Lock() # Impesso condição de corrida na hora das threads escreverem
        self.lock_mapa_peca_peers = threading.Lock() # Impesso condição de corrida na hora das threads escreverem
        
        self.hash_pecas = info["pieces"]
        self.piece_length = info["piece length"]
        self.length = info["length"]
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.swarm = swarm
        self.caminho = "arquivo_final.bin"
        self.total_pecas = math.ceil(info["length"] / self.piece_length)
        self.pecas_baixadas = set() # Guarda as peças que foram validadas e salvas no disco
        self.lock_pecas_baixadas = threading.Lock()

        # Aloca exatamente o espaço do arquivo no disco
        with open(self.caminho, "a+b") as f:
            f.truncate(self.length) 
    # Registra sem condição de corrida as peças envidadas pelo outro peer
    def registrar_pecas(self, peer:tuple, conjunto_pecas):
        with self.lock_mapa_peca_peers: # garante que apenas 1 thread edite o dicionário
            for peca_index in conjunto_pecas: 
                if peca_index not in self.mapa_peca_peers:
                    self.mapa_peca_peers[peca_index] = set()
                self.mapa_peca_peers[peca_index].add(peer)

    # Instacia uma thread para cada peer do swarm. Eu quis chamar de mini leecher
    def instanciar_mini_leechers(self, swarm:list):
        print("[GerenciadorDownload]: instaciando mini leechers...")
        for peer in swarm:
            with self.lock_mini_leechers_ativos:
                if peer not in self.mini_leechers_ativos:
                    mini_leecher = MiniLeecher(self, peer, self.hash_pecas, self.piece_length, self.info_hash, self.peer_id, self.total_pecas)
                    self.mini_leechers_ativos.update({peer : mini_leecher})
                    mini_leecher.start()
                    
        print("[GerenciadorDownload]: sucesso")

    # Salva no disco a peça, validada, na posição correta
    def escrever_peca_disco(self, index, peca):
        posicao_no_disco = index * self.piece_length
        with open(self.caminho, "r+b") as f:
            f.seek(posicao_no_disco)
            f.write(peca)
        # Salva as peças baixada, para poder compartilhar com outros nós.
        with self.lock_pecas_baixadas:
            self.pecas_baixadas.add(index)
        #print(f"[Orquestrador]: peça {index} escrita no disco com sucesso.")
    
    # Gerenciador para distribuir requisições aos leechers ativos
    def orquestrador(self):
            for index_peca in range(self.total_pecas):
                
                # Se a peça já foi baixada, pulo pra próxima
                with self.lock_pecas_baixadas:
                    if index_peca in self.pecas_baixadas:
                        print(self.pecas_baixadas)
                        print(f"PECA JÁ BAIXADA!")
                        continue
                
                # Busca peers que têm essa peça
                with self.lock_mapa_peca_peers:
                    peers_com_peca  = list(self.mapa_peca_peers.get(index_peca, set()))
                # Nenhum peer têm essa peça ainda
                if not peers_com_peca: # Não vai acontecer na demo ;)
                    continue 

                with self.lock_mini_leechers_ativos:
                    for peer in peers_com_peca:
                        # Pega o leecher que está em contato com o peer
                        mini_leecher = self.mini_leechers_ativos.get(peer)
                        tamanho_peca = self._calcular_tamanho_peca(index_peca)
                        self._enfilerar_blocos_peca(mini_leecher, index_peca, tamanho_peca)
                        break # Se eu encontrei um peer para pedir, então não preciso pedir a mesma peça para outro
            
            #print(f"[Orquestrador]: arquivo baixado com sucesso!")
    def _calcular_tamanho_peca(self, index):
        if index == self.total_pecas - 1: # última peça
            resto = self.length % self.piece_length
            if resto != 0:
                return resto
            else:
                return self.piece_length
        return self.piece_length

    # Coloco todos os blocos da peca na fila.
    def _enfilerar_blocos_peca(self, mini_leecher, index_peca, tamanho_peca):
        tam_bloco = 16384 # Por padrão
        begin = 0
        while begin < tamanho_peca:
            length = min(tam_bloco, tamanho_peca - begin) # pego o tamanho do bloco padrão e do bloco menor que o padrão (último bloco)
            mini_leecher.adicionar_request_fila(index_peca, begin, length)
            begin += length


# A thread vai fazer o handhsake com o peer que lhe foi passado, retornar as peças que aquele peer têm.
# Depois disso, vai esperar por peças para fazer request na fila_request. 
# Vai alocar um espaço na RAM para a peça, receber os blocos da peça e validar o hash da peça.
# Depos disso, vai devolver a peça pro gerenciador para ele escrever no disco.
# Depois libera o espaço na RAM.
class MiniLeecher(threading.Thread):
    def __init__(self, gerenciador:GerenciadorDownload, peer, hash_pecas, piece_length, info_hash, peer_id, total_pecas):
        self.peer = peer # tupla (ip, porta)
        self.gerenciador = gerenciador
        self.fila_request = queue.Queue()
        self.choked = True # Começa com True até o peer nos dar Unchoke 
        self.hash_pecas = hash_pecas # concateação dos hashes das peças
        self.piece_length = piece_length  # tamanho da peça
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.total_pecas = total_pecas
        super().__init__(daemon=True)

    def run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Instancia o socket cliente
            self.sock.settimeout(5.0) # Caso o peer esteja offline, o timeout para o connect
            self.sock.connect(self.peer)
            self.sock.settimeout(None) # Deixo livre, já que a conexão foi estabelecida

            # Abre a conexão, realiza o handshake e recebe o bitfield. Retorna as peças que aquele peer tem
            pecas_do_peer = self.handshake()
            #print("Recebeu bitfield")

            # Registra as peças no mapa para o gerenciador designar quais threads vão pedir quais peças
            self.gerenciador.registrar_pecas(self.peer, pecas_do_peer)
             
            if type(self.interested()) == Unchoke: # Liberou geral!
                self.choked = False
                print(f"[MiniLeecher] {self.peer}: unchoke")
            time.sleep(3)
            self._loop_trabalho()
                
        except Exception as e:
            print(f"[MiniLeecher] {self.peer} erro: {e}")
            # O peer não respondeu ao handshake, pode estar offline. 
            # Termino essa thread e excluo ela das ativas
            with self.gerenciador.lock_mini_leechers_ativos:
                self.gerenciador.mini_leechers_ativos.pop(self.peer)
        finally:
            if self.sock:
                self.sock.close()

    # handshake
    def handshake(self) -> set:
        pack_handshake = Handshake(self.info_hash, self.peer_id).para_bytes()
        self.sock.sendall(pack_handshake) # Mando o handshake para o peer
        bitfield = ler_mensagem(self.sock) # Resposta do outro peer
        return pecas_do_bitfield(bitfield.bits, self.total_pecas) # Transformo em um set de peças

    def adicionar_request_fila(self, index:int, begin:int, length=16384):
        self.fila_request.put((index, begin, length))

    def _calcular_tamanho_peca(self, index):
            if index == self.total_pecas - 1: # última peça
                resto = self.gerenciador.length % self.piece_length
                if resto != 0:
                    return resto
            return self.piece_length

    def interested(self):
        pack_interested = Interested().para_bytes()
        self.sock.sendall(pack_interested) # Mando o interested para o peer
        return ler_mensagem(self.sock) # Deve ser Unchoke ou Choke
        
    def _loop_trabalho(self):
        while not self.choked and not self.fila_request.empty():
                self._processar_peca()

            

    def _processar_peca(self):
        index, begin, length = self.fila_request.get()
        tamanho_peca = self._calcular_tamanho_peca(index) 
        buffer_peca = bytearray(tamanho_peca)
        total_blocos = math.ceil(tamanho_peca / 16384) # Tamanho padrão dos blocos
        blocos_recebidos = 0
        while blocos_recebidos < total_blocos:
                # Manda o Request para o seeder
                request = Request(index, begin, length).para_bytes()
                self.sock.sendall(request)

                # Resposta do seeder, Piece(peca). Bloco da peça 
                msg = ler_mensagem(self.sock) 
                #print(f"PIECE: {(msg.indice, msg.inicio, len(msg.bloco))}")
                dados_bloco = msg.bloco
                buffer_peca[begin: begin + len(dados_bloco)] = dados_bloco

                blocos_recebidos += 1
                if self.fila_request.empty():
                    break
                elif blocos_recebidos < total_blocos:
                    index, begin, length = self.fila_request.get()
                     
        if validar_peca(index, buffer_peca, self.hash_pecas):
            self.gerenciador.escrever_peca_disco(index, buffer_peca)
            #print(f"[MiniLeecher] peca validada: {index}")
                
        else:
            print(f"[MiniLeecher] {self.peer}: Peça {index} corrompida.")

                

    