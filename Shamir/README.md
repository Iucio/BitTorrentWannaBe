# Shamir

Divide um segredo em **n** partes (shares) de forma que **k** delas bastam para reconstruí-lo, e menos de k não revelam nada.

Vai ser usado para dividir a chave de criptografia dos arquivos entre os peers

## Como funciona

- Sorteia um polinômio de grau k−1 com o segredo no termo constante: `f(x) = S + a1·x + ... + a(k-1)·x^(k-1)  (mod p)`
- Cada share é um ponto `(x, f(x))`
- Com k pontos, a interpolação de Lagrange em `x = 0` devolve `S`
- Contas módulo `p = 10^9 + 7` (primo)

## Compilar e rodar

```bash
g++ -std=c++17 -O2 -o shamir shamir.cpp
./shamir
```


## Ver ainda 

- Chave do AES é 256 bits, com p=10^9+7 dá ~ 30 bits, mtt menos. Ver dps como resolver