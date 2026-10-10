"""
Cifra dos arquivos com AES-GCM e divisão da chave com o shamir

O arquivo cifrado é: 

    nonce (12 bytes) -> segurança extra
    dados cifrados
    tag (16 bytes) -> Integridade (um MAC)

"""

import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

tam_chave = 32  # AES-256
tam_nonce = 12


def gerar_chave():
    return AESGCM.generate_key(bit_length=8 * tam_chave)


def cifrar_arquivo(origem, destino, chave):
    with open(origem, "rb") as f:
        dados = f.read()
    nonce = secrets.token_bytes(tam_nonce)  # cada arquivo tem chave própria, então o nonce nunca repete
    with open(destino, "wb") as f:
        f.write(nonce + AESGCM(chave).encrypt(nonce, dados, None))
