from Cliente.parser import bencode
from Cliente.request import request
from Tracker.url_decoder import url_decode
import random
import string

def gerar_peer_id(): # Apenas para demo
    prefixo = "-UF0001-" # Identificao utilizada no protocolo, mas criei uma, pois é um trabalho de faculdade.
    randon_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=12))
    peer_id = prefixo + randon_bytes

    return peer_id

#dic_demo = {"announce":"11.23.54.232", "info": {"name": "exemplo.txt", "piece": "abcdefjk", "piece length": 262144}, "private": 1}

# Leitura do .Torrent
torrent = "d8:announce28:http://11.23.54.232:80/teste4:infod4:name11:exemplo.txt5:piece8:abcdefjk12:piece lengthi262144ee7:privatei1ee"

read_torrent = bencode(torrent)
print(f"dicionario formado pelo cliente ao ler o .Torrent:\n{read_torrent}\n")

# Criação da requisição ao tracker (obtido pelo torrent)
peer_id = gerar_peer_id()
req = request(read_torrent, peer_id)
print(f"url formada pelo cliente:\n{req}\n")

# Tracker recebe e decodifca a requisição
dic_tracker = url_decode(req)
print(f"dicionario formado pelo tracker, vindo da url do cliente:\n{dic_tracker}\n")