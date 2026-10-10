"""
Algoritmo de Shamir

Divide um segredo S em n chaves (x, y) de forma que k delas bastam para
reconstruí-lo, e menos de k não revelam nada. As contas são módulo p.
"""

import secrets

P = 2**521 - 1  # primo de Mersenne, cabe o AES de 128 e 256 tranquilo

def add(a, b, p):
    return (a % p + b % p) % p


def sub(a, b, p):
    return (a % p - b % p) % p  # em Python o % já dá não negativo


def mult(a, b, p):
    return (a % p) * (b % p) % p  # inteiro do Python não estoura, não precisa de long long


def binpow(a, b, p):
    ans = 1
    while b:
        if b & 1:
            ans = mult(ans, a, p)
        a = mult(a, a, p)
        b >>= 1
    return ans


def inv(a, p):
    return binpow(a, p - 2, p)


def eval(a, x, p):
    ans = 0
    xx = 1
    for aa in a:
        ans = add(ans, mult(aa, xx, p), p)
        xx = mult(xx, x, p)
    return ans


def gen_keys(S, n, k, p):
    a = [S] + [secrets.randbelow(p) for _ in range(k - 1)]
    if k > 1:
        a[k - 1] = 1 + secrets.randbelow(p - 1)  # nao_zero

    keys = set()
    while len(keys) < n:
        x = 1 + secrets.randbelow(p - 1)  # nao_zero
        y = eval(a, x, p)
        keys.add((x, y))
    return keys


def interpol(points, x, p):
    ps = list(points)
    k = len(ps)

    l = [1] * k
    for j in range(k):
        for i in range(k):
            if i != j:
                n = sub(x, ps[i][0], p)
                m = sub(ps[j][0], ps[i][0], p)
                l[j] = mult(l[j], mult(n, inv(m, p), p), p)

    L = 0
    for j in range(k):
        L = add(L, mult(ps[j][1], l[j], p), p)
    return L
