import random, string, socket, Sessao, threading as t
from servicos.request import request_tracker
from servicos.mensagens import ler_handshake, ErroProtocolo

class Cliente:
    def __init__(self):
        self.peer_id = self._gerar_peer_id()
        self.server = self._gerar_servidor()
        self.host, self.porta = self.server.getsockname()
        self.sessoes = {}
        self._interface()
        print(f"Esperando peers na porta {self.porta}\n")
        t.Thread(target=self._aceitar_peers, daemon=True).start() # Atende outros peers em segundo plano

    # Método privado da classe
    def _gerar_peer_id(self): # Ainda não sei onde que vai ficar essa função.
        prefixo = "-UF0001-" # Identificao utilizada no protocolo, mas criei uma, pois é um trabalho de faculdade.
        randon_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=12))
        return (prefixo + randon_bytes).encode("latin1")

    # Método privado da classe para instaciar o servidor para comunicações.
    def _gerar_servidor(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", 0)) # 0.0.0.0 aceita conexão por qualquer interface. 0 fala para pegar qualquer porta disponível da máquina, ou seja, efêmera e aleatória.
        server.listen()
        return server

    # Espera peers conectarem; cada um é atendido numa thread própria
    def _aceitar_peers(self):
        while True:
            try:
                conexao, endereco = self.server.accept()
            except OSError: # Servidor fechado no shutdown
                return
            t.Thread(target=self._atender_peer, args=(conexao, endereco), daemon=True).start()

    # O handshake do peer diz de qual arquivo (info_hash) ele quer peças
    def _atender_peer(self, conexao, endereco):
        peer = f"{endereco[0]}:{endereco[1]}"
        print(f"Peer conectou: {peer}")
        conexao.settimeout(60) # Peer parado por 1 min é desconectado
        motivo = "saiu"
        with conexao:
            try:
                handshake = ler_handshake(conexao)
                sessao = self.sessoes.get(handshake.info_hash)
                if sessao:
                    sessao.upload(conexao)
                else:
                    motivo = "pediu um arquivo que este cliente não tem"
            except ErroProtocolo as erro: # Peer mandou algo fora do protocolo
                motivo = str(erro)
            except TimeoutError:
                motivo = "ficou 1 min parado"
            except OSError: # Peer fechou a conexão
                pass
        print(f"Peer desconectou: {peer} ({motivo})")

    # Salva a sessão por info_hash como chave de busca. Com caminho_arquivo, o nó já tem o arquivo e vira seeder
    def instanciar_sessao(self, torrent, caminho_arquivo=None):
        nova_sessao = Sessao.Sessao(torrent, self.peer_id)
        if caminho_arquivo:
            nova_sessao.carregar_arquivo(caminho_arquivo)
        self.sessoes[nova_sessao.info_hash] = nova_sessao
        #nova_sessao.announce(self.porta, self.peer_id)
        return nova_sessao 

    # Announce de uma sessao com o event atual dela. Retorna a resposta do Tracker
    def announce(self, info_hash):
        sessao = self.sessoes[info_hash]
        resposta = sessao.announce(self.porta, self.peer_id, sessao.event)
        sessao.atualizar_dados_tracker(resposta)
        return resposta

    def shutdown(self):
        print(f"\nDesligando...")
        for sessao in self.sessoes.values():
        self.event = Event.STOPPED
        for sessao in self.sessoes.values():
            sessao.shutdown(self.porta, self.peer_id)
        self.server.close() # Libera recursos
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
             