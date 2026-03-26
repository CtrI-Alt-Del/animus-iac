# Animus IAC

Repositorio de Infrastructure as Code do projeto **Animus**, responsavel por definir e operar a infraestrutura dos ambientes com **Pulumi** e **Python**.

O foco deste repositorio e descrever recursos de cloud e configuracoes de stack para os servicos usados pela aplicacao, com destaque para **GCP** e **Qdrant**.

## Visao Geral

O `animus-iac` centraliza a definicao da infraestrutura necessaria para os ambientes `stg` e `prod` do projeto. A modelagem de infra segue o que esta documentado em `documentation/infrastructure.md`, com GCP como base principal e servicos externos especializados quando necessario.

Principais responsabilidades do repositorio:

- provisionar e atualizar recursos no Google Cloud
- manter configuracoes separadas por stack Pulumi
- organizar a infraestrutura por contexto tecnico, como `gcp` e `qdrant`
- permitir `preview` e aplicacao de mudancas de forma reproduzivel

## Stack

- **Linguagem:** Python 3.13+
- **IaC:** Pulumi
- **Provider principal:** Pulumi GCP
- **Task runner:** Poe the Poet
- **Gerenciamento de dependencias:** uv

## Estrutura do Projeto

```text
.
├── Pulumi.yaml
├── Pulumi.stg.yaml
├── Pulumi.prod.yaml
├── pyproject.toml
├── documentation/
│   ├── architecture.md
│   └── infrastructure.md
└── src/
    ├── __main__.py
    └── animus/
        ├── gcp/
        └── qdrant/
```

## Ambientes

O projeto trabalha com duas stacks Pulumi:

- `stg`
- `prod`

Cada stack usa seu proprio arquivo de configuracao:

- `Pulumi.stg.yaml`
- `Pulumi.prod.yaml`

Hoje ambas compartilham configuracoes basicas de GCP, mas a expectativa e que evoluam para refletir diferencas reais de isolamento, capacidade e seguranca entre os ambientes.

## Comandos

Os atalhos operacionais definidos em `pyproject.toml` sao:

```bash
poe stg    # seleciona a stack stg
poe prod   # seleciona a stack prod
poe prev   # executa pulumi preview
poe up     # executa pulumi up --yes
```

Fluxo recomendado:

```bash
poe stg
poe prev
poe up
```

Ou para producao:

```bash
poe prod
poe prev
poe up
```

## Entry Point de Teste

O arquivo `src/__main__.py` atualmente contem um programa Pulumi minimo para validar o funcionamento das stacks.

Ele:

- le `gcp:project` e `gcp:region` da configuracao da stack
- identifica a stack atual
- exporta outputs simples para facilitar o teste do `preview` e do `up`

Exemplo de outputs esperados:

```text
stack: stg
gcp_project: animus
gcp_region: us-east
is_production: false
```

## Como Rodar

### Pre-requisitos

- Python 3.13+
- `uv` instalado
- Pulumi CLI instalado
- acesso ao backend de estado do Pulumi ja configurado

### Instalacao

```bash
uv sync
```

### Login no Pulumi

Antes de rodar os comandos de stack, faca login no backend de estado do Pulumi:

```bash
pulumi login
```

Se o projeto usar um backend especifico, execute o login com a URL correspondente.

### Autenticacao no GCP

Para que o provider do GCP consiga ler e provisionar recursos, voce precisa autenticar sua CLI local no Google Cloud.

Fluxo comum para desenvolvimento:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project animus
```

O que cada passo faz:

- `gcloud auth login`: autentica sua conta na CLI do Google Cloud
- `gcloud auth application-default login`: configura credenciais locais para bibliotecas e providers, incluindo o Pulumi GCP
- `gcloud config set project animus`: define o projeto padrao da sessao local

Se o acesso for feito por service account, exporte as credenciais de forma segura e sem commitar arquivos sensiveis no repositorio.

### Autenticacao no Qdrant

Se a stack ou scripts locais precisarem acessar o Qdrant Cloud, voce tambem precisa ter a URL do cluster e a API key do ambiente correto.

Fluxo recomendado:

- obter a URL do cluster Qdrant
- obter a API key correspondente ao ambiente (`stg` ou `prod`)
- carregar esses valores via Secret Manager, variaveis de ambiente ou config segura do Pulumi

Exemplo local com variaveis de ambiente:

```bash
export QDRANT_URL="https://<cluster>.cloud.qdrant.io"
export QDRANT_API_KEY="<api-key>"
```

Evite hardcodar URL, tokens ou secrets do Qdrant em `Pulumi.<stack>.yaml`, no codigo Python ou no repositorio.

### Criacao das stacks `stg` e `prod`

Depois de fazer login no Pulumi e autenticar o acesso ao GCP, voce pode criar os ambientes no estado do Pulumi.

Criar a stack de staging:

```bash
pulumi stack init stg
```

Criar a stack de producao:

```bash
pulumi stack init prod
```

Se os arquivos `Pulumi.stg.yaml` e `Pulumi.prod.yaml` ja existirem, o Pulumi passa a usar essas configuracoes quando a stack correspondente for selecionada.

Fluxo recomendado apos o login:

```bash
pulumi login
gcloud auth login
gcloud auth application-default login
gcloud config set project animus
pulumi stack init stg
pulumi stack init prod
poe stg
poe prev
```

Se a stack ja existir, `pulumi stack init` vai falhar informando que ela ja foi criada. Nesse caso, basta selecionar a stack com `poe stg` ou `poe prod`.

### Testar a stack

```bash
poe stg
poe prev
```

Para producao:

```bash
poe prod
poe prev
```

Se quiser persistir os outputs no estado da stack:

```bash
poe up
```

## Infraestrutura Alvo

Conforme `documentation/infrastructure.md`, a infraestrutura do projeto considera principalmente:

- **Google Cloud Run** para compute
- **Cloud SQL** para PostgreSQL
- **Cloud Memorystore** para Redis
- **Google Cloud Storage** para arquivos e artefatos
- **Artifact Registry** para imagens
- **Secret Manager** para segredos
- **Qdrant Cloud** para busca vetorial
- **Inngest Cloud** para jobs assincronos
- **OneSignal** para notificacoes push

## Documentacao

- `documentation/architecture.md`
- `documentation/infrastructure.md`

## Estado Atual

O repositorio ainda esta em fase inicial. Ja existem as stacks, os comandos operacionais e um entrypoint funcional de teste, mas os modulos de infraestrutura ainda precisam ser implementados.

Os proximos passos naturais sao:

1. estruturar modulos reais em `src/animus/gcp/` e `src/animus/qdrant/`
2. compor esses modulos em `src/__main__.py`
3. enriquecer as configs de `stg` e `prod` com diferencas reais por ambiente
