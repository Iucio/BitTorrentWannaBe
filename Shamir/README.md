# Shamir

Divide um segredo em **n** partes (shares) de forma que **k** delas bastam para reconstruí-lo, e menos de k não revelam nada.

É usado para dividir a chave AES-256 de cada arquivo cifrado entre os peers: o arquivo só abre com k partes juntas. Cada parte fica com um **guardião**, um cliente da rede escolhido pelo seeder.

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

As partes pela rede ficam em `Cliente/servicos/partes.py` (o guardião e as funções de entregar e pedir parte), e a cifra em `Cliente/servicos/cifra.py`.

## Partes pela rede (guardiões)

Todo cliente pode ser guardião, mas só vira guardião de um arquivo quando o seeder o escolhe no announce. Quem decide é o seeder, arquivo por arquivo: um guardião só tem poder sobre o que um seeder confiou a ele.

```text
1. todo cliente ligado entra na SALA       -> lista de quem pode ser escolhido
2. seeder lista a SALA e escolhe B, C, E   -> manda guardioes=B,C,E no announce started do arquivo
3. Tracker registra os guardiões do arquivo (tabela guardioes)
4. seeder entrega uma parte pra cada um    -> GuardarParte; o guardião confirma devolvendo a parte
5. leecher baixa o cifrado                 -> como qualquer arquivo
6. leecher pede /guardioes do arquivo      -> Tracker devolve os guardiões ligados, com o endereço atual
7. leecher pede a parte a cada um          -> PedirParte; tem que ser antes do shutdown
8. leecher junta k partes e decifra        -> baixados/
```

**Regras do guardião** (`Guardiao` em `partes.py`):

- Só **guarda** se quem manda está no swarm do arquivo e o dono do arquivo o escolheu (ele aparece em `/guardioes`). Parte que já tem não é trocada.
- Só **entrega** pra quem o Tracker diz que está no swarm do arquivo. O aceite pode ficar mais elaborado depois, mas por enquanto só garante que quem pede está no swarm do Tracker da rede privada.
- Em qualquer recusa, fecha a conexão sem responder.
- A regra de entrega fica numa função só (`pode_entregar`), onde entram regras personalizadas no futuro.

**SALA** é um `info_hash` inventado (`SHA1("BitTorrentWannaBe sala")`) que não é de arquivo nenhum. Todo cliente ligado faz announce nele, então o Tracker tem o endereço atual de cada um e o seeder enxerga quem está ligado. Pro Tracker é um swarm como outro qualquer.

**Protocolo**: três mensagens novas no Peer Wire (ids 30, 31 e 32: `GuardarParte`, `PedirParte`, `Parte`, com x e y em 66 bytes cada) e o 1 bit reservado do handshake ligado, que avisa que a conexão é de partes e não de peças. O BitTorrent usa esses bits do mesmo jeito, pra avisar extensões.

### Demo numa máquina

Com o Tracker ligado (`./tracker 6969`) e um cliente cadastrado pra cada terminal (`TRACKER_CHAVE`), dentro de `Cliente/`:

```bash
python3 cliente_demo.py                       # em 3 terminais: clientes ligados que podem ser escolhidos
python3 cifrar.py video.mp4 3 2               # 3 partes, 2 abrem
python3 seeder_demo.py video.mp4.cifrado video.mp4.cifrado.torrent partes/video.mp4.parte1 partes/video.mp4.parte2 partes/video.mp4.parte3
python3 leecher_demo.py video.mp4.cifrado.torrent
```

O seeder mostra a SALA numerada e pergunta quem guarda as partes (de k a n números). O leecher baixa, pede as partes e termina com `arquivo aberto em baixados/video.mp4`. Com menos de k guardiões ligados, avisa quantas partes conseguiu. Arquivos `.parte` passados ao leecher completam o que faltar, sem contar a mesma parte duas vezes.

## Cifrar e abrir sem a rede

```bash
python3 cifrar.py video.mp4 3 2   # n = 3 partes, k = 2 abrem (padrão)
```

Gera:

- `video.mp4.cifrado`: o arquivo cifrado com AES-256-GCM (nonce + dados + tag)
- `video.mp4.cifrado.torrent`: o .torrent do cifrado, com `k` e `n` dentro do `info`
- `partes/video.mp4.parte1` ... `parte3`: as partes da chave, em texto `x y` (hexadecimal)

A chave em si não é salva em lugar nenhum. O seeder continua com as partes depois de entregar. Para abrir um arquivo baixado com os arquivos de parte:

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

- Quem abriu o arquivo pode repassar o arquivo ou a chave dele: nenhum software impede isso
- Basta estar no swarm do arquivo pra receber a parte; não existe ainda lista de quem pode abrir
- O tráfego entre peers não é cifrado: quem escuta a rede pode copiar uma parte em trânsito
- O guardião guarda as partes só na memória e o `peer_id` muda a cada execução: se ele reiniciar, perde o papel. O seeder mantém as partes e pode escolher outro
- O cliente ainda não faz announce periódico: quem fica ligado mais de 1 h sem novo announce some da SALA e do `/guardioes`
- O Shamir sozinho não percebe parte adulterada: quem garante é a tag do AES-GCM, que recusa a chave errada

## Trabalhos futuros

- Regras personalizadas pro guardião decidir se entrega (lista de quem o seeder liberou, aprovação manual, limite de pedidos), na função `pode_entregar`
- Rota de presença (heartbeat) no lugar da SALA, junto com o alerta de lockdown
- Identificar o guardião pelo cadastro no Tracker, e não pelo `peer_id`, pra ele sobreviver a reinícios
- Shamir verificável (Feldman/Pedersen), pra detectar parte adulterada antes de decifrar
