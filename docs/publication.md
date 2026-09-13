# Publicação

Este projeto será publicado como o repositório público `only-bangers-mine-server`.

## Conteúdo versionado

O repositório inclui o código do instalador, manifests, overrides KubeJS,
testes, documentação e assets compatíveis com os limites do GitHub.

## Conteúdo excluído

`mine server.zip` permanece no workspace, mas não entra no Git: o arquivo tem
cerca de 618 MB e ultrapassa o limite de 100 MB por arquivo do GitHub. O
arquivo auxiliar `mine server.zip:Zone.Identifier` também é específico do
Windows e não pertence ao projeto.

Também ficam fora segredos, logs, caches, arquivos temporários e partes
incompletas de downloads, conforme `.gitignore`. Metadados locais de agentes
(`.agents/`, `.codex/`, `.dual-graph/`, `.dual-graph-context/`) e instruções
específicas deste workspace (`AGENTS.md`, `CODEX.md`) também não fazem parte
do produto público. `opencode.json` também é configuração local do ambiente e
fica fora do produto. Arquivos `.DS_Store` também são descartados por serem
metadados do Finder, não conteúdo do pack.

## Auditoria antes de publicar

Use estes comandos antes de cada publicação:

```bash
git status --short --ignored
git diff --cached --stat
git diff --cached --name-only
git diff --cached --check
```

O conjunto a publicar deve conter apenas arquivos do projeto, documentação e
assets versionáveis. Nunca adicione tokens, senhas, chaves privadas ou perfis
locais do Minecraft Launcher.

## Estado da publicação

- Repositório: `only-bangers-mine-server`
- Visibilidade: pública
- Branch: `main`
- URL: será registrada após a criação via `gh`
