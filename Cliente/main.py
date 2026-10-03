import Cliente
from pathlib import Path
from servicos.torrent_reader import ler_torrent

# Início do programa
cliente = Cliente.Cliente()

dir = Path(__file__).parent.parent
path = dir / "Arquivo demo/spyxfamily_op.mp4.torrent"
spyxfamily = ler_torrent(path)

# Inicio das sessoes nos arquivos (upload ou download)
sessao = cliente.instanciar_sessao(spyxfamily) # retorna info_hash da sessao

sessao.download()
# Desligamento da aplicação
# Envia announces contendo o campo event=stopped para cada sessao (info_hash) 
cliente.shutdown()