# Publicação

## Repositório

- Nome: `only-bangers-mine-server`
- Owner: `venysssssssssss`
- URL: <https://github.com/venysssssssssss/only-bangers-mine-server>
- Remoto local: `origin`
- Fluxo desta auditoria: branch `docs/live-server-audit` + PR para `main`

## Conteúdo versionado

Entram scripts, manifestos, hashes SHA-512, testes, overrides úteis,
documentação e assets pequenos como `docs/assets/server-icon.png`.

O kit cliente atual é descrito pelo manifesto e pelo script, mas os jars locais
não entram no release público. O instalador AOF7 e seus testes permanecem para
preservar o histórico técnico do downloader.

## Conteúdo excluído

Ficam fora do Git regular:

- ZIPs locais do servidor e variantes de skin;
- `dist/OnlyBangers-Windows-Setup.zip` e sua pasta expandida;
- `windows-kit/client-mods/` com jars do cliente;
- logs, mundo, EasyAuth, backups, caches, `.part` e perfis locais;
- tokens, senhas, chaves, IDs de host e dados Tailscale.

Os arquivos locais não são apagados; são apenas excluídos do stage. GitHub
rejeita blobs individuais acima de 100 MB, e esses artefatos não são necessários
para revisar scripts, manifestos, hashes e documentação.

ZIPs pequenos dentro de `windows-kit/overrides/` podem ser resources ou
shaderpacks necessários ao kit legado; eles são assets do projeto, não pacotes
de distribuição, e permanecem versionados quando já fazem parte do fluxo.

## GitHub CLI no host remoto

O host remoto não possuía `gh`; a versão 2.46.0 foi instalada no espaço do
usuário, sem sudo. O login web precisa ser concluído no próprio host quando o
acesso a `github.com` estiver disponível. O token local não é copiado nem
gravado no repositório.

## Auditoria antes de cada commit

```bash
git status --short --ignored
git diff --cached --name-only
git diff --cached --stat
git diff --cached --check
```

Use stage seletivo. Não use `git add -A` enquanto ZIPs/jars não rastreados
estiverem presentes sem regras de exclusão. Revise arquivos novos procurando
segredos antes do push.

## Publicação via PR

```bash
gh auth status
git remote -v
git push -u origin docs/live-server-audit
gh pr create --base main --head docs/live-server-audit \
  --title "docs: document live OnlyBangers server" \
  --body-file /tmp/onlybangers-pr.md
```

O corpo do PR deve listar snapshot SSH, topologia, mods, otimizações, testes,
limites públicos e o achado systemd. Não registrar credenciais no arquivo
temporário nem no repositório.
