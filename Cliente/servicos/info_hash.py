import hashlib
from servicos.parser import bencode

def infhash(dic):
    if type(dic) == dict:
        info_bencode = bencode(dic["info"]).encode('utf-8')
        raw = hashlib.sha1(info_bencode).digest()
        return raw # Bytes puros
    else:
        raise Exception("Erro: hash invalido")