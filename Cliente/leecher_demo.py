import Cliente, os
from pathlib import Path
from servicos.torrent_reader import ler_torrent
from servicos.gerador_torrent import gerar_torrent

# Endereço do Tracker. Padrão: mesma máquina (./tracker 6969). 
# Outro: TRACKER_URL=http://<ip>:<porta>

# se n passar é localhost
tracker = os.environ.get("TRACKER_URL", "http://127.0.0.1:6969")

# Início do programa
cliente = Cliente.Cliente()

dir = Path(__file__).parent.parent
path_torrent = dir / "Arquivo demo/spyxfamily_op.mp4.torrent"
spyxfamily = ler_torrent(path_torrent)

# Inicio das sessoes nos arquivos (upload ou download)
# Faz o announce e recebe os peers do Tracker
sessao = cliente.instanciar_sessao(spyxfamily, tracker=tracker) 

sessao.download()

# Desligamento da aplicação
# Envia announces contendo o campo event=stopped para cada sessao (info_hash) 
cliente.shutdown()