# Neste módulo vai estar todas as funções para comunicação P2P
# Desde o handshake, troca de mensagens, até a escrita no disco.

# Offset do hash no .torrent, chave pieces.
# offset inicial = N X 20, N sendo o índice da peça. Peça 0, N = 0
# offset final = (N x 20) + 20, 20 sendo o tamanho da peça, ou seja, piece length

# offset de bloco na memória RAM (begin)
# Alocar buffer na memória com o tamanho totalal da peça: bytearray(piece_length)
# Posição no buffer = [begin : begin + tamanho_do_bloco] Ele faz um slice no bytearray

#from torrent_reader import ler_torrent
import hashlib
from pathlib import Path

def fragmentar_arquivo(caminho, piece_length):
    lista_pecas = []
    with open(caminho, "rb") as f:
        while True:
            peca = f.read(piece_length)
            if not peca:
                break
            lista_pecas.append(peca)

    map_index_peca = {}
    for i in range(len(lista_pecas)):
        map_index_peca.update({i : lista_pecas[i]})
    return map_index_peca

def validar_peca(indice, peca, pieces): # pieces = hashes concatenados de todos as pecas

    # Como pode não estar ordenada, preciso achar o hash equivalente da peca dentro a array de hashes
    offset_hash = indice * 20 # 20 bytes porque sha1 retorna um hash de 20 bytes
    hash_esperado = pieces[offset_hash: offset_hash + 20] # 20 bytes porque sha1 retorna um hash de 20 bytes
    hash_calculado = hashlib.sha1(peca).digest()

    if hash_esperado != hash_calculado:
        return False

    return True



