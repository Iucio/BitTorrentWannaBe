import urllib3


def request_tracker(url): 
    http = urllib3.PoolManager()
    resposta = http.request("GET", url) 
    return resposta.json() # Transforma em dicionário

