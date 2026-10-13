import Cliente, os, sys, threading
from pathlib import Path
from servicos.torrent_reader import ler_torrent
import time

tracker = os.environ.get("TRACKER_URL", "http://127.0.0.1:6969")

cliente = Cliente.Cliente()

dir = Path(__file__).parent.parent
path = dir / "Arquivo demo/spyxfamily_op.mp4"
path_torrent = dir / "Arquivo demo/spyxfamily_op.mp4.torrent"
torrent = ler_torrent(path_torrent)

sessao = cliente.instanciar_sessao(torrent, path, tracker)

# Comandos no terminal do seeder (lockdown):
#   peers                  lista o peer_id de quem está conectado
#   bloquear <peer_id>     nega upload (CHOKE) para esse leecher
#   desbloquear <peer_id>  volta a atender (UNCHOKE)
def comandos():
    for linha in sys.stdin:
        partes = linha.split()
        if partes[:1] == ["peers"]:
            print("[Seeder] conectados:", cliente.peers_conectados())
        elif len(partes) == 2 and partes[0] == "bloquear":
            cliente.bloquear(partes[1])
        elif len(partes) == 2 and partes[0] == "desbloquear":
            cliente.desbloquear(partes[1])

threading.Thread(target=comandos, daemon=True).start()

# Compartilha até o usuário apertar Ctrl+C
try:
    while True:
        time.sleep(0.25)
except KeyboardInterrupt:
    cliente.shutdown() # Envia event=stopped ao Tracker
