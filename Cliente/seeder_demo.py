import Cliente, os, sys, painel
from pathlib import Path
from servicos.torrent_reader import ler_torrent
from servicos.cifra import ler_parte
from servicos.partes import SALA, consultar, entregar_parte

# python3 seeder_demo.py [arquivo] [torrent] [partes...]
# sem argumento arquivo e torrent são o vídeo da demo
# com as partes da chave (do cifrar.py), você escolhe na SALA quem guarda cada uma

tracker = os.environ.get("TRACKER_URL", "http://127.0.0.1:6969")
chave = os.environ.get("TRACKER_CHAVE", "") # ./tracker cadastrar <nome> mostra a chave

dir = Path(__file__).parent.parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else dir / "Arquivo demo/spyxfamily_op.mp4"
path_torrent = Path(sys.argv[2]) if len(sys.argv) > 2 else dir / "Arquivo demo/spyxfamily_op.mp4.torrent"
torrent = ler_torrent(path_torrent)

# Confere as partes antes de entrar na rede
partes = [ler_parte(caminho) for caminho in sys.argv[3:]]
if partes:
    if "shamir" not in torrent["info"]:
        sys.exit("esse .torrent não é de arquivo cifrado")
    k = torrent["info"]["shamir"]["k"]
    if len(partes) < k:
        sys.exit(f"precisa de {k} partes, veio {len(partes)}")

cliente = Cliente.Cliente(chave, tracker)

# Mostra os clientes ligados (a SALA) e pergunta quem guarda as partes. Cada um guarda uma
def escolher_guardioes(k, n):
    eu = cliente.peer_id.decode("latin1")
    ligados = [p for p in consultar(tracker, "peers", SALA, chave) if p["peer_id"] != eu]
    if len(ligados) < k:
        cliente.shutdown()
        sys.exit(f"precisa de {k} clientes ligados pra guardar as partes, tem {len(ligados)}")
    print("Clientes ligados:")
    for i, p in enumerate(ligados, start=1):
        print(f"  [{i}] {p['peer_id']}  {p['ip']}:{p['port']}")
    while True:
        numeros = input(f"Quem guarda as partes? De {k} a {n} números separados por espaço: ").split()
        if all(x.isdigit() for x in numeros):
            numeros = [int(x) for x in numeros]
            if k <= len(numeros) <= n and len(set(numeros)) == len(numeros) and all(1 <= x <= len(ligados) for x in numeros):
                return [ligados[x - 1] for x in numeros]
        print("escolha inválida")

escolhidos = escolher_guardioes(k, len(partes)) if partes else []

# O announce started já leva os escolhidos: o Tracker registra quem guarda as partes
sessao = cliente.instanciar_sessao(torrent, path, tracker, [g["peer_id"].encode("latin1") for g in escolhidos])

# Uma parte pra cada guardião. As partes continuam aqui também
for guardiao, parte in zip(escolhidos, partes):
    if entregar_parte((guardiao["ip"], guardiao["port"]), sessao.info_hash, cliente.peer_id, parte):
        print(f"[Seeder] parte entregue para {guardiao['peer_id']}")
    else:
        print(f"[Seeder] {guardiao['peer_id']} não confirmou a parte")

# Compartilha mostrando o painel até apertar q ou Ctrl+C (PAINEL=0 desliga o painel)
painel.acompanhar(cliente, sessao, "semear")
cliente.shutdown() # Envia event=stopped ao Tracker
