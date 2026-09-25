import urllib3, json as j


def request(url): 
    http = urllib3.PoolManager()
    resposta = http.request("GET", url) 
    return resposta.data

