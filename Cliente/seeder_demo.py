import Cliente, os, sys
from pathlib import Path
from servicos.torrent_reader import ler_torrent
import time

# python3 seeder_demo.py [arquivo] [torrent]
# sem argumento arquivo e torrent são o vídeo da demo

tracker = os.environ.get("TRACKER_URL", "http://127.0.0.1:6969")

cliente = Cliente.Cliente()

dir = Path(__file__).parent.parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else dir / "Arquivo demo/spyxfamily_op.mp4"
path_torrent = Path(sys.argv[2]) if len(sys.argv) > 2 else dir / "Arquivo demo/spyxfamily_op.mp4.torrent"
torrent = ler_torrent(path_torrent)

sessao = cliente.instanciar_sessao(torrent, path, tracker)

# Compartilha até o usuário apertar Ctrl+C
try:
    while True:
        time.sleep(0.25)
except KeyboardInterrupt:
    cliente.shutdown() # Envia event=stopped ao Tracker