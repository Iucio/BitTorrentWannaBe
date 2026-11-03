# Shamir

Divide um segredo em **n** partes (shares) de forma que **k** delas bastam para reconstruí-lo, e menos de k não revelam nada.

É usado para dividir a chave AES-256 de cada arquivo cifrado entre os peers: o arquivo só abre com k partes juntas.

## Como funciona

- Sorteia um polinômio de grau k−1 com o segredo no termo constante: `f(x) = S + a1·x + ... + a(k-1)·x^(k-1)  (mod p)`
- Cada share é um ponto `(x, f(x))`, com x sorteado (nunca 0)
- Com k pontos, a interpolação de Lagrange em `x = 0` devolve `S`
- Contas módulo um primo `p`

## Onde está

| Arquivo | O que é | p |
|---------|---------|---|
| `Shamir/shamir.cpp` | Versão de estudo, com menu no terminal | `10^9 + 7` |
| `Cliente/servicos/shamir.py` | Mesmas funções (`gen_keys`, `interpol`...), usada pelo cliente | `2^521 − 1` |

O p do C++ só cabe segredo de ~30 bits. No Python o p é o primo de Mersenne `2^521 − 1`, maior que a chave do AES (256 bits).

## Cifrar e abrir um arquivo

Dentro de `Cliente/`:

```bash
python3 cifrar.py video.mp4 3 2   # n = 3 partes, k = 2 abrem (padrão)
```

Gera:

- `video.mp4.cifrado`: o arquivo cifrado com AES-256-GCM (nonce + dados + tag)
- `video.mp4.cifrado.torrent`: o .torrent do cifrado, com `k` e `n` dentro do `info`
- `partes/video.mp4.parte1` ... `parte3`: as partes da chave, em texto `x y` (hexadecimal)

A chave em si não é salva em lugar nenhum. Para abrir o arquivo baixado:

```bash
python3 decifrar.py arquivo_final.bin video.mp4.cifrado.torrent partes/video.mp4.parte1 partes/video.mp4.parte3
```

Abre em `baixados/video.mp4`. Com mais de k partes, testa as combinações até uma abrir, então uma parte errada no meio não atrapalha. Com menos de k, ou só partes erradas, recusa.

## Compilar e rodar (C++)

```bash
g++ -std=c++17 -O2 -o shamir shamir.cpp
./shamir
```

## Limitações

- As n partes ficam todas na pasta `partes/` de quem cifrou; entregar cada uma para um peer diferente ainda é manual
- O Shamir sozinho não percebe parte adulterada: quem garante é a tag do AES-GCM, que recusa a chave errada
