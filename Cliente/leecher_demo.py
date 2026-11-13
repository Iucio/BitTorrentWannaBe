import Cliente, os, sys, painel, time
from pathlib import Path
from servicos.torrent_reader import ler_torrent
from servicos.cifra import ler_parte, decifrar_com_partes
from servicos.partes import consultar, pedir_parte

# python3 leecher_demo.py [torrent] [partes...]
# sem argumento torrent é o vídeo da demo
# arquivo cifrado: pede as partes da chave aos guardiões e decifra sozinho no fim.
# Partes passadas aqui completam se os guardiões não derem k

# Endereço do Tracker. Padrão: mesma máquina (./tracker 6969).
# Outro: TRACKER_URL=http://<ip>:<porta>

# se n passar é localhost
tracker = os.environ.get("TRACKER_URL", "http://127.0.0.1:6969")
# Chave de acesso: ./tracker cadastrar <nome> mostra a chave
chave = os.environ.get("TRACKER_CHAVE", "")

dir = Path(__file__).parent.parent
path_torrent = Path(sys.argv[1]) if len(sys.argv) > 1 else dir / "Arquivo demo/spyxfamily_op.mp4.torrent"
spyxfamily = ler_torrent(path_torrent)
info = spyxfamily["info"]
cifrado = "shamir" in info # só o .torrent do cifrar.py tem

# Confere antes de entrar na rede (sair depois deixaria o cliente na SALA)
partes_arquivo = [ler_parte(caminho) for caminho in sys.argv[2:]]
if partes_arquivo and not cifrado:
    sys.exit("esse .torrent não é de arquivo cifrado")

# Início do programa
cliente = Cliente.Cliente(chave, tracker)

# Inicio das sessoes nos arquivos (upload ou download)
# Faz o announce e recebe os peers do Tracker
sessao = cliente.instanciar_sessao(spyxfamily, tracker=tracker)

# Baixa mostrando o painel, que fecha sozinho no fim (PAINEL=0 desliga o painel)
painel.acompanhar(cliente, sessao, "baixar")

# Pede as partes antes do shutdown: o guardião só entrega pra quem ainda está no swarm
partes = []
if cifrado:
    for guardiao in consultar(tracker, "guardioes", sessao.info_hash, chave):
        parte = pedir_parte((guardiao["ip"], guardiao["port"]), sessao.info_hash, cliente.peer_id)
        if parte:
            partes.append(parte)
            print(f"[Leecher] parte recebida de {guardiao['peer_id']}")
        else:
            print(f"[Leecher] {guardiao['peer_id']} não entregou a parte")
    partes = list(dict.fromkeys(partes + partes_arquivo)) # sem repetidas

# Abre o arquivo baixado com as partes da chave
if cifrado:
    k = info["shamir"]["k"]
    if len(partes) < k:
        sys.exit(f"precisa de {k} partes pra abrir, conseguiu {len(partes)}")
    destino = Path("baixados") / info["name"].removesuffix(".cifrado")
    destino.parent.mkdir(exist_ok=True)
    if not decifrar_com_partes("arquivo_final.bin", destino, partes, k): # onde o GerenciadorDownload grava
        sys.exit("não deu pra abrir: partes erradas ou arquivo corrompido")
    print(f"arquivo aberto em {destino}")