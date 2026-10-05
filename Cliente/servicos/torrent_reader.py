from servicos.parser import bencode

def ler_torrent(caminho):
    with open(caminho, "rb") as arquivo:
        conteudo = arquivo.read()

    return bencode(conteudo.decode("latin1"))