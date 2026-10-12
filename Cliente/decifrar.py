import sys
from itertools import combinations
from pathlib import Path
from cryptography.exceptions import InvalidTag
from servicos.cifra import juntar_chave, ler_parte, decifrar_arquivo
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

# Mesmo com chaves inválidas, tenta qualquer combinação de k chaves pra tentar decifrar
for combinacao in combinations(partes, k):
    try:
        decifrar_arquivo(baixado, destino, juntar_chave(list(combinacao)))
        break
    except (ValueError, InvalidTag):
        continue
else:
    sys.exit("não deu pra abrir: partes erradas ou arquivo corrompido")

print(f"arquivo aberto em {destino}")
