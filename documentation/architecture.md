# Arquitetura do Projeto Animus IAC

## Visao Geral

O `animus-iac` e o repositorio de Infrastructure as Code do projeto Animus. Ele usa
**Pulumi com runtime Python** para descrever, provisionar e atualizar a infraestrutura
necessaria para os ambientes da aplicacao.

O objetivo deste repositorio nao e implementar a logica da API, mas sim centralizar a
definicao declarativa de recursos de cloud, configuracoes por stack e a composicao de
servicos compartilhados entre ambientes.

## Objetivos Arquiteturais

- **Infraestrutura versionada**: toda mudanca de infra deve passar por codigo, review e historico em git.
- **Composicao por dominio de infraestrutura**: recursos devem ser organizados por contexto tecnico, como `gcp` e `qdrant`.
- **Separacao por stack**: cada ambiente usa sua propria stack Pulumi (`stg`, `prod`) com configuracoes isoladas.
- **Reprodutibilidade**: a mesma base de codigo deve permitir `preview` e `up` de forma previsivel entre ambientes.
- **Baixo acoplamento**: a definicao dos recursos deve evitar espalhar configuracao hardcoded pelo codigo.

## Modelo do Projeto

O projeto segue um modelo simples de entrada unica do Pulumi:

- `Pulumi.yaml`: define o projeto Pulumi, runtime e ponto de entrada.
- `Pulumi.stg.yaml`: configuracao da stack de staging.
- `Pulumi.prod.yaml`: configuracao da stack de producao.
- `pyproject.toml`: dependencias Python e comandos operacionais via Poe.
- `src/`: codigo Python usado para declarar os recursos.

## Estrutura Atual

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

## Responsabilidades por Area

- **`src/__main__.py`**: ponto de composicao da stack; deve instanciar e conectar os modulos de infraestrutura.
- **`src/animus/gcp/`**: recursos nativos do Google Cloud, como Cloud Run, Cloud SQL, Memorystore, GCS, Artifact Registry e Secret Manager.
- **`src/animus/qdrant/`**: recursos, configuracoes ou integracoes relacionadas ao Qdrant Cloud.
- **`Pulumi.<stack>.yaml`**: parametros por ambiente, como projeto, regiao, nomes, tamanhos ou flags de comportamento.

## Relacao com a Infraestrutura do Produto

De acordo com `documentation/infrastructure.md`, a infraestrutura alvo do Animus e centrada em GCP,
com integracoes externas para casos especificos:

- **GCP** como base principal de compute, dados, artefatos e segredos.
- **Qdrant Cloud** para busca vetorial.
- **Inngest Cloud** para jobs assincronos.
- **OneSignal** para notificacoes push.

Este repositorio deve refletir essa divisao, mantendo no codigo de infra apenas a modelagem dos
recursos, dependencias e configuracoes operacionais desses servicos.

## Stacks e Ambientes

Hoje o projeto trabalha com as stacks:

- `stg`
- `prod`

Cada stack representa um ambiente independente no Pulumi. A separacao de ambiente deve acontecer
principalmente por:

- arquivos `Pulumi.<stack>.yaml`
- nomes/prefixos de recursos
- configuracoes de capacidade e protecao
- segredos e integracoes externas especificas por ambiente

Se duas stacks tiverem exatamente a mesma configuracao, a separacao existe no Pulumi, mas o valor
arquitetural dela fica reduzido. O ideal e que staging e producao tenham diferencas explicitas
quando houver requisitos distintos de isolamento, custo ou seguranca.

## Fluxo Operacional

Os comandos definidos em `pyproject.toml` expõem o fluxo basico de trabalho:

- `poe stg`: seleciona a stack `stg`
- `poe prod`: seleciona a stack `prod`
- `poe prev`: executa `pulumi preview`
- `poe up`: executa `pulumi up --yes`

Fluxo recomendado:

```text
selecionar stack -> revisar mudancas com preview -> aplicar com pulumi up
```

## Padroes Recomendados para Evolucao

- **Modulos pequenos e coesos**: cada arquivo/modulo deve agrupar recursos de um mesmo contexto.
- **Configuracao dirigida por stack**: evitar valores fixos no codigo quando eles variam por ambiente.
- **Exports claros**: outputs do Pulumi devem expor apenas informacoes uteis para operacao e integracao.
- **Dependencias explicitas**: quando um recurso depende de outro, a relacao deve ser visivel no codigo.
- **Nomes previsiveis**: padronizar nomes de recursos para facilitar operacao, auditoria e troubleshooting.

## Armadilhas a Evitar

1. Duplicar definicoes de recurso entre stacks em vez de parametrizar.
2. Hardcodar projeto, regiao, nomes ou secrets diretamente no codigo Python.
3. Misturar infraestrutura de ambientes diferentes sem prefixo, convencao ou isolamento claro.
4. Deixar `preview` e `up` dependerem de ajustes manuais fora do Pulumi.
5. Acoplar a estrutura do repositorio a um servico especifico de forma que dificulte expansao futura.

## Stack Tecnologica

| Tecnologia | Finalidade |
|---|---|
| **Python 3.13+** | Runtime do projeto IaC |
| **Pulumi** | Definicao e orquestracao da infraestrutura |
| **Pulumi GCP** | Provider para recursos do Google Cloud |
| **Poe the Poet** | Atalhos de comandos operacionais |
| **uv** | Execucao e gerenciamento de dependencias Python |
