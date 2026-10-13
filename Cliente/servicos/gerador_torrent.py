import hashlib
from pathlib import Path
from servicos.parser import bencode

def gerar_torrent(caminho_arquivo, url_tracker, piece_length=32, shamir=None):
    # Lê os bytes do arquivo
    with open(caminho_arquivo, "rb") as arquivo:
        conteudo = arquivo.read()

    # Tamanho do arquivo 
    tamanho_total = len(conteudo)

    # Concatenar os hashes das peças
    hashes_conc_str = ""
    for i in range(0, tamanho_total, piece_length):
        # Vai percorrendo o conteudo do arquivo de piece_length a piece_length bytes
        peca = conteudo[i:i+piece_length]
        # 20 bytes binários
        hash_peca = hashlib.sha1(peca).digest()
        hashes_conc_str += hash_peca.decode("latin1")

    info = {
        "length": tamanho_total,
        "name": caminho_arquivo.name,
        "piece length": piece_length,
        "pieces": hashes_conc_str # string para a biblioteca parser funcionar
    }

    # Arquivo cifrado: ({"k": 2, "n": 3}) fica dentro do info pra entrar no info_hash 
    # Ai ninguém troca sem mudar o arquivo
    if shamir:
        info["shamir"] = shamir

    torrent_dic = {
        "announce": url_tracker,
        "info": info,
        "private": 1 
    }
    # Transformo em B-encode para escrever no arquivo .torrent
    torrent = bencode(torrent_dic)

    # Escrevo em bytes. Para ler o arquivo precisa decodificar em latin1, isso é importante para o hash das peças.
    with open(f"{caminho_arquivo}.torrent", "wb") as arquivo:
       arquivo.write(bytes(torrent.encode("latin1"))) 
    return f"{caminho_arquivo}.torrent"

if __name__ == "__main__": 
    dir = Path(__file__).parent.parent.parent
    path = dir / "Arquivo demo/spyxfamily_op.mp4"
    gerar_torrent(path, "https://exemplo.tracker.com", 131072)