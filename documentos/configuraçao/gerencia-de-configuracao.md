# Gerência de Configuração

## Estratégia de Branches

O projeto utiliza Git e GitHub para controle de versões.

A estratégia de ramificação adotada utiliza duas branches principais:

- `main`
- `develop`

### Branch `main`

A branch `main` representa a versão estável e entregável do projeto.

Ela deve conter apenas versões consideradas adequadas para apresentação ou entrega.

As alterações não são desenvolvidas diretamente na `main`.

### Branch `develop`

A branch `develop` é utilizada para o desenvolvimento e integração das alterações realizadas pela equipe.

As novas funcionalidades, correções e atualizações de documentação são incorporadas inicialmente na `develop`.

Quando o conjunto de alterações é considerado estável, é aberto um Pull Request da `develop` para a `main`.

### Fluxo de desenvolvimento

O fluxo adotado pelo projeto é:

`develop → main`

A `develop` representa o estado atual de desenvolvimento do sistema, enquanto a `main` representa versões estáveis e entregáveis.

## Pull Requests

Os Pull Requests são utilizados para registrar a integração das alterações da branch `develop` para a branch `main`.

Antes do merge, as alterações devem ser revisadas para garantir que a versão integrada esteja adequada para entrega ou demonstração.

## Commits

Os commits devem possuir mensagens objetivas, descrevendo a alteração realizada.

Exemplos:

- `Adiciona estrutura inicial da documentação`
- `Implementa parser Bencode`
- `Atualiza análise de riscos`
- `Corrige comunicação com Tracker`

## Controle de Modificações

O projeto utiliza GitHub Issues para registrar e acompanhar tarefas, funcionalidades e alterações.

As Issues podem conter:

- responsável;
- milestone;
- labels;
- descrição da atividade;
- critérios de aceite;
- relacionamento com outras Issues.

As Issues concluídas são marcadas como fechadas, mantendo o histórico das atividades realizadas.

## Milestones

Os milestones são utilizados para agrupar Issues relacionadas às principais etapas do projeto:

- `Planejamento e Documentação`;
- `Desenvolvimento do Sistema`;
- `Testes e Entrega`.

## Organização da documentação

A documentação do projeto é mantida dentro da pasta `documentos/`, organizada por categorias:

- `configuracao/` — gerência de configuração e versionamento;
- `cronograma/` — cronograma e planejamento temporal;
- `eap/` — Estrutura Analítica do Projeto;
- `monitoramento/` — Burndown, EVM e acompanhamento;
- `planejamento/` — documentos gerais de planejamento;
- `riscos/` — identificação e gerenciamento de riscos;
- `slides/` — apresentações das rodadas;
- `visao/` — Documento de Visão.
