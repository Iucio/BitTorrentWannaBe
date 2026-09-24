class Sessao:
    def __init__(self, complete:int, incomplete:int, interval:int, uploaded=0, downloaded=0, left=0, min_interval:int=0):
        # Dados da sessão
        self.uploaded = uploaded
        self.downloaded = downloaded
        self.left = left
        self.interval = interval
        self.min_interval = min_interval
        self.complete = complete
        self.incomplete = incomplete