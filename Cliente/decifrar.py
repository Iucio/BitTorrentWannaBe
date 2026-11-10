import sys
from pathlib import Path
from servicos.cifra import ler_parte, decifrar_com_partes
from servicos.torrent_reader import ler_torrent

# python3 decifrar.py <arquivo_baixado> <torrent> <parte>

if len(sys.argv) < 4:
    sys.exit("uso: python3 decifrar.py <arquivo_baixado> <torrent> <parte>")

baixado, caminho_torrent, *arquivos_partes = sys.argv[1:]
info = ler_torrent(caminho_torrent)["info"]
k = info["shamir"]["k"]
if len(arquivos_partes) < k:
    sys.exit(f"precisa de {k} partes, veio {len(arquivos_partes)}")

partes = [ler_parte(caminho) for caminho in arquivos_partes]
destino = Path("baixados") / info["name"].removesuffix(".cifrado")
destino.parent.mkdir(exist_ok=True)

if not decifrar_com_partes(baixado, destino, partes, k):
    sys.exit("não deu pra abrir: partes erradas ou arquivo corrompido")

print(f"arquivo aberto em {destino}")
