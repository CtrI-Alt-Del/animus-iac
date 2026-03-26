# Infraestrutura do Animus Server

## Visao Geral

A infraestrutura do Animus Server e hospedada predominantemente no **Google Cloud Platform (GCP)**,
com servicos externos gerenciados para orquestracao de jobs, notificacoes push e banco de vetores.
A escolha do GCP como plataforma principal garante comunicacao interna via rede privada,
IAM unificado e faturamento centralizado entre os servicos.

---

## Servicos

### Compute

| Servico | Plataforma | Responsabilidade |
|---|---|---|
| **API Server** | Google Cloud Run | Executa a aplicacao FastAPI em container. Auto-scaling elastico por demanda. |

### Dados

| Servico | Plataforma | Responsabilidade |
|---|---|---|
| **PostgreSQL** | Google Cloud SQL | Persistencia relacional principal: usuarios, analises, sessoes e historico. |
| **Redis** | Google Cloud Memorystore | Cache de resultados de busca semantica. |
| **File Storage** | Google Cloud Storage (GCS) | Armazenamento de PDFs de peticoes e documentos enviados pelo usuario. Tambem armazena artefatos de modelos ML. |

### DevOps

| Servico | Plataforma | Responsabilidade |
|---|---|---|
| **CI/CD** | GitHub Actions | Pipeline de build, testes e push de imagens ao registry. |
| **Container Registry** | Google Artifact Registry | Armazenamento e versionamento de imagens Docker da aplicacao. |

### Seguranca

| Servico | Plataforma | Responsabilidade |
|---|---|---|
| **Secrets** | Google Secret Manager | Gerenciamento de credenciais, connection strings e API keys. Injetado no Cloud Run como variaveis de ambiente. |

### Servicos Externos

| Servico | Plataforma | Responsabilidade |
|---|---|---|
| **Background Jobs** | Inngest Cloud | Orquestracao de jobs assincronos com retry, steps e observabilidade. |
| **Push Notifications** | OneSignal | Envio de notificacoes push ao Mobile Client. |
| **Vector Database** | Qdrant Cloud | Busca semantica de precedentes juridicos por similaridade de embeddings com suporte a filtros combinados (tribunal, status, tipo). |
| **ML Tracking** | MLflow (Cloud Run — apenas dev) | Tracking de experimentos e versionamento do modelo classificador via Model Registry. |

---

## Ambientes

### Separacao por servico

| Servico | Local | Stg | Prod |
|---|---|---|---|
| **API Server** | FastAPI local | Cloud Run (`min-instances: 0`) | Cloud Run (`min-instances: 1`) |
| **PostgreSQL** | Docker Compose | Cloud SQL (`db-f1-micro`) | Cloud SQL (`db-g1-small` + backups) |
| **Redis** | Docker Compose | Cloud Memorystore (`BASIC` 1GB) | Cloud Memorystore (`STANDARD` + replicacao) |
| **GCS** | — | Bucket sem versionamento | Bucket com versionamento |
| **Qdrant** | Docker Compose (`qdrant/qdrant`) | Qdrant Cloud (colecao `stg_*`) | Qdrant Cloud (colecao sem prefixo) |
| **Inngest** | Inngest Dev Server (`npx inngest-cli dev`) | Inngest Cloud — environment `stg` | Inngest Cloud — environment `prod` |
| **MLflow** | Cloud Run (`min-instances: 0`) | Cloud Run (`min-instances: 0`) | Nao existe em prod |

### Qdrant — separacao por colecao

Local, stg e prod usam o mesmo cluster Qdrant Cloud com colecoes separadas por prefixo.
O nome da colecao e montado dinamicamente via `settings.qdrant_collection_prefix` — nunca hardcoded:

```python
self._collection = f"{settings.qdrant_collection_prefix}precedents"
```

| Ambiente | `QDRANT_COLLECTION_PREFIX` | Colecao resultante |
|---|---|---|
| Local (Docker) | `dev_` | `dev_precedents` |
| Stg | `stg_` | `stg_precedents` |
| Prod | `` (vazio) | `precedents` |

### Inngest — separacao por environment

Cada ambiente tem seu proprio environment no Inngest Cloud com chaves isoladas,
armazenadas no Secret Manager:

| Ambiente | Environment Inngest | Secret |
|---|---|---|
| Local | Inngest Dev Server | — |
| Stg | `stg` | `stg/inngest_event_key` |
| Prod | `prod` | `prod/inngest_event_key` |

---

## Fluxo de Deploy

```
feature branch
  → PR aberto
    → GitHub Actions: build + test + pulumi preview (stack stg)

merge → main
  → GitHub Actions: pulumi up (stack stg)
  → Cloud Run stg: deploy da nova revisao

tag de release (ex: v1.0.0)
  → GitHub Actions: pulumi up (stack prod)
  → Cloud Run prod: deploy da nova revisao
```

O Cloud Run puxa a imagem diretamente do Artifact Registry. Credenciais sao
gerenciadas via IAM (Workload Identity Federation) — sem service account keys
no repositorio. Secrets de aplicacao lidos do Secret Manager por prefixo de ambiente (`stg/` ou `prod/`).

---

## Fluxo Principal de Analise de Peticao

```
Mobile Client
  → Cloud Run (API Server)         # recebe a peticao
  → GCS                            # armazena o PDF
  → Inngest Cloud                  # dispara o job assincrono

  [Inngest Job]
  → Qdrant Cloud                   # busca semantica de precedentes (com filtros)
  → Cloud Memorystore (Redis)      # cache do resultado da busca
  → Cloud Run (XGBoost em memoria) # classifica aplicabilidade
  → Cloud SQL (PostgreSQL)         # persiste a analise
  → OneSignal                      # notifica o usuario

  → Mobile Client                  # recebe o push
```

## Fluxo de Vetorizacao de Precedentes (job semanal)

```
Inngest Cloud (cron — toda segunda 02:00 UTC)
  → API Pangea                     # busca precedentes em batches paginados
  → Cloud SQL (PostgreSQL)         # persiste precedentes novos (idempotente)
  → Gemini API                     # gera embeddings de enunciation e thesis
  → Qdrant Cloud                   # persiste vetores com payload estruturado
```

---

## Observacoes

- **Cloud Memorystore** fica dentro da mesma VPC do Cloud Run e Cloud SQL — sem latencia de rede externa nem custo de egress. Cache posicionado na frente do Qdrant para absorver buscas repetidas por temas juridicos frequentes.
- **Qdrant Cloud** oferece filtros combinados (tribunal, status, tipo) junto com a busca vetorial em uma unica query — sem JOIN posterior. Colecoes separadas por prefixo (`dev_`, `stg_`, sem prefixo em prod) garantem isolamento dentro do mesmo cluster.
- **MLflow** roda no Cloud Run em stg com `min-instances: 0` — hiberna quando ocioso, custo proximo de zero. Nao existe em prod. O modelo classificador treinado e carregado no Cloud Run da API via MLflow Model Registry. Artefatos persistidos no GCS.
- **Inngest Cloud** e o unico servico de computacao fora do GCP. Nao ha equivalente nativo no GCP com o mesmo nivel de observabilidade, retry e orquestracao de steps para jobs de longa duracao.
- **OneSignal** abstrai o FCM internamente. O sistema nao se comunica com o FCM diretamente.
- O **Secret Manager** deve ser a unica fonte de segredos. Nenhuma credencial deve ser hardcoded em variaveis de ambiente do Cloud Run ou no repositorio.