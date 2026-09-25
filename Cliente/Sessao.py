from servicos.info_hash import infhash

class Sessao:
    def __init__(self, arquivo, uploaded=0, downloaded=0, left=0):
        # Dados da sessão
        self.info_hash = infhash(arquivo) # Extrai o info_hash do arquivo
        self.tracker = arquivo["announce"] # Endereço do Tracker
        self.uploaded = uploaded # Quantos bytes foram compartilhados na rede pelo nó
        self.downloaded = downloaded # Quantos bytes o nó baixou da rede
        self.left = left # Quantos bytes faltam para baixar do arquivo espeficicado pelo info_hash
        self.arquivo = arquivo # Dicionário do .Torrent
        self.private = arquivo["private"] # Define se o arquivo é privado ou não
        # Dados retornados pelo Tracker
        self.interval = 0
        self.min_interval = 0
        self.complete = 0
        self.incomplete = 0

        # Lista de peers daquele arquivo
        self.swarm = [] # Ex: [("19.75.87.9", 8000), ("11.123.43.6", 9080)]

    # Atualizar dados interos através da resposta do Tracker
    def atualizar_dados_tracker(self, dados_tracker:dict):
        self.interval = dados_tracker["interval"]
        self.min_interval = dados_tracker["min_interval"]
        self.complete = dados_tracker["complete"]
        self.incomplete = dados_tracker["incomplete"]