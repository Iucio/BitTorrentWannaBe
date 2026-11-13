import os, sys
from pathlib import Path
from servicos.cifra import gerar_chave, cifrar_arquivo, dividir_chave, salvar_parte
from servicos.gerador_torrent import gerar_torrent

tam_peca = 128 * 1024

# python3 cifrar.py <arquivo> [n] [k]   (padrão: 3 partes, 2 abrem)

if len(sys.argv) < 2:
    sys.exit("uso: python3 cifrar.py <arquivo> [n] [k]")

tracker = os.environ.get("TRACKER_URL", "http://127.0.0.1:6969")
original = Path(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
k = int(sys.argv[3]) if len(sys.argv) > 3 else 2
if not 1 <= k <= n:
    sys.exit("k precisa estar entre 1 e n")

chave = gerar_chave()
cifrado = original.with_name(original.name + ".cifrado")
cifrar_arquivo(original, cifrado, chave)
torrent = gerar_torrent(cifrado, tracker, tam_peca, {"k": k, "n": n})

pasta = Path("partes")
pasta.mkdir(exist_ok=True)
for i, parte in enumerate(dividir_chave(chave, n, k), start=1):
    salvar_parte(parte, pasta / f"{original.name}.parte{i}")
del chave

print(f"cifrado: {cifrado}")
print(f"torrent: {torrent}")
print(f"{n} partes da chave em {pasta}/ ({k} abrem o arquivo)")
