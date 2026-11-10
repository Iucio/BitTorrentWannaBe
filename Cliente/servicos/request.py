import urllib3, time


def request_tracker(url): 
    http = urllib3.PoolManager()
    for _ in range(3):
        falha = False
        try:
            resposta = http.request("GET", url) 
        except:
            time.sleep(1) # Espera 1 segundo antes de tentar novamente
            falha = True
            print(f"[BitTorrentWannaBe] Tracker falhou, tentando novamente...")
            continue
    if falha:
        return False
    return resposta.json() # Transforma em dicionário

