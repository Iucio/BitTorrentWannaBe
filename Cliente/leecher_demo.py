import Cliente, os, sys
from pathlib import Path
from servicos.torrent_reader import ler_torrent
from servicos.gerador_torrent import gerar_torrent
from servicos.cifra import ler_parte, decifrar_com_partes

# python3 leecher_demo.py [torrent] [partes...]
# sem argumento torrent é o vídeo da demo
# com as partes da chave (do cifrar.py), decifra sozinho no fim

# Endereço do Tracker. Padrão: mesma máquina (./tracker 6969).
# Outro: TRACKER_URL=http://<ip>:<porta>

# se n passar é localhost
tracker = os.environ.get("TRACKER_URL", "http://127.0.0.1:6969")
# Chave de acesso: ./tracker cadastrar <nome> mostra a chave
chave = os.environ.get("TRACKER_CHAVE", "")

# Início do programa
cliente = Cliente.Cliente(chave, tracker)

dir = Path(__file__).parent.parent
path_torrent = Path(sys.argv[1]) if len(sys.argv) > 1 else dir / "Arquivo demo/spyxfamily_op.mp4.torrent"
spyxfamily = ler_torrent(path_torrent)

# Confere as partes antes de baixar
partes = [ler_parte(caminho) for caminho in sys.argv[2:]]
if partes:
    k = spyxfamily["info"]["shamir"]["k"] # só o .torrent do cifrar.py tem
    if len(partes) < k:
        sys.exit(f"precisa de {k} partes, veio {len(partes)}")

# Inicio das sessoes nos arquivos (upload ou download)
# Faz o announce e recebe os peers do Tracker
sessao = cliente.instanciar_sessao(spyxfamily, tracker=tracker) 

sessao.download()

# Desligamento da aplicação
# Envia announces contendo o campo event=stopped para cada sessao (info_hash) 
cliente.shutdown()

# Abre o arquivo baixado com as partes da chave
if partes:
    destino = Path("baixados") / spyxfamily["info"]["name"].removesuffix(".cifrado")
    destino.parent.mkdir(exist_ok=True)
    if not decifrar_com_partes("arquivo_final.bin", destino, partes, k): # onde o GerenciadorDownload grava
        sys.exit("não deu pra abrir: partes erradas ou arquivo corrompido")
    print(f"arquivo aberto em {destino}")