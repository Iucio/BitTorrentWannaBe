# Gerência de Configuração

## Estratégia de Branches

O projeto utiliza Git e GitHub para controle de versões e adota uma estratégia
de branches para separar o desenvolvimento da versão estável do sistema.

Durante a etapa inicial do projeto foram utilizadas principalmente as branches
`main` e `develop`. A partir da Rodada 2, o fluxo passa a incluir branches
específicas para o desenvolvimento de funcionalidades.

### Branch `main`

A branch `main` representa a versão estável e entregável do projeto.

Alterações de desenvolvimento não devem ser realizadas diretamente nessa branch.
A integração de mudanças ocorre por meio de Pull Requests.

### Branch `develop`

A branch `develop` é utilizada para integração das funcionalidades em
desenvolvimento.

As alterações concluídas nas branches de funcionalidades são integradas
primeiramente à `develop`.

### Branches de funcionalidades

A partir da Rodada 2, novas funcionalidades e tarefas de desenvolvimento devem,
sempre que possível, ser realizadas em branches próprias criadas a partir da
`develop`.

O padrão de nomenclatura adotado é:

`feature/nome-da-tarefa`

Exemplos:

- `feature/criar-tracker`
- `feature/cliente-p2p`
- `feature/handshake`
- `feature/verificacao-integridade`

Após a conclusão da tarefa, a branch de funcionalidade é integrada à `develop`
por meio de Pull Request.

### Fluxo de desenvolvimento

O fluxo adotado é:

`feature/* → develop → main`

A `develop` concentra o desenvolvimento em andamento, enquanto a `main` recebe
apenas versões consideradas estáveis e adequadas para entrega ou demonstração.

## Pull Requests

Os Pull Requests são utilizados para registrar e revisar a integração de mudanças
entre branches.

O fluxo esperado é:

1. desenvolvimento da tarefa em uma branch `feature/*`;
2. Pull Request da branch de funcionalidade para `develop`;
3. integração e validação das alterações;
4. Pull Request de `develop` para `main` quando uma versão estiver pronta para
   entrega ou demonstração.

## Commits

Os commits devem possuir mensagens objetivas que descrevam a alteração realizada.

Exemplos:

- `Adiciona estrutura inicial da documentação`
- `Implementa parser Bencode`
- `Corrige validação dos fragmentos`

## Controle de modificações

As tarefas e alterações do projeto são registradas por meio de GitHub Issues.

As Issues podem ser associadas a:

- responsável;
- milestone;
- labels;
- funcionalidade correspondente.

Esse mecanismo permite acompanhar o estado das atividades e manter o histórico
das modificações realizadas durante o projeto.

## Milestones

Os milestones são utilizados para agrupar Issues relacionadas às principais
etapas do projeto:

- `Planejamento e Documentação`;
- `Desenvolvimento do Sistema`;
- `Testes e Entrega`.

## Organização da documentação

A documentação do projeto é mantida dentro da pasta `documentos/`, organizada
por categorias:

- `configuracao/` — gerência de configuração e versionamento;
- `cronograma/` — cronograma e planejamento temporal;
- `eap/` — Estrutura Analítica do Projeto;
- `monitoramento/` — Burndown, EVM e acompanhamento;
- `planejamento/` — documentos gerais de planejamento;
- `riscos/` — identificação e gerenciamento de riscos;
- `slides/` — apresentações das rodadas;
- `visao/` — Documento de Visão.
