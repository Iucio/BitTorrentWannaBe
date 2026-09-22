import urllib3, random, string
from .url_encoder import url_encode

# É necessário decidir qual parte do cliente vai controlar a sessão.
# Quantos bytes faltam (left), quantos foram baixados (downloaded) e quantos bytes foram compartilhados na rede (uploaded).

def gerar_peer_id(): # Ainda não sei onde que vai ficar essa função.
    prefixo = "-UF0001-" # Identificao utilizada no protocolo, mas criei uma, pois é um trabalho de faculdade.
    randon_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=12))
    peer_id = prefixo + randon_bytes

    return peer_id

def request(dic, peer_id): 
    porta = 6767 # porta na qual o peer está escutando 
    uploaded = 0 # quantos bytes o peer fez upload nesta sessão
    downloaded = 0 # quantos bytes o peer fez download nesta sessão
    left = 0 # quantos bytes faltam para completar o download do arquivo especificado pelo info_hash
    url = url_encode(dic, peer_id, porta, uploaded, downloaded, left)
    return url # return para a demo
    #http = urllib3.PoolManager()
    #resposta = http.request("GET", url) 
    #return resposta.data

