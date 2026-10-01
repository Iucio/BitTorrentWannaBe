"""Mensagens do Peer Wire Protocol (tarefas 1.3.1, 1.3.2 e 1.3.3).

Funções para montar cada mensagem em bytes e ler de volta. Não guarda estado
e não depende de outros módulos do projeto.

Formato de todas as mensagens, exceto o handshake:

    <tamanho: 4 bytes> <id: 1 byte> <conteúdo: tamanho - 1 bytes>

Os números são big-endian (padrão em redes), por isso os formatos do `struct`
começam com ">". "I" é um inteiro de 4 bytes e "B" é 1 byte.
"""

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, Union

PROTOCOLO = b"BitTorrent protocol"
TAMANHO_HANDSHAKE = 1 + len(PROTOCOLO) + 8 + 20 + 20  # 68 bytes
TAMANHO_BLOCO = 16 * 1024  # tamanho padrão de um bloco pedido no REQUEST

# Maior mensagem aceita na leitura (um PIECE com bloco de até 128 KiB).
# Impede que um peer anuncie uma mensagem gigante e nos faça alocar memória sem limite.
LIMITE_MENSAGEM = 9 + 128 * 1024


class ErroProtocolo(Exception):
    """O peer enviou algo fora do protocolo. A conexão deve ser fechada."""


class Id(IntEnum):
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6
    PIECE = 7


# ---------------------------------------------------------------------------
# Handshake (1.3.1)
# ---------------------------------------------------------------------------

def _bytes20(valor: Union[bytes, str], nome: str) -> bytes:
    """info_hash e peer_id têm 20 bytes. Aceita str porque o peer_id do Cliente é texto."""
    if isinstance(valor, str):
        valor = valor.encode("latin1")
    if len(valor) != 20:
        raise ValueError(f"{nome} deve ter 20 bytes, recebeu {len(valor)}")
    return bytes(valor)


@dataclass(frozen=True)
class Handshake:
    """68 bytes fixos, sem prefixo de tamanho:

    | 1 byte | 19 bytes              | 8 bytes        | 20 bytes  | 20 bytes |
    | 19     | "BitTorrent protocol" | reservado (0s) | info_hash | peer_id  |
    """

    info_hash: bytes
    peer_id: bytes

    def __post_init__(self):
        # a classe é imutável (frozen), então a conversão usa object.__setattr__
        object.__setattr__(self, "info_hash", _bytes20(self.info_hash, "info_hash"))
        object.__setattr__(self, "peer_id", _bytes20(self.peer_id, "peer_id"))

    def para_bytes(self) -> bytes:
        return bytes([len(PROTOCOLO)]) + PROTOCOLO + bytes(8) + self.info_hash + self.peer_id


def decodificar_handshake(dados: bytes) -> Handshake:
    if len(dados) != TAMANHO_HANDSHAKE:
        raise ErroProtocolo(f"handshake deve ter {TAMANHO_HANDSHAKE} bytes, veio {len(dados)}")
    if dados[0] != len(PROTOCOLO) or dados[1:20] != PROTOCOLO:
        raise ErroProtocolo("handshake de outro protocolo")
    return Handshake(info_hash=dados[28:48], peer_id=dados[48:68])


# ---------------------------------------------------------------------------
# Mensagens (1.3.2 e 1.3.3)
# ---------------------------------------------------------------------------

def _com_tamanho(id_: Id, conteudo: bytes = b"") -> bytes:
    return struct.pack(">IB", 1 + len(conteudo), id_) + conteudo


@dataclass(frozen=True)
class Choke:
    """'Não vou atender seus pedidos.'"""

    def para_bytes(self) -> bytes:
        return _com_tamanho(Id.CHOKE)


@dataclass(frozen=True)
class Unchoke:
    """'Pode pedir.'"""

    def para_bytes(self) -> bytes:
        return _com_tamanho(Id.UNCHOKE)


@dataclass(frozen=True)
class Interested:
    """'Você tem peças que eu quero.'"""

    def para_bytes(self) -> bytes:
        return _com_tamanho(Id.INTERESTED)


@dataclass(frozen=True)
class NotInterested:
    """'Não quero nada seu.'"""

    def para_bytes(self) -> bytes:
        return _com_tamanho(Id.NOT_INTERESTED)


@dataclass(frozen=True)
class Have:
    """'Acabei de conseguir a peça `indice`.'"""

    indice: int

    def para_bytes(self) -> bytes:
        return _com_tamanho(Id.HAVE, struct.pack(">I", self.indice))


@dataclass(frozen=True)
class Bitfield:
    """'Estas são as peças que eu tenho', um bit por peça.

    Para montar a partir das peças: Bitfield(bitfield_de_pecas(pecas, numero_de_pecas)).
    Para ler as peças recebidas: pecas_do_bitfield(mensagem.bits, numero_de_pecas).
    """

    bits: bytes

    def para_bytes(self) -> bytes:
        return _com_tamanho(Id.BITFIELD, self.bits)


@dataclass(frozen=True)
class Request:
    """'Me envie `tamanho` bytes da peça `indice`, a partir do byte `inicio` dela.'"""

    indice: int
    inicio: int
    tamanho: int

    def para_bytes(self) -> bytes:
        return _com_tamanho(Id.REQUEST, struct.pack(">III", self.indice, self.inicio, self.tamanho))


@dataclass(frozen=True)
class Piece:
    """'Aqui está o trecho da peça `indice` que começa no byte `inicio`.'"""

    indice: int
    inicio: int
    bloco: bytes

    def para_bytes(self) -> bytes:
        return _com_tamanho(Id.PIECE, struct.pack(">II", self.indice, self.inicio) + self.bloco)


Mensagem = Union[Choke, Unchoke, Interested, NotInterested, Have, Bitfield, Request, Piece]


def decodificar(conteudo: bytes) -> Mensagem:
    """Transforma o que vem depois dos 4 bytes de tamanho numa mensagem.

    Lança ErroProtocolo se o id for desconhecido ou o tamanho não bater com o tipo.
    """
    if not conteudo:
        raise ErroProtocolo("mensagem vazia")

    id_, dados = conteudo[0], conteudo[1:]

    def exigir(tamanho: int):
        if len(dados) != tamanho:
            raise ErroProtocolo(f"mensagem id={id_} deveria ter {tamanho} bytes de conteúdo, "
                                f"veio {len(dados)}")

    if id_ == Id.CHOKE:
        exigir(0)
        return Choke()
    if id_ == Id.UNCHOKE:
        exigir(0)
        return Unchoke()
    if id_ == Id.INTERESTED:
        exigir(0)
        return Interested()
    if id_ == Id.NOT_INTERESTED:
        exigir(0)
        return NotInterested()
    if id_ == Id.HAVE:
        exigir(4)
        return Have(*struct.unpack(">I", dados))
    if id_ == Id.BITFIELD:
        return Bitfield(bytes(dados))  # o tamanho é conferido em pecas_do_bitfield
    if id_ == Id.REQUEST:
        exigir(12)
        return Request(*struct.unpack(">III", dados))
    if id_ == Id.PIECE:
        if len(dados) < 8:
            raise ErroProtocolo("PIECE sem índice e início")
        indice, inicio = struct.unpack(">II", dados[:8])
        return Piece(indice, inicio, bytes(dados[8:]))
    raise ErroProtocolo(f"id de mensagem desconhecido: {id_}")


# ---------------------------------------------------------------------------
# Bitfield
# ---------------------------------------------------------------------------

def bitfield_de_pecas(pecas: Iterable[int], numero_de_pecas: int) -> bytes:
    """Peça 0 é o bit mais à esquerda do primeiro byte. Ex.: peças {0, 1, 9} de 10 → C0 40."""
    bits = bytearray((numero_de_pecas + 7) // 8)
    for indice in pecas:
        if not 0 <= indice < numero_de_pecas:
            raise ValueError(f"peça {indice} fora do arquivo (0 a {numero_de_pecas - 1})")
        bits[indice // 8] |= 0x80 >> (indice % 8)
    return bytes(bits)


def pecas_do_bitfield(bits: bytes, numero_de_pecas: int) -> set:
    """Inverso de bitfield_de_pecas. Rejeita tamanho errado e bits de sobra ligados."""
    esperado = (numero_de_pecas + 7) // 8
    if len(bits) != esperado:
        raise ErroProtocolo(f"bitfield deveria ter {esperado} bytes, veio {len(bits)}")
    pecas = set()
    for indice in range(len(bits) * 8):
        if bits[indice // 8] & (0x80 >> (indice % 8)):
            if indice >= numero_de_pecas:
                raise ErroProtocolo("bitfield com bits ligados depois da última peça")
            pecas.add(indice)
    return pecas


# ---------------------------------------------------------------------------
# Leitura pelo socket
# ---------------------------------------------------------------------------

def recv_exato(sock, n: int) -> bytes:
    """Lê exatamente n bytes. O TCP pode entregar menos do que pedimos num recv."""
    partes = []
    faltam = n
    while faltam > 0:
        parte = sock.recv(min(faltam, 64 * 1024))
        if not parte:
            raise ConnectionError("o peer fechou a conexão")
        partes.append(parte)
        faltam -= len(parte)
    return b"".join(partes)


def ler_mensagem(sock, limite: int = LIMITE_MENSAGEM) -> Mensagem:
    """Lê uma mensagem completa: primeiro o tamanho, depois exatamente esse tanto de bytes."""
    (tamanho,) = struct.unpack(">I", recv_exato(sock, 4))
    if tamanho > limite:
        raise ErroProtocolo(f"mensagem de {tamanho} bytes passa do limite de {limite}")
    return decodificar(recv_exato(sock, tamanho))


def ler_handshake(sock) -> Handshake:
    return decodificar_handshake(recv_exato(sock, TAMANHO_HANDSHAKE))
