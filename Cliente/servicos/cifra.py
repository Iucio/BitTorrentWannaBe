"""
Cifra dos arquivos com AES-GCM e divisão da chave com o shamir

O arquivo cifrado é: 

    nonce (12 bytes) -> segurança extra
    dados cifrados
    tag (16 bytes) -> Integridade (um MAC)

"""

import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from servicos.shamir import P, gen_keys, interpol

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


def decifrar_arquivo(origem, destino, chave):
    """Levanta exceção se a chave ou o arquivo estiverem errados."""
    with open(origem, "rb") as f:
        dados = f.read()
    nonce, cifrado = dados[:tam_nonce], dados[tam_nonce:]
    aberto = AESGCM(chave).decrypt(nonce, cifrado, None)  # conferir a tag
    with open(destino, "wb") as f:
        f.write(aberto)


def dividir_chave(chave, n, k):
    """n partes (x, y) da chave; quaisquer k delas remontam."""
    return gen_keys(int.from_bytes(chave, "big"), n, k, P)


def juntar_chave(partes):
    """Recusa partes erradas ou a menos. O que escapar, o GCM recusa ao decifrar."""
    segredo = interpol(partes, 0, P)
    if segredo.bit_length() > 8 * tam_chave:
        raise ValueError("as partes não formam a chave (erradas ou a menos)")
    return segredo.to_bytes(tam_chave, "big")


# Parte em arquivo do uploader q envia dps pra cada peer
# hexadecimal, padrão da criptografia
def salvar_parte(parte, caminho):
    x, y = parte
    with open(caminho, "w") as f:
        f.write(f"{x:x} {y:x}\n")

# Le e passa de volta para int
def ler_parte(caminho):
    with open(caminho) as f:
        x, y = f.read().split()
    return int(x, 16), int(y, 16)
