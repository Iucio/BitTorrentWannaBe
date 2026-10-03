import socket
import hashlib
import threading
import struct
from servicos.p2p import fragmentar_arquivo
from servicos.torrent_reader import ler_torrent
from servicos.info_hash import infhash
from pathlib import Path
from servicos.mensagens import (
    Handshake, decodificar_handshake, ler_mensagem, 
    Bitfield, Unchoke, Piece, Request, bitfield_de_pecas, Id
)

# Configurações do Arquivo Falso de Teste
  # 100 KB
  # 32 KiB
dir = Path(__file__).parent.parent
path = dir / "Arquivo demo/spyxfamily_op.mp4"
path_torrent = dir / "Arquivo demo/spyxfamily_op.mp4.torrent"
mapa_index_peca = fragmentar_arquivo(path, 131072)
torrent = ler_torrent(path_torrent)
INFO_HASH = infhash(torrent)
PIECE_LENGTH = torrent["info"]["piece length"]
TAMANHO_ARQUIVO = torrent["info"]["length"]
HASHES_CONCATENADOS = torrent["info"]["pieces"]

# Calcula os hashes SHA-1 das peças simuladas
TOTAL_PECAS = (TAMANHO_ARQUIVO + PIECE_LENGTH - 1) // PIECE_LENGTH

PEER_ID_SEEDER = b"-PY0001-123456789012"

def rodar_seeder(host="127.0.0.1", port=6881):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    print(f"[*] SEEDER MOCK: Escutando em {host}:{port}...")

    conn, addr = server.accept()
    print(f"[+] SEEDER MOCK: Conexão recebida de {addr}")

    try:
        # 1. Lê Handshake
        dados_hs = conn.recv(68)
        hs = decodificar_handshake(dados_hs)
        print("[+] SEEDER MOCK: Handshake recebido com sucesso!")

        # 2. Responde Handshake + Bitfield (possui todas as peças)
        conn.sendall(Handshake(hs.info_hash, PEER_ID_SEEDER).para_bytes())
        
        todas_pecas = set(range(TOTAL_PECAS))
        bits_bitfield = bitfield_de_pecas(todas_pecas, TOTAL_PECAS)
        conn.sendall(Bitfield(bits_bitfield).para_bytes())

        # 3. Loop de escuta do Seeder
        while True:
            msg = ler_mensagem(conn)
            print(msg)
            if not msg:
                break
                
            # Quando o client manda Interested, o Seeder responde Unchoke
            if msg.para_bytes()[4] == Id.INTERESTED:
                print("[+] SEEDER MOCK: Recebeu Interested. Enviando Unchoke!")
                conn.sendall(Unchoke().para_bytes())

            # Quando o client manda Request, o Seeder extrai os bytes e manda a Piece
            elif isinstance(msg, Request):
                peca = mapa_index_peca[msg.indice] # bloco
                bloco_dados = peca[msg.inicio: msg.inicio + msg.tamanho]
                resposta = Piece(msg.indice, msg.inicio, bloco_dados).para_bytes()
                print("PIECE", msg.indice)
                conn.sendall(resposta)

    except Exception as e:
        print(f"[-] SEEDER MOCK: Erro/Conexão encerrada: {e}")
    finally:
        conn.close()
        server.close()

if __name__ == "__main__":
    rodar_seeder()