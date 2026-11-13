# BitTorrentWannaBe

Projeto desenvolvido para a disciplina de **Gerência de Projeto e Manutenção de Software (GPMS)**.

## Sobre o projeto

O **BitTorrentWannaBe** é um sistema de compartilhamento de arquivos fragmentados em rede fechada, inspirado no funcionamento do BitTorrent.

A arquitetura é composta por:

- **Tracker**: registra peers e informa quais clientes possuem determinado arquivo;
- **Clientes/Peers**: realizam a transferência direta dos fragmentos entre si.

A comunicação Cliente–Tracker utiliza HTTP, enquanto a comunicação entre peers ocorre via TCP.

---

## Estado da Rodada 2

Na Rodada 2 foi entregue um MVP funcional com:

- comunicação Cliente–Tracker;
- registro de peers por `info_hash`;
- persistência no Tracker com SQLite;
- comunicação Peer-to-Peer via TCP;
- handshake entre peers;
- mensagens BITFIELD, INTERESTED, UNCHOKE, REQUEST e PIECE;
- upload e download de fragmentos;
- validação de integridade das peças;
- escrita do arquivo em disco;
- funcionamento de Seeder e Leecher;
- testes de Bencode, Tracker e mensagens P2P.

### Depois da Rodada 2

- cadastro e autorização de clientes na rede: só entra quem tem chave de acesso (ver [Acesso à rede](#acesso-à-rede)).

---

## Estrutura do repositório

```text
BitTorrentWannaBe/
├── Arquivo demo/
├── Cliente/
├── Tracker/
├── documentos/
│   ├── configuraçao/
│   ├── cronograma/
│   ├── eap/
│   ├── monitoramento/
│   ├── planejamento/
│   ├── riscos/
│   └── visao/
├── README.md
├── LICENSE
└── .gitignore
```

---

## Tecnologias

### Cliente
- Python
- TCP Sockets
- HTTP
- Bencode
- SHA-1
- Threads

### Tracker
- C++
- SQLite
- HTTP
- TCP Sockets
- CMake

### Gerência do projeto
- Git
- GitHub
- GitHub Issues
- GitHub Milestones
- Pull Requests

---

## Gerência de Configuração

O projeto utiliza duas branches principais:

- `main`: versão estável e entregável;
- `develop`: desenvolvimento e integração das alterações.

Fluxo principal:

```text
develop → Pull Request → main
```

As modificações são acompanhadas por meio de **Issues**, **Milestones** e **Pull Requests**, mantendo o histórico das atividades e das integrações realizadas.

---

## Documentação da Rodada 2

Os principais artefatos estão disponíveis em `documentos/`:

- `documentos/monitoramento/burndown2.pdf`
- `documentos/monitoramento/evm2.pdf`
- `documentos/cronograma/cronograma2.pdf`
- `documentos/riscos/riscos2.pdf`
- `documentos/eap/eap2.pdf`
- `documentos/planejamento/PLANO_DE_PROJETO_BITTORRENT2.docx.pdf`
- `documentos/configuraçao/gerencia-de-configuracao.md`

---

## Acesso à rede

Só entra na rede quem foi cadastrado no Tracker. O admin cadastra cada cliente na máquina do Tracker e entrega a chave mostrada:

```bash
./tracker cadastrar "PC-Lab-03"
```

O cliente manda essa chave em todo announce, pela variável `TRACKER_CHAVE` (dentro de `Cliente/`):

```bash
TRACKER_CHAVE=<chave> python3 seeder_demo.py <arquivo> <torrent>
TRACKER_CHAVE=<chave> python3 leecher_demo.py <torrent>
```

Sem chave, com chave errada ou revogada (`./tracker revogar <id>`), o Tracker recusa e o cliente encerra com `Tracker recusou: ...`. Detalhes em [Tracker/README.md](Tracker/README.md#cadastro-de-clientes).

---

## Fluxo demonstrado

```text
Seeder
  |
  | announce (com a chave)
  v
Tracker
  |
  | lista de peers
  v
Leecher
  |
  | TCP + handshake
  v
Seeder
  |
  | BITFIELD
  | INTERESTED
  | UNCHOKE
  | REQUEST
  | PIECE
  v
Download + validação + gravação em disco
```

---

## Licença

Este projeto está licenciado sob a licença MIT.
