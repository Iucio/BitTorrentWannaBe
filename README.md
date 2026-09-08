# BitTorrentWannaBe

Sistema de compartilhamento de arquivos fragmentados em rede fechada, desenvolvido para a disciplina de Gerência de Projeto e Manutenção de Software (GPMS).

## Sobre o projeto

O projeto propõe uma arquitetura baseada em **Tracker + Clientes (Peers)**, inspirada no modelo BitTorrent.

O Tracker é responsável pela coordenação da rede, controle de acesso e localização dos fragmentos, enquanto a transferência dos dados ocorre diretamente entre os clientes.

O diferencial do sistema é utilizar a fragmentação dos arquivos como uma camada adicional de proteção, evitando que um único nó da rede mantenha permanentemente uma cópia completa do arquivo.

## Funcionalidades principais

- Parser Bencode
- Comunicação entre Cliente e Tracker
- Comunicação Peer-to-Peer via TCP
- Handshake entre peers
- Mensagens BITFIELD, HAVE, INTERESTED, UNCHOKE, REQUEST e PIECE
- Download de fragmentos
- Verificação de integridade
- Reconstrução do arquivo
- Upload e distribuição de arquivos
- Controle básico de acesso à rede

## Estrutura do repositório

```text
BitTorrentWannaBe/
├── documentos/
│   ├── configuracao/
│   ├── cronograma/
│   ├── eap/
│   ├── monitoramento/
│   ├── planejamento/
│   ├── riscos/
│   ├── slides/
│   └── visao/
├── README.md
├── LICENSE
└── .gitignore ```

Tecnologias previstas
Python
TCP Sockets
HTTP
Bencode
SHA-1
Biblioteca struct
Documentação

Os artefatos produzidos ao longo da disciplina são mantidos na pasta documentos/, incluindo:

Documento de Visão
Plano de Projeto
EAP
Cronograma
Análise de riscos
Monitoramento e controle
Slides das rodadas
Documentação de gerência de configuração
Disciplina

Projeto desenvolvido para a disciplina GPMS — Gerência de Projeto e Manutenção de Software.

Licença

Este projeto está licenciado sob a licença MIT.