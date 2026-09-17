# Calcula o info_hash

import hashlib
from GitHub.Tracker.parser import bencode

def hash(info):
    if type(info) == dict:
        info_bencode = bencode(info).encode('utf-8')
        return hashlib.sha1(info_bencode).digest()
    elif type(info) == str:
        return hashlib.sha1(info.encode('utf-8')).digest()
    elif type(info) == bytes:
        return hashlib.sha1(info).digest()