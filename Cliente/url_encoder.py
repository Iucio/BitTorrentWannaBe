from urllib.parse import urlencode, quote_from_bytes, parse_qs, urlparse
from info_hash import infhash

# A única função deste módulo é pegar todas as informações e formar a url

def url_encode(dic, peer_id, porta, uploaded, downloaded, left, event="started"):
    path = f"{dic["announce"]}?" # Caminho da url
    try:
        info_hash = infhash(dic) # Vem em bytes puro
        params = { # parâmetros da url
                "info_hash": quote_from_bytes(info_hash), # Transformo em percent-encoded. Padrão utilizado em urls.
                "peer_id": peer_id, 
                "port": porta,
                "uploaded": uploaded,
                "downloaded": downloaded,
                "left": left,
                "event": event,
                "private": dic["private"] 
                }
    except Exception as e:
        print(e)
        
    return path + urlencode(params) # Concatena as duas strings