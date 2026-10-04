import Cliente
from pathlib import Path
from servicos.torrent_reader import ler_torrent
from servicos.gerador_torrent import gerar_torrent

# Tracker rodando na mesma máquina: ./tracker 6969
tracker = "http://127.0.0.1:6969"

# Início do programa
cliente = Cliente.Cliente()

dir = Path(__file__).parent.parent
path_torrent = dir / "Arquivo demo/spyxfamily_op.mp4.torrent"
spyxfamily = ler_torrent(path_torrent)

# Inicio das sessoes nos arquivos (upload ou download)
sessao = cliente.instanciar_sessao(spyxfamily) # retorna info_hash da sessao
sessao.add_peer_demo(("192.168.1.8", 53405))

sessao.download()

# Desligamento da aplicação
# Envia announces contendo o campo event=stopped para cada sessao (info_hash) 
cliente.shutdown()