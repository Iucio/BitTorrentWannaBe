from urllib.parse import parse_qs, urlparse

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
