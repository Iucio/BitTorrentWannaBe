from urllib.parse import urlencode, parse_qs, urlparse
from .info_hash import hash
from Tracker.url_decoder import url_decode # import apenas para demonstração

# A única função deste módulo é pegar todas as informações e formar a url, apenas.

def url_encode(dic, peer_id, porta, uploaded, downloaded, left):
    path = f"{dic["announce"]}?" # Caminho da url
    try:
        info_hash = hash(dic["info"])
        params = { # parâmetros da url
                "info_hash": info_hash,  # Caso seja um dicionario sem info_hash
                "peer_id": peer_id, 
                "port": porta,
                "uploaded": uploaded,
                "downloaded": downloaded,
                "left": left,
                "private": dic["private"]
                }
    except Exception as e:
        print(e)
        
    return path + urlencode(params) # Concatena as duas strings