from url_encoder import url_encode

def request(dic, peer_id): 
    url = url_encode(dic, peer_id)
    return url # return para a demo
    #http = urllib3.PoolManager()
    #resposta = http.request("GET", url) 
    #return resposta.data

