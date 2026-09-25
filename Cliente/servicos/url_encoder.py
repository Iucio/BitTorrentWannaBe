from urllib.parse import urlencode, quote_from_bytes
import Sessao

# A única função deste módulo é pegar todas as informações e formar a url

def url_encode(sessao:Sessao, porta, peer_id, event=""):
    path = f"{sessao.tracker}?" # Caminho da url
    params = { # parâmetros da url
        "info_hash": quote_from_bytes(sessao.info_hash), # Transformo em percent-encoded. Padrão utilizado em urls.
        "peer_id": peer_id, 
        "port": porta,
        "uploaded": sessao.uploaded,
        "downloaded": sessao.downloaded,
        "left": sessao.left,
        "private": sessao.private
    }
    if event:
        params.update({"event": event})
        
    return path + urlencode(params) # Concatena as duas strings