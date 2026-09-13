# Contribuindo

## Fluxo mínimo

1. Crie uma branch para a mudança.
2. Faça a menor alteração que resolve o problema.
3. Atualize a documentação quando comportamento, manifest ou operação mudarem.
4. Rode os testes antes de criar o commit.
5. Revise o diff, especialmente URLs, hashes e caminhos de saída.

## Comandos de verificação

Na raiz do projeto:

```powershell
python -m unittest discover -s tests -v
python windows-kit/aof7_installer.py --self-test
```

Para validar apenas o manifest mínimo:

```powershell
python windows-kit/aof7_installer.py --check-only `
  --manifest tests/fixtures/manifest-minimal.json `
  --output-root C:\AOF7-check
```

Não use um diretório de instalação real para fixtures de teste.

## Mudanças no manifest

Toda alteração em `windows-kit/manifest.json` deve manter:

- Minecraft 1.20.1 e Fabric Loader 0.16.0, salvo mudança deliberada de versão;
- URLs HTTPS sem credenciais embutidas;
- caminhos relativos dentro da instância;
- tamanho e SHA-256 registrados no estado, quando o fluxo de download for alterado;
- testes atualizados quando o comportamento do downloader mudar.

## Estilo de commits

Use o formato curto `tipo: resumo`, por exemplo:

- `docs: explain launcher recovery`
- `fix: preserve verified download`
- `chore: refresh release manifest`

Commits devem ter uma intenção clara. Evite misturar refatoração sem relação,
binários gigantes e mudanças de configuração pessoal.

## Pull requests

Descreva o problema, a mudança, os comandos executados e qualquer impacto no
manifest ou nos overrides KubeJS. Não inclua logs pessoais, tokens ou arquivos
de perfil do Launcher.
