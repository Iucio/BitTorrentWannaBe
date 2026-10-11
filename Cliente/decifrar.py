import sys

# python3 decifrar.py <arquivo_baixado> <torrent> <parte>

if len(sys.argv) < 4:
    sys.exit("uso: python3 decifrar.py <arquivo_baixado> <torrent> <parte>")

baixado, caminho_torrent, *arquivos_partes = sys.argv[1:]
