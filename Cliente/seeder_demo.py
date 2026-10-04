import Cliente
from pathlib import Path
from servicos.torrent_reader import ler_torrent
import time

cliente = Cliente.Cliente()

dir = Path(__file__).parent.parent
path = dir / "Arquivo demo/spyxfamily_op.mp4"
path_torrent = dir / "Arquivo demo/spyxfamily_op.mp4.torrent"
torrent = ler_torrent(path_torrent)

sessao = cliente.instanciar_sessao(torrent, path)

while True:
    time.sleep(0.25)