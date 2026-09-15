# OnlyBangers Server Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Alinhar a documentação pública ao servidor OnlyBangers ativo e publicar uma branch revisável sem alterar o Minecraft remoto.

**Architecture:** A documentação terá duas camadas: README como entrada e documentos atuais como referência operacional. Mermaid explicará o caminho cliente → túnel/IPv6 → proxy loopback → Java Fabric; o snapshot live será datado e separado de decisões históricas.

**Tech Stack:** Markdown, Mermaid, Git, GitHub CLI, Python `unittest`, JSON e shell read-only via SSH.

**Spec:** `docs/superpowers/specs/2026-09-15-onlybangers-server-audit-design.md`

## Global Constraints

- Host Minecraft somente leitura; nenhum restart, `daemon-reload`, alteração de config ou cópia de banco. Instalação/autenticação user-local do `gh` é permitida para publicação.
- Minecraft 1.20.1, Fabric Loader 0.19.5 e Java 21 são versões live documentadas.
- Nenhum WebSocket será declarado como parte do servidor sem evidência.
- README usa `server-icon.png` como ícone, nunca como foto física.
- Não publicar credenciais, IDs, Tailscale, RCON, EasyAuth, logs privados, ZIPs de distribuição ou jars grandes.
- Não adicionar dependências, CI ou runtime novo.

---

### Task 1: Registrar desenho e asset público

**Files:**
- Create: `docs/superpowers/specs/2026-09-15-onlybangers-server-audit-design.md`
- Create: `docs/superpowers/plans/2026-09-15-onlybangers-server-audit.md`
- Create: `docs/assets/server-icon.png`

**Interfaces:**
- Consumes: snapshot SSH e decisões aprovadas.
- Produces: spec, plano executável e asset visual pequeno.

- [x] **Step 1: Copiar o ícone existente do host**

  Copiar somente o `server-icon.png` existente no host e salvar em
  `docs/assets/server-icon.png`; não copiar o diretório `world`.

- [x] **Step 2: Validar asset**

  Confirmar que o arquivo é PNG e que o tamanho é pequeno o suficiente para
  documentação pública; a legenda deve dizer “ícone do servidor”.

- [x] **Step 3: Commitar spec, plano e asset**

  Executar `git diff --check`, revisar nomes e commit `docs: define live server audit`.

### Task 2: Reescrever entrada e arquitetura

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`

**Interfaces:**
- Consumes: versões live, endpoint Playit, IPv6, serviço systemd, mods e métricas Spark.
- Produces: entrada pública e diagramas coerentes com o caminho real.

- [x] **Step 1: Atualizar identidade do README**

  Trocar foco AOF7 legado por OnlyBangers, mantendo links aos scripts existentes
  quando úteis e distinguindo o kit Windows do servidor live.

- [x] **Step 2: Adicionar conexão, mods e otimização**

  Explicar Playit, IPv6, EMI versus JEI, EasyAuth server-only, SkinRestorer e
  funções dos mods de performance sem alegar benchmark inexistente.

- [x] **Step 3: Adicionar o ícone com legenda honesta**

  Referenciar `docs/assets/server-icon.png` no README; não chamá-lo de foto.

- [x] **Step 4: Substituir diagramas installer-only**

  Manter o fluxo do instalador, mas incluir topologia live, proxy IPv6,
  loopback/RCON, fronteiras públicas/privadas e estado systemd.

- [x] **Step 5: Revisar nomes e links**

  Confirmar que cada caminho citado existe e que AOF7 aparece apenas onde
  descreve o instalador histórico ainda presente.

### Task 3: Alinhar operação, segurança, publicação e setup

**Files:**
- Modify: `docs/operations.md`
- Modify: `docs/security.md`
- Modify: `docs/publication.md`
- Modify: `docs/SETUP-WINDOWS-TLAUNCHER.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: README e arquitetura atualizados.
- Produces: instruções reproduzíveis, limites de segurança e release limpo.

- [x] **Step 1: Documentar operação live**

  Registrar unidade systemd, JVM, porta, caminhos de conexão, Spark, recursos,
  backups e o alerta de fragmento 1.21.1 versus drop-in 1.20.1.

- [x] **Step 2: Documentar segurança real**

  Explicar `online-mode=false` + EasyAuth, RCON local, rede pública, dados que
  ficam privados e necessidade de rotação se segredo for exposto.

- [x] **Step 3: Documentar mods por função**

  Alinhar cliente/servidor, remover recomendações de JEI/EasyAuth no cliente e
  manter SkinRestorer como server-only.

- [x] **Step 4: Fechar fronteira pública**

  Ignorar ZIPs e artefatos grandes não rastreados sem apagar cópias locais;
  manter scripts, manifest, hashes, docs e assets pequenos.

- [x] **Step 5: Revisar políticas históricas**

  Atualizar apenas fatos operacionais atuais; preservar specs/plans anteriores.

### Task 4: Validar e publicar

**Files:**
- Modify: documentation files only if a failed check exposes inconsistency.

**Interfaces:**
- Consumes: branch documentada e artefatos filtrados.
- Produces: commit público e PR revisável.

- [x] **Step 1: Executar testes completos**

  Rodar `python -m unittest discover -s tests -v` e exigir código de saída zero;
  testes HTTP locais podem precisar de execução fora do sandbox restrito.

- [x] **Step 2: Executar self-test**

  Rodar `python windows-kit/aof7_installer.py --self-test`.

- [x] **Step 3: Auditar conteúdo público**

  Revisar `git status --short --ignored`, `git diff --cached --name-only`,
  `git diff --cached --stat`, `git diff --cached --check`, JSONs e padrões de
  segredo antes de cada commit.

- [x] **Step 4: Criar commits de intenção**

  Separar spec/asset, documentação e higiene/publicação; nunca stagear ZIP,
  banco, log, cache, estado ou jar grande.

- [ ] **Step 5: Configurar e publicar via gh**

  Confirmar `gh --version` e `gh auth status` no host remoto. Se o login web
  continuar bloqueado, o usuário deve autenticar
  manualmente no host ou liberar egress para `github.com`; então fazer push da
  branch e abrir PR contra `main`. Não fazer push direto em `main`.

- [ ] **Step 6: Emitir narrativa final**

  Após PR e verificações, escrever no terminal resumo LinkedIn PT-BR curto,
  técnico e didático, centrado na diferença entre TCP Minecraft e WebSocket.
