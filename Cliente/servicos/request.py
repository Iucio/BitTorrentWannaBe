import urllib3, time


def request_tracker(url,tentar_novamente=True): 
    http = urllib3.PoolManager()
    for _ in range(3):
        falha = False
        try:
            resposta = http.request("GET", url) 
            break
        except:
            falha = True
            if not tentar_novamente:
                break
            print(f"[BitTorrentWannaBe] Tracker falhou, tentando novamente...")
            continue
            
    if falha:
        return "failure reason"
    return resposta.json() # Transforma em dicionário