# Calcula o info_hash

import hashlib
from urllib.parse import quote_from_bytes
from parser import bencode

def hash(info):
    if type(info) == dict:
        info_bencode = bencode(info).encode('utf-8')
        raw = hashlib.sha1(info_bencode).digest()
        return quote_from_bytes(raw)
    else:
        raise Exception("Erro: tentativa de hash de um nao dicionario")