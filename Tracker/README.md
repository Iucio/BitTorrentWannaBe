# Tracker

Servidor responsável pela coordenação da rede e distribuição de peers como num BitTorrent
## Sobre o tracker

O Tracker mantém, para cada arquivo (identificado pelo `info_hash`), a lista de peers que estão participando do compartilhamento (swarm)

Periodicamente, cada cliente envia um **announce** ao Tracker informando quem é, em qual porta está escutando e quanto do arquivo ainda falta baixar, pode não ter nada, assim ele é um seeder na rede. Em resposta, o Tracker devolve o endereço (IP e porta) de outros peers do mesmo arquivo, para que os clientes se conectem diretamente entre si.

O Tracker não armazena nem transfere nenhum fragmento de arquivo: ele apenas indica quem possui o quê.

## Funcionalidades principais

- Servidor HTTP próprio (somente `GET`)
- Rota `/announce` (`/teste` só pra testes pequenos msm)
- Leitura e validação dos parâmetros do announce
- Registro de peers por `info_hash` (em memória)
- Tratamento dos eventos `started`, `completed` e `stopped`
- Contagem de seeders (`complete`) e leechers (`incomplete`)
- Respeito ao `min_interval` entre announces de rotina
- Expiração de peers que pararam de enviar announce
- Sorteio e limite (`numwant`) da lista de peers devolvida
- Resposta em JSON


## Tecnologias

- C++17
- CMake
- Sockets TCP
- HTTP

## Como compilar

É necessário um ambiente Linux (ou WSL) com `g++` e, opcionalmente, `cmake`.

Com CMake (recomendado, pq já define como compilr corretamente):

```bash
cd Tracker/cpp
cmake -S . -B build
cmake --build build
```

O executável fica em `Tracker/cpp/build/tracker`.

Sem CMake, direto com o `g++`:

```bash
cd Tracker/cpp
g++ -std=c++17 -O2 src/*.cpp -o tracker
```

## Como executar

```bash
./tracker [porta]
```

A porta padrão é a `80`, contudo, portas abaixo de 1024 exigem `sudo`, então para testes locais é mais prático usar outra:

```bash
./tracker 5023 
```
*Arbritario esse número

Cada requisição atendida aparece no terminal:

```text
[tracker] ouvindo em 0.0.0.0:5023
[tracker] 127.0.0.1 GET /announce -> 200
```

## Rota `/announce`

`GET /announce?info_hash=...&peer_id=...&port=...&left=...`

| Parâmetro    | Obrigatório | Descrição |
|--------------|-------------|-----------|
| `info_hash`  | sim | SHA-1 (20 bytes) do dicionário `info` do .torrent, em percent-encoding |
| `peer_id`    | sim | Identificador do cliente, 20 bytes |
| `port`       | sim | Porta em que o cliente aceita conexões de outros peers |
| `left`       | sim | Bytes que ainda faltam baixar (`0` = seeder) |
| `uploaded`   | não | Total de bytes enviados |
| `downloaded` | não | Total de bytes baixados |
| `event`      | não | `started`, `completed` ou `stopped`; omitido no announce de rotina |
| `numwant`    | não | Quantidade de peers desejada (padrão 50, máximo 50) |
| `ip`         | não | IP a ser divulgado; se omitido, usa o IP de quem conectou |

Exemplo com `curl`:

```bash
curl "http://127.0.0.1:5023/announce?info_hash=%C8%C9%CA%CB%CC%CD%CE%CF%D0%D1%D2%D3%D4%D5%D6%D7%D8%D9%DA%DB&peer_id=-UF0001-abcdefghijkl&port=6881&left=0&event=started"
```

## Resposta

Sucesso (`200`):

```json
{
  "interval": 1800,
  "min_interval": 900,
  "complete": 1,
  "incomplete": 2,
  "peers": [
    {"peer_id": "-UF0001-abcdefghijkl", "ip": "192.168.0.10", "port": 6881}
  ]
}
```

- `interval`: tempo (s) que o cliente deve esperar até o próximo announce
- `min_interval`: tempo mínimo (s) entre announces de rotina
- `complete` / `incomplete`: quantidade de seeders / leechers do arquivo
- `peers`: outros peers do mesmo `info_hash` (o próprio cliente não aparece)

Erro:

```json
{"failure_reason": "parametro ausente: info_hash"}
```

| Status | Quando |
|--------|--------|
| `200` + `failure_reason` | Regra do tracker violada (ex.: announce antes do `min_interval`) |
| `400` | Parâmetro ausente ou inválido, URL mal formada |
| `404` | Caminho desconhecido |
| `405` | Método diferente de `GET` |

## Configuração

Os valores padrão ficam na struct `Config`, em `src/announce.hpp`:

| Campo              | Padrão | Significado |
|--------------------|--------|-------------|
| `interval`         | 1800 s | Intervalo sugerido entre announces |
| `min_interval`     | 900 s  | Intervalo mínimo entre announces de rotina |
| `fator_expiracao`  | 2      | Peer sem announce há `interval × fator` é removido |
| `numwant_max`      | 50     | Máximo de peers por resposta |

## Limitações conhecidas

Esta é uma primeira versão. Pontos ainda em aberto:

- O servidor atende uma conexão por vez
- Ainda não há controle de acesso: qualquer cliente pode anunciar ou remover peers
- A rota `/teste` é provisória e responde igual à `/announce`

