# only-bangers-mine-server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar este kit de servidor Minecraft em um repositório GitHub público chamado `only-bangers-mine-server`, com documentação operacional completa e diagramas arquiteturais renderizados pelo GitHub.

**Architecture:** O código existente permanece como fonte de verdade. A documentação explica o bootstrap Windows, o instalador Python, o manifest, downloads verificáveis, instância isolada, overrides KubeJS e testes; Mermaid em Markdown descreve os fluxos sem criar runtime novo.

**Tech Stack:** Git, GitHub CLI (`gh`), Markdown, Mermaid, PowerShell, Python standard library, `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-12-only-bangers-mine-server-design.md`

## Global Constraints

- Repositório público com nome exato `only-bangers-mine-server`.
- Não publicar tokens, senhas, chaves privadas, configurações pessoais, logs transitórios ou caches.
- Não publicar metadados locais de agentes nem instruções específicas do workspace (`.agents/`, `.codex/`, `.dual-graph*/`, `AGENTS.md`, `CODEX.md`).
- Não adicionar dependências para documentação ou diagramas.
- Não reescrever o instalador nem alterar receitas/mods sem defeito comprovado.
- O arquivo `mine server.zip` (~618 MB) não entra no Git regular: excede o limite de arquivo do GitHub e será mantido fora do commit, com a exclusão documentada.
- Validar com `python -m unittest discover -s tests -v` antes de afirmar conclusão.
- Se `gh auth status` continuar inválido, parar antes de criação/push e pedir `gh auth login`.

---

### Task 1: Preparar a fronteira pública do repositório

**Files:**
- Create: `.gitignore`
- Create: `docs/publication.md`
- Modify: none
- Test: command-based repository audit

**Interfaces:**
- Produces: padrões seguros para staging e um registro explícito do que pode ou não ser publicado.

- [ ] **Step 1: Criar regras mínimas de exclusão**

  Incluir somente padrões para segredos, logs, caches, temporários Windows/Python, arquivos `.part` e o ZIP de 618 MB:

  ```gitignore
  .env
  .env.*
  *.pem
  *.key
  *.p12
  logs/
  __pycache__/
  *.py[cod]
  *.part
  .pytest_cache/
  .venv/
  mine server.zip
  mine server.zip:Zone.Identifier
  ```

- [ ] **Step 2: Documentar a decisão de publicação**

  Criar `docs/publication.md` explicando que o repositório contém código, manifests, overrides, testes e assets versionáveis; explicar que `mine server.zip` fica fora por exceder o limite de arquivo do GitHub; registrar os comandos `git status --short`, `git diff --cached --stat` e `git diff --cached --name-only` para auditoria.

- [ ] **Step 3: Inicializar o repositório local**

  Executar:

  ```bash
  git init
  git branch -M main
  ```

- [ ] **Step 4: Auditar candidatos antes do primeiro stage**

  Executar `git status --short --ignored` e confirmar que nenhum nome de credencial, log ou ZIP gigante está no conjunto que será publicado.

- [ ] **Step 5: Commitar a fronteira pública**

  ```bash
  git add .gitignore docs/publication.md docs/superpowers/specs/2026-09-12-only-bangers-mine-server-design.md docs/superpowers/plans/2026-09-12-only-bangers-mine-server.md
  git diff --cached --check
  git commit -m "chore: define public repository boundary"
  ```

### Task 2: Criar o README de entrada

**Files:**
- Create: `README.md`
- Test: link and command review

**Interfaces:**
- Consumes: scripts e caminhos existentes em `windows-kit/`, `tests/` e `dist/`.
- Produces: entrada única para instalação, operação e navegação do projeto.

- [ ] **Step 1: Escrever a visão geral**

  Explicar que o projeto distribui uma instância AOF7 para Minecraft 1.20.1/Fabric, incluindo bootstrap Windows, manifest, downloader verificável, overrides e testes.

- [ ] **Step 2: Documentar requisitos e instalação**

  Mostrar o caminho principal com `windows-kit/Install-AOF7.cmd`, o modo de verificação `python windows-kit/aof7_installer.py --check-only --manifest tests/fixtures/manifest-minimal.json --output-root C:\\AOF7-check` e a localização do transcript `logs\\install.log` quando a instalação for executada.

- [ ] **Step 3: Documentar navegação e suporte**

  Incluir tabela de diretórios, links para `docs/architecture.md`, `docs/operations.md`, `docs/security.md`, `CONTRIBUTING.md`, `SECURITY.md` e `docs/publication.md`, além de uma seção curta de troubleshooting.

- [ ] **Step 4: Validar o README**

  Conferir que cada caminho citado existe, que blocos shell não usam placeholders ambíguos e que a instrução de instalação não promete suporte fora do Windows.

- [ ] **Step 5: Commitar a entrada pública**

  ```bash
  git add README.md
  git diff --cached --check
  git commit -m "docs: add project entrypoint"
  ```

### Task 3: Documentar arquitetura e operação

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/operations.md`
- Test: Mermaid/link review and command audit

**Interfaces:**
- Consumes: fluxo real do instalador, manifest, downloads, launcher profile, KubeJS e testes existentes.
- Produces: documentação didática para entendimento e execução sem alterar runtime.

- [ ] **Step 1: Criar a visão geral arquitetural**

  Em `docs/architecture.md`, explicar responsabilidades e limites dos componentes e incluir um diagrama `flowchart LR` com Bootstrap → Instalador → Manifest/URLs → Diretório de saída → Launcher/Servidor, além dos testes como verificador.

- [ ] **Step 2: Criar o diagrama de instalação**

  Incluir um `sequenceDiagram` cobrindo carregamento do manifest, validação HTTPS/caminho, download, SHA-256, gravação atômica, estado e atualização do perfil.

- [ ] **Step 3: Criar os diagramas de falha e segurança**

  Mostrar retry/`.part`/Range e preservação do arquivo antigo; mostrar fronteiras de confiança e rejeições de traversal, URL não HTTPS e credenciais na URL.

- [ ] **Step 4: Criar mapa de diretórios e ciclo de operação**

  Documentar o ciclo Windows → instância Minecraft → KubeJS → testes e mapear `windows-kit/`, `tests/`, `dist/` e `docs/` sem listar cada um dos 436 entries do manifest.

- [ ] **Step 5: Escrever o manual operacional**

  Em `docs/operations.md`, cobrir pré-requisitos, instalação normal, `--check-only`, reexecução idempotente, retomada, logs, backup do launcher profile, atualização do manifest, diagnóstico e recuperação do arquivo `.part`.

- [ ] **Step 6: Validar documentação técnica**

  Confirmar seis diagramas/visões exigidos pela spec, revisar consistência entre nomes de arquivos e comandos e executar `git diff --check`.

- [ ] **Step 7: Commitar arquitetura e operação**

  ```bash
  git add docs/architecture.md docs/operations.md
  git diff --cached --check
  git commit -m "docs: explain architecture and operations"
  ```

### Task 4: Documentar segurança e contribuição

**Files:**
- Create: `docs/security.md`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Test: secret-pattern and link review

**Interfaces:**
- Consumes: validações existentes do manifest/downloader e política pública da Task 1.
- Produces: regras para mudanças futuras, relato de vulnerabilidades e modelo de ameaça público.

- [ ] **Step 1: Descrever controles de segurança existentes**

  Documentar HTTPS, rejeição de credenciais em URL, `safe_join`, hashes, download atômico, retry limitado, preservação do arquivo antigo e backup do launcher profile.

- [ ] **Step 2: Documentar o que nunca deve ser commitado**

  Listar tokens, senhas, chaves, perfis locais, logs com dados pessoais, caches e o ZIP gigante; explicar rotação imediata caso segredo seja exposto.

- [ ] **Step 3: Criar guia de contribuição**

  Descrever branch, edição mínima, testes `python -m unittest discover -s tests -v`, revisão de manifest, validação de links e commits no padrão `tipo: resumo`.

- [ ] **Step 4: Criar política de vulnerabilidades**

  Em `SECURITY.md`, pedir que detalhes sensíveis sejam reportados privadamente ao mantenedor, sem abrir exploit público antes da correção, e indicar que o projeto não deve receber segredos em issues/PRs.

- [ ] **Step 5: Auditar texto público**

  Procurar por placeholders vazios, URLs fictícias apresentadas como reais, tokens, senhas e instruções contraditórias; corrigir antes do stage.

- [ ] **Step 6: Commitar políticas**

  ```bash
  git add docs/security.md CONTRIBUTING.md SECURITY.md
  git diff --cached --check
  git commit -m "docs: add security and contribution policies"
  ```

### Task 5: Verificar, revisar e preparar a publicação

**Files:**
- Modify: any documentation file only if verification finds a concrete inconsistency
- Test: full repository verification

**Interfaces:**
- Consumes: commits das Tasks 1–4.
- Produces: branch `main` auditada, pronta para remote público.

- [ ] **Step 1: Executar a suíte completa**

  ```bash
  python -m unittest discover -s tests -v
  ```

  Resultado esperado: código de saída `0` e nenhum teste falhando.

- [ ] **Step 2: Executar o self-test do instalador**

  ```bash
  python windows-kit/aof7_installer.py --self-test
  ```

  Se a opção não estiver disponível no ambiente atual, registrar o motivo e usar os testes da suíte como evidência equivalente.

- [ ] **Step 3: Revisar o stage e o tamanho dos arquivos**

  Executar `git status --short --ignored`, `git diff --cached --name-only`, `git diff --cached --stat` e `git diff --cached --check` para confirmar que o ZIP de 618 MB e dados locais não foram stageados.

- [ ] **Step 4: Importar o conteúdo seguro do projeto**

  Stagear o restante com `git add -A`, revisar a lista completa com `git diff --cached --name-only` e confirmar que código, manifests, overrides, testes e assets versionáveis estão presentes. Remover do stage qualquer segredo, log, cache, arquivo `*.part` ou ZIP gigante identificado pela auditoria. Então executar:

  ```bash
  git diff --cached --check
  git commit -m "chore: import project contents"
  ```

- [ ] **Step 5: Revisar o histórico**

  Executar `git log --oneline --decorate --max-count=10` e confirmar que cada commit representa uma intenção clara, sem misturar documentação com conteúdo binário.

- [ ] **Step 6: Solicitar revisão final do diff**

  Revisar os commits e corrigir apenas achados críticos/importantes antes de qualquer push.

### Task 6: Criar e publicar o repositório GitHub

**Files:**
- Modify: `.git/config` via Git commands
- External: GitHub repository and remote
- Test: `gh repo view` and remote verification

**Interfaces:**
- Consumes: branch `main` verificada da Task 5 e sessão `gh` autenticada.
- Produces: repositório público `only-bangers-mine-server` com branch principal publicada.

- [ ] **Step 1: Confirmar autenticação**

  ```bash
  gh auth status
  ```

  Se retornar token inválido, executar `gh auth login -h github.com` interativamente e repetir o check; não armazenar token em arquivo do projeto.

- [ ] **Step 2: Criar o repositório público**

  ```bash
  gh repo create only-bangers-mine-server --public --source=. --remote=origin --push
  ```

- [ ] **Step 3: Validar remoto e visibilidade**

  ```bash
  git remote -v
  gh repo view --json nameWithOwner,isPrivate,defaultBranchRef,url
  git ls-remote --heads origin main
  ```

  Resultado esperado: nome exato, `isPrivate=false`, branch padrão `main` e uma referência remota para `main`.

- [ ] **Step 4: Registrar o resultado**

  Atualizar `docs/publication.md` com a URL efetivamente retornada pelo `gh`, a branch publicada e a exclusão do ZIP; não registrar tokens ou dados da conta além do owner público.

- [ ] **Step 5: Commitar o registro final e publicar novamente**

  ```bash
  git add docs/publication.md
  git diff --cached --check
  git commit -m "docs: record public repository publication"
  git push origin main
  ```
