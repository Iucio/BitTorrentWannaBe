# BitTorrentWannaBe

Sistema de compartilhamento de arquivos fragmentados em rede fechada, inspirado no funcionamento do BitTorrent.

Projeto desenvolvido para a disciplina de **Gerência de Projeto e Manutenção de Software (GPMS — TCC00363)** da Universidade Federal Fluminense.

## Sobre o projeto

O **BitTorrentWannaBe** implementa uma arquitetura distribuída de compartilhamento de arquivos formada por um **Tracker central** e múltiplos **Clientes/Peers**.

O Tracker coordena a entrada dos clientes na rede e a descoberta de peers, enquanto a transferência dos fragmentos ocorre diretamente entre os clientes por meio de conexões TCP.

Na versão final, o sistema também incorpora mecanismos de segurança e disponibilidade, como:

- autorização de clientes por chave de acesso;
- persistência de dados no Tracker com SQLite;
- fragmentação e transferência P2P;
- verificação de integridade dos fragmentos;
- proteção dos arquivos com **AES-256-GCM**;
- divisão da chave criptográfica com **Shamir Secret Sharing**;
- distribuição das partes da chave entre guardiões;
- mecanismos de **lockdown**, **heartbeat** e retentativas;
- painel de acompanhamento no terminal.

---

## Versão final — Rodada 3

A versão final do projeto foi integrada à `main` pelo **PR #46**.

**Baseline final:**

```text
main @ ce67e8f21586cfa5bd119ab4bb76630cafc33d1f
```

Publicada em **13/11/2026**.

Principais funcionalidades entregues:

- Parser Bencode;
- Tracker com persistência SQLite;
- cadastro, listagem e revogação de clientes;
- autorização de clientes por chave de acesso;
- announce Cliente → Tracker via HTTP;
- resposta do Tracker em JSON;
- descoberta de peers por `info_hash`;
- comunicação P2P por TCP;
- handshake entre peers;
- mensagens BITFIELD, INTERESTED, UNCHOKE, REQUEST e PIECE;
- serialização das mensagens HAVE e CHOKE;
- download incremental;
- upload de fragmentos;
- verificação de integridade por fragmento;
- escrita e reconstrução do arquivo em disco;
- criptografia AES-256-GCM;
- divisão da chave AES utilizando Shamir;
- distribuição das partes da chave entre guardiões da rede;
- lockdown em caso de indisponibilidade;
- heartbeat e retentativas;
- painel do cliente no terminal;
- compatibilidade do Tracker com Linux e Windows;
- testes de integração do fluxo final.

---

## Arquitetura

```text
                         +--------------------+
                         |      TRACKER       |
                         |--------------------|
                         | Autorização        |
                         | SQLite             |
                         | Swarms / Peers      |
                         | Guardiões          |
                         +---------+----------+
                                   |
                         HTTP / JSON
                                   |
             +---------------------+---------------------+
             |                                           |
             v                                           v
      +--------------+                           +--------------+
      |   Cliente A  | <------- TCP / P2P ------>|   Cliente B  |
      | Seeder/Peer  |                           | Leecher/Peer |
      +--------------+                           +--------------+
             |                                           |
             +-------------- Fragmentos -----------------+
```

O **Tracker não transfere o arquivo**. Ele coordena a rede, registra peers, valida as chaves de acesso e informa os endereços necessários.

A transferência do conteúdo ocorre diretamente entre os clientes.

---

## Fluxo de transferência

O fluxo básico entre Seeder, Tracker e Leecher é:

```text
Seeder
  |
  | announce + chave de acesso
  v
Tracker
  |
  | valida autorização
  | registra o peer
  v
Leecher
  |
  | announce
  | recebe lista de peers
  v
Seeder
  |
  | TCP
  | Handshake
  | BITFIELD
  | INTERESTED
  | UNCHOKE
  | REQUEST
  | PIECE
  v
Leecher
  |
  | valida fragmentos
  | grava em disco
  v
Arquivo reconstruído
```

---

## Segurança dos arquivos

A versão final utiliza **AES-256-GCM** para proteger o conteúdo dos arquivos.

Cada arquivo recebe uma chave AES própria. Essa chave não é armazenada diretamente: ela é dividida em `n` partes utilizando o algoritmo de **Shamir Secret Sharing**.

Apenas `k` dessas partes são necessárias para reconstruir a chave.

```text
Arquivo original
      |
      v
 AES-256-GCM
      |
      +--------------------> Arquivo cifrado
      |
      v
  Chave AES
      |
      v
    Shamir
      |
 +----+----+----+
 |    |    |    |
 v    v    v    v
P1   P2   P3   ... Pn
 |    |    |
 v    v    v
Peers guardiões
```

Cada parte pode ser armazenada por um peer guardião diferente.

Durante o download, o Leecher:

1. baixa o arquivo cifrado;
2. consulta os guardiões registrados no Tracker;
3. solicita as partes da chave;
4. reúne pelo menos `k` partes;
5. reconstrói a chave AES;
6. valida e decifra o arquivo com AES-GCM.

Mais detalhes em [`Shamir/README.md`](Shamir/README.md).

---

## Acesso à rede

Somente clientes cadastrados podem utilizar o Tracker.

O administrador cadastra um cliente diretamente na máquina onde o Tracker está sendo executado:

```bash
./tracker cadastrar "PC-Lab-03"
```

O Tracker gera uma chave de acesso:

```text
cliente 3 cadastrado: PC-Lab-03
chave de acesso: 9f2c41e8a0b7d35c6e14f0a2b8c97d61
```

Também é possível listar e revogar clientes:

```bash
./tracker clientes
./tracker revogar 3
```

O cliente envia sua chave em todos os announces por meio da variável de ambiente:

```bash
TRACKER_CHAVE=<chave>
```

Uma chave inexistente ou revogada faz com que o Tracker recuse o acesso.

Mais detalhes em [`Tracker/README.md`](Tracker/README.md).

---

## Tecnologias

### Cliente

- Python 3
- TCP Sockets
- HTTP
- Threads
- Bencode
- SHA-1
- AES-256-GCM
- Shamir Secret Sharing
- `cryptography`
- `urllib3`
- `progressbar2`

### Tracker

- C++17
- SQLite 3
- HTTP
- TCP Sockets
- CMake
- Ninja no ambiente Windows

### Gerência do projeto

- Git
- GitHub
- GitHub Issues
- GitHub Milestones
- Pull Requests
- Planning Poker
- Burndown
- Earned Value Management (EVM)

---

## Estrutura do repositório

```text
BitTorrentWannaBe/
├── Arquivo demo/
├── Cliente/
│   ├── Cliente.py
│   ├── GerenciadorDownload.py
│   ├── Sessao.py
│   ├── cliente_demo.py
│   ├── seeder_demo.py
│   ├── leecher_demo.py
│   ├── cifrar.py
│   ├── decifrar.py
│   ├── painel.py
│   ├── servicos/
│   └── testes/
├── Shamir/
│   ├── README.md
│   └── shamir.cpp
├── Tracker/
│   ├── README.md
│   └── cpp/
├── documentos/
│   ├── configuraçao/
│   ├── cronograma/
│   ├── eap/
│   ├── monitoramento/
│   ├── planejamento/
│   ├── riscos/
│   └── visao/
├── testes/
├── README.md
├── LICENSE
└── .gitignore
```

---

## Compilando o Tracker

### Linux / WSL

Instale as dependências:

```bash
sudo apt install g++ cmake libsqlite3-dev
```

Depois:

```bash
cd Tracker/cpp
cmake -S . -B build
cmake --build build
```

Execute, por exemplo, na porta `6969`:

```bash
./build/tracker 6969
```

### Windows

É necessário possuir MinGW-w64, CMake e Ninja.

```powershell
cd Tracker\cpp
cmake -S . -B build -G Ninja
cmake --build build
build\tracker.exe 6969
```

Caso o SQLite não esteja instalado, o CMake pode obtê-lo automaticamente durante a primeira compilação.

---

## Executando uma demonstração

### 1. Inicie o Tracker

```bash
cd Tracker/cpp
./build/tracker 6969
```

### 2. Cadastre os clientes

Abra outro terminal:

```bash
./build/tracker cadastrar "Cliente-01"
./build/tracker cadastrar "Cliente-02"
./build/tracker cadastrar "Cliente-03"
```

Guarde as chaves geradas.

---

### Download comum

Dentro de `Cliente/`, configure a chave e o endereço do Tracker.

Linux/macOS:

```bash
export TRACKER_URL=http://127.0.0.1:6969
export TRACKER_CHAVE=<chave>
```

Execute o Seeder:

```bash
python3 seeder_demo.py <arquivo> <torrent>
```

Em outro terminal, com outra chave cadastrada:

```bash
python3 leecher_demo.py <torrent>
```

---

## Demonstração com AES-GCM e Shamir

### 1. Cifre o arquivo

Dentro de `Cliente/`:

```bash
python3 cifrar.py video.mp4 3 2
```

Nesse exemplo:

- `n = 3`: são criadas três partes da chave;
- `k = 2`: duas partes são suficientes para reconstruir a chave.

São gerados:

```text
video.mp4.cifrado
video.mp4.cifrado.torrent

partes/
├── video.mp4.parte1
├── video.mp4.parte2
└── video.mp4.parte3
```

### 2. Inicie clientes que atuarão como guardiões

Em terminais diferentes:

```bash
python3 cliente_demo.py
```

Cada cliente deve possuir sua própria `TRACKER_CHAVE`.

### 3. Inicie o Seeder

```bash
python3 seeder_demo.py \
  video.mp4.cifrado \
  video.mp4.cifrado.torrent \
  partes/video.mp4.parte1 \
  partes/video.mp4.parte2 \
  partes/video.mp4.parte3
```

O Seeder mostra os clientes disponíveis e permite selecionar os guardiões das partes da chave.

### 4. Inicie o Leecher

```bash
python3 leecher_demo.py video.mp4.cifrado.torrent
```

O Leecher:

- baixa o arquivo cifrado;
- consulta os guardiões;
- solicita as partes da chave;
- reconstrói a chave;
- valida o AES-GCM;
- decifra o arquivo.

O arquivo aberto é salvo em:

```text
baixados/
```

---

## Painel do cliente

As demos possuem um painel no terminal para acompanhamento do estado do cliente e da transferência.

O painel pode ser desativado definindo:

```bash
PAINEL=0
```

---

## Lockdown, heartbeat e retentativas

O projeto possui mecanismos para lidar com indisponibilidade do Tracker e controle das conexões P2P.

Entre eles:

- heartbeat para verificar disponibilidade;
- novas tentativas de comunicação;
- mensagens CHOKE e UNCHOKE;
- lockdown de sessões;
- recuperação quando possível.

A eleição automática de um novo Tracker, considerada no escopo inicial, foi retirada da versão final.

---

## Testes

### Tracker

Após compilar:

```bash
cd Tracker/cpp/build
ctest --output-on-failure
```

Os testes do Tracker incluem cenários relacionados a:

- SQLite;
- persistência;
- peers e swarms;
- `info_hash`;
- `uploaded` e `downloaded`;
- cadastro de clientes;
- listagem;
- revogação;
- migração do banco.

Também existem testes do Cliente e do protocolo P2P nas pastas:

```text
Cliente/testes/
testes/
```

---

## Gerência de Configuração

O fluxo adotado na versão final foi:

```text
feature/*
    |
    v
 develop
    |
    | Pull Request + validação
    v
  main
```

### Branches

- `feature/*`: implementação isolada de funcionalidades;
- `develop`: integração e validação;
- `main`: baseline estável e entregável.

As alterações relevantes são registradas por meio de:

- Issues;
- responsáveis;
- critérios de aceite;
- Milestones;
- commits;
- Pull Requests;
- evidências de teste.

A versão final foi promovida da `develop` para a `main` pelo **PR #46**.

---

## Documentação do projeto

Os artefatos de planejamento e acompanhamento estão versionados em [`documentos/`](documentos/).

Entre os materiais produzidos estão:

- Documento de Visão;
- Plano de Projeto;
- EAP;
- Planning Poker;
- cronograma;
- análise de riscos;
- Burndown;
- EVM;
- Gerência de Configuração;
- registros das Rodadas 1, 2 e 3.

O plano final da Rodada 3 consolida a execução do projeto e a baseline publicada na `main`.

---

## Limitações conhecidas

A versão final possui algumas limitações formalmente registradas:

- o Tracker continua sendo um ponto central da arquitetura;
- existe apenas um Tracker ativo por vez;
- a eleição automática de um novo Tracker foi retirada do escopo;
- o broadcast completo de HAVE foi retirado do escopo final;
- a transferência final utiliza um Seeder por execução;
- o rodízio de fragmentos entre vários Seeders está registrado na **Issue #44** como evolução futura;
- a chave de acesso do Tracker trafega por HTTP;
- as partes Shamir são mantidas em memória pelos guardiões;
- o tráfego P2P das partes da chave não possui criptografia própria;
- a suíte Python legada não faz parte do critério final de aceite.

---

## Trabalhos futuros

Possíveis evoluções incluem:

- rodízio automático entre vários Seeders;
- HTTPS entre Cliente e Tracker;
- criptografia adicional da comunicação P2P;
- persistência das partes mantidas pelos guardiões;
- identificação persistente dos guardiões;
- proteção das branches;
- integração contínua (CI);
- automação da suíte de testes.

---

## Equipe

- Lucas Ardelino — Gerente de Projeto
- Felipe Gomes — Product Owner / Desenvolvedor
- Carlos Henrique Nascimento — Scrum Master / Desenvolvedor
- Lucio Diniz — Responsável por Configuração
- Vinicius Araújo — Desenvolvedor
- Luiz Eduardo — Desenvolvedor

---

## Licença

Este projeto é distribuído sob a licença **MIT**.

Consulte o arquivo [`LICENSE`](LICENSE) para mais informações.
