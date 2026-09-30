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
- Registro de peers por `info_hash`, persistido em SQLite (sobrevive a reinícios)
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
- SQLite 3

## Como compilar

É necessário um ambiente Linux (ou WSL) com `g++`, a biblioteca de desenvolvimento do SQLite e, opcionalmente, `cmake`:

```bash
sudo apt install g++ cmake libsqlite3-dev
```

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
g++ -std=c++17 -O2 src/*.cpp -o tracker -lsqlite3
```

## Como executar

```bash
./tracker [porta] [banco]
```

A porta padrão é a `80`, contudo, portas abaixo de 1024 exigem `sudo`, então para testes locais é mais prático usar outra:

```bash
./tracker 5023 
```
*Arbritario esse número

O segundo argumento é o arquivo do banco SQLite (padrão `tracker.db`, na pasta de onde o Tracker foi executado). Se não existir, é criado com a tabela vazia. Os peers gravados continuam lá depois de reiniciar o Tracker, e os que passaram do prazo de expiração são removidos no próximo announce.

Cada requisição atendida aparece no terminal:

```text
[tracker] banco: tracker.db
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

## Banco de dados

O Tracker guarda os peers de cada swarm num banco SQLite embutido (`src/repositorio_sqlite.cpp`). O schema fica no início desse arquivo e é criado automaticamente na primeira execução:

| Coluna            | Tipo    | Descrição |
|-------------------|---------|-----------|
| `info_hash`       | BLOB    | SHA-1 do arquivo, 20 bytes crus (chave, junto com `peer_id`) |
| `peer_id`         | BLOB    | Identificador do cliente, 20 bytes |
| `ip`              | TEXT    | IP divulgado aos outros peers |
| `porta`           | INTEGER | Porta em que o peer aceita conexões |
| `left_bytes`      | INTEGER | Bytes que faltam (`0` = seeder); usado para `complete`/`incomplete` |
| `ultimo_announce` | INTEGER | Unix timestamp do último announce; usado no `min_interval` e na expiração |
| `uploaded`        | INTEGER | Bytes enviados pelo peer na sessão atual, como ele informa no announce |
| `downloaded`      | INTEGER | Bytes baixados pelo peer na sessão atual, como ele informa no announce |

A chave primária é `(info_hash, peer_id)`: um arquivo tem vários peers e um peer pode estar em vários arquivos. Como `info_hash` é a primeira coluna da chave, as buscas por arquivo já usam esse índice. `complete` e `incomplete` são calculados a cada announce, não gravados.

A versão do schema fica gravada no próprio arquivo (`PRAGMA user_version`, hoje `2`). Um `tracker.db` criado pela versão anterior, sem `uploaded`/`downloaded`, é atualizado automaticamente ao abrir o Tracker: os peers já gravados são mantidos e as colunas novas começam em zero.

Para inspecionar o banco (precisa do pacote `sqlite3`):

```bash
sqlite3 tracker.db "SELECT hex(info_hash), CAST(peer_id AS TEXT), ip, porta, left_bytes, datetime(ultimo_announce, 'unixepoch') FROM peers;"
```

### Ranking dos peers ativos

`uploaded` e `downloaded` permitem ver quem está compartilhando mais **entre os peers ativos no momento**. Como um peer aparece uma vez por arquivo, a consulta soma as linhas de cada `peer_id`:

```bash
sqlite3 tracker.db "SELECT CAST(peer_id AS TEXT) AS peer, SUM(uploaded) AS enviou, SUM(downloaded) AS baixou FROM peers GROUP BY peer_id ORDER BY enviou DESC;"
```

É uma visão de curto prazo, não um histórico:

- os valores são os totais da sessão atual do cliente e voltam a zero quando ele reinicia;
- um peer que sai com `event=stopped` é removido na hora e deixa de aparecer; um que cai sem avisar aparece até expirar;
- o `peer_id` é gerado a cada execução do cliente, então a mesma pessoa aparece como peers diferentes se reabrir o programa;
- os números são informados pelo próprio cliente, e o Tracker não tem como conferi-los.

## Testes

```bash
cd Tracker/cpp/build
ctest --output-on-failure    # ou ./teste_repositorio
```

Os testes rodam a mesma bateria no repositório em memória e no SQLite (inclui `info_hash` com byte nulo, gravação de `uploaded`/`downloaded`, contagem de seeders/leechers, `min_interval`, expiração, persistência depois de fechar o banco e migração de um banco da versão anterior).

## Limitações conhecidas

Esta é uma primeira versão. Pontos ainda em aberto:

- O servidor atende uma conexão por vez
- Ainda não há controle de acesso: qualquer cliente pode anunciar ou remover peers
- A rota `/teste` é provisória e responde igual à `/announce`

