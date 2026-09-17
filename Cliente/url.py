import urllib3
from urllib.parse import urlencode, parse_qs, urlparse
from GitHub.Cliente.info_hash import hash



def url_encode(dic):
    path = f"{dic["announce"]}?" # Caminho
    try:
        params = {
            "info_hash": hash(dic["info"]),  # Caso seja um dicionario sem info_hash
            "peer_id": dic["peer_id"], 
            "port": dic["port"]
            }
    except:
        params = {
            "info_hash": dic["info_hash"], # Mantenho o info_hash originial
            "peer_id": dic["peer_id"], 
            "port": dic["port"]
            } 

    return path + urlencode(params) # Concatena as duas strings

def url_decode(url:str):
    parsed_url = urlparse(url) # Separa os argumentos (depois do '?') do caminho http://exemplo.com/announce
    path = parsed_url.path # Caminho dns ou IP EX: http://10.11.145.16/announce?info_hash= ou http://www.tracker.com/announce?info_hash=
    params = parsed_url.query # parâmetros depois do '?' na url
    dic = parse_qs(params, encoding="latin1") # Transformo em dicionário

    for chave, valor in dic.items(): # A função da biblioteca coloca tudo dentro de uma lista, não sei porque
        dic.update({chave: valor[0]}) # Faço isso para tirar o valor de dentro da lista
    
    dic["info_hash"] = dic["info_hash"].encode("latin1") # Transformo a string em bytes (info_hash deve ser visto como bytes puro)
    dic.update({"announce": path}) # Coloco o path da url dentro do dicionário

    return dic

def request(url): # AINDA A TESTAR!!!
    http = urllib3.PoolManager()

    resposta = http.request("GET", url)

    return resposta.data


############
### DEMO ###
############

url = "/announce?info_hash=%a4%1d%23%89%f0%11%b2%3a%4b%88%c1%de%90%fa%33%12%78%bc%99%00&peer_id=-PY0001-987654321098&port=6882"

print(f"url original:\n", url)
# Transformo a url em dicionario
dic = url_decode(url)
print(f"\ndicionario feito da url:\n", dic)

# Transformo o dicionario numa url
url2 = url_encode(dic)
print(f"\nurl feita do dicionario:\n", url2)

# O campo info_hash da url e da url2 são diferentes no print, entretanto, o conteúdo em bytes é o mesmo
# Isso acontece porque certos caractares foram convertidos em um e na outra não. Ex: %4b == 'k'.
# Como 'k' é um caracter aceito nas urls, ele foi convertido, portanto a url mudou o conteúdo de %4b para 'k',
# mas continua sendo o mesmo caracter.