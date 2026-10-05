# Neste módulo vai estar todas as funções para comunicação P2P
# Desde o handshake, troca de mensagens, até a escrita no disco.

# Offset do hash no .torrent, chave pieces.
# offset inicial = N X 20, N sendo o índice da peça. Peça 0, N = 0
# offset final = (N x 20) + 20, 20 sendo o tamanho da peça, ou seja, piece length

# offset de bloco na memória RAM (begin)
# Alocar buffer na memória com o tamanho totalal da peça: bytearray(piece_length)
# Posição no buffer = [begin : begin + tamanho_do_bloco] Ele faz um slice no bytearray

from servicos.torrent_reader import ler_torrent
import hashlib, struct

def validar_peca(indice, peca, pieces): # pieces = hashes concatenados de todos as pecas

    # Como pode não estar ordenada, preciso achar o hash equivalente da peca dentro a array de hashes
    offset_hash = indice * 20 # 20 bytes porque sha1 retorna um hash de 20 bytes
    hash_esperado = pieces[offset_hash: offset_hash + 20] # 20 bytes porque sha1 retorna um hash de 20 bytes
    hash_calculado = hashlib.sha1(peca).digest()

    if hash_esperado != hash_calculado:
        return False

    return peca
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

def parse_bitfield(bitfield_bytes: bytes, total_pieces:int):
    indices_desejados = []

    for piece_index in range(total_pieces):
        byte_index = piece_index // 8 # Cada byte ocupa 8 peças (8 bits), separo byte por byte do bitfield
        bit_offset = 7 - (piece_index % 8) # Descobre a posição exata do bit. Como os bits são lidos da esquerda pra direita, a primeira peça do byte (resto 0) fica no bity 7 (mais á esquerda), depois assim por diante

        if (bitfield_bytes[byte_index] >> bit_offset) and 1: # Muito complexo pra explicar em uma linha. Faz a operação: bitwise right shift
            indices_desejados.append(piece_index)

    return indices_desejados

def handshake(info_hash, peer_dst, peer_id, socket):
    pstr = b"BitTorrentWannaBe"
    pstrlen = len(pstr)
    pacote = struct.pack(">B17s20s20s", pstrlen, pstr, info_hash, peer_id)
    

# Teste rápido, só roda chamando direto (de dentro de Cliente): python3 -m servicos.p2p
if __name__ == "__main__":
    mapa = fragmentar_arquivo("exemplo.txt", 132)
    torrent = ler_torrent("exemplo.txt.torrent")

    for indice, peca in mapa.items():
        peca = validar_peca(indice, peca, torrent["info"]["pieces"])
        if peca:
            print("SUCESSO")
        else:
            print("ERRO")
def validar_peca(indice, peca, pieces): # pieces = hashes concatenados de todos as pecas

    # Como pode não estar ordenada, preciso achar o hash equivalente da peca dentro a array de hashes
    offset_hash = indice * 20 # 20 bytes porque sha1 retorna um hash de 20 bytes
    hash_esperado = pieces[offset_hash: offset_hash + 20] # 20 bytes porque sha1 retorna um hash de 20 bytes
    hash_calculado = hashlib.sha1(peca).digest()

    if hash_esperado != hash_calculado:
        return False

    return True



