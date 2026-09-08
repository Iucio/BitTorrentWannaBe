# Gerência de Configuração

## Estratégia de Branches

O projeto utilizará uma estratégia de branches para organizar o desenvolvimento
e evitar alterações diretas na versão principal.

### Branch main

A branch `main` representa a versão principal e estável do projeto.

Não devem ser realizadas alterações diretamente na branch `main`.

### Branch develop

A branch `develop` será utilizada para o desenvolvimento e integração das
funcionalidades do projeto.

As alterações realizadas nas branches de funcionalidades serão integradas
primeiramente na `develop`.

### Branches de funcionalidades

Cada tarefa ou funcionalidade deverá ser desenvolvida em uma branch própria,
criada a partir da branch `develop`.

O padrão de nomenclatura será:

`feature/nome-da-tarefa`

Exemplos:

- `feature/criar-tracker`
- `feature/criar-cliente-p2p`
- `feature/comunicacao`
- `feature/testes`

Após a conclusão da tarefa, a branch `feature` deverá ser integrada à branch
`develop`.

### Fluxo de desenvolvimento

O fluxo definido para o projeto será:

`feature/* → develop → main`

A branch `main` receberá somente versões consideradas estáveis do projeto.

## Commits

Os commits deverão possuir mensagens objetivas, descrevendo a alteração
realizada.

Exemplo:

`Adiciona estrutura inicial da documentação`

## Organização da documentação

A documentação do projeto será mantida dentro da pasta `documentos/`,
organizada por categorias.

Estrutura prevista:

- `configuracao/` — documentos relacionados à configuração e gerenciamento do projeto;
- `cronograma/` — cronograma e planejamento temporal;
- `eap/` — Estrutura Analítica do Projeto;
- `monitoramento/` — acompanhamento do projeto;
- `planejamento/` — documentos de planejamento;
- `riscos/` — identificação e gerenciamento de riscos;
- `slides/` — apresentações;
- `visao/` — Documento de Visão e documentos relacionados.
