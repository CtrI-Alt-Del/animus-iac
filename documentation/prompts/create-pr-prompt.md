---
description: Criar pull request padronizado usando GitHub CLI
---

# Prompt: Criar PR

**Objetivo:** Padronizar a criação de Pull Requests (PRs), garantindo descrições
claras que facilitem a revisão de código e o rastreamento de tarefas. O foco é
utilizar exclusivamente a **GitHub CLI (gh)** para manter a integridade do fluxo
de trabalho.

---

## Entrada

- Uma Spec (especificação) devidamente implementada e validada.
- Uma Bug Report (relatório de bug) devidamente implementada e validada.
- ID do ticket do Jira (ex: `ANI-123`)

> Se o ticket do Jira não estiver presente, não execute o prompt.

---

## Diretrizes de Execução

### 1 Analise do Contexto

- Revise a Spec implementada e o changelog das alterações realizadas.
- Identifique:

  - impactos técnicos
  - decisões de design tomadas
  - riscos e efeitos colaterais

---

### 2 Definicao do Titulo

- Deve ser:

  - curto
  - direto
  - em PT-BR
  - refletir a essência da alteração
  - Incluir a task do Jira como prefixo (ex: `[ANI-12] Adiciona tela de sign up`)

Exemplos:

- Implementação da listagem de produtos
- Correção do erro de carregamento de imagem
- Correção de navegação para tela de catálogo

Nao incluir prefixos no titulo:

```
feat/
fix/
refactor/
```

---

### 3 Estrutura da Descricao (Body)

O corpo do PR deve seguir o template abaixo.

**Regras de formatação:**

- usar Markdown
- não usar título principal `#`
- usar `##` e níveis abaixo

---

## Objetivo (obrigatorio)

Explique por que este PR foi criado e qual seu propósito central.

---

## Causa do bug (opcional - apenas fix)

Descreva a causa técnica raiz.

---

## Changelog (obrigatorio)

Lista técnica das mudanças:

- arquivos alterados
- comportamento modificado
- regras adicionadas
- refatorações feitas

---

## Novas dependencias (opcional)

Informe se houve adicao de novas dependencias no PR.

Se houve, detalhe:

- nome do pacote
- local da adicao (`pyproject.toml`, `uv.lock`, etc.)
- motivo da inclusao
- impacto esperado em build/runtime/seguranca

---

## Como testar (obrigatorio)

Passo a passo claro para o revisor validar:

1. …
2. …
3. …

---

## Observacoes (opcional)

- decisões de arquitetura
- limitações conhecidas
- tradeoffs
- próximos passos

---

> Não incluir as palavras entre parênteses, são meramente instruções.

## 4 Criacao via gh CLI

Nao usar GitHub MCP. Nao usar APIs MCP. Usar exclusivamente **gh**.

> Repositorio: https://github.com/CtrI-Alt-Del/animus-iac

Comando padrão:

```
gh pr create \
  --repo owner/repo \
  --base main \
  --head <nome-da-branch> \
  --title "<Titulo do PR>" \
  --body-file <body do PR>
```

---

## 5 Retorno

Após criação:

```
gh pr view --web
```

ou

```
gh pr view --json url
```

Retornar:

- link do PR criado
- título final
- resumo do body gerado
