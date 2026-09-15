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

## Mudanças nos manifestos

Existem dois fluxos e eles não devem ser misturados:

- `windows-kit/manifest.json`: kit AOF7 legado, Minecraft 1.20.1/Fabric Loader
  0.16.0, coberto por `test_aof7_installer.py`;
- `windows-kit/onlybangers-client-manifest.json`: cliente atual, Minecraft
  1.20.1/Fabric Loader 0.19.5, 52 jars com SHA-512.

Para ambos: mantenha caminhos relativos, não embuta credenciais e atualize os
testes quando comportamento do instalador mudar. O downloader legado registra
SHA-256 dos bytes recebidos; o kit atual compara SHA-512 declarado.

## Estilo de commits

Use o formato curto `tipo: resumo`, por exemplo:

- `docs: explain launcher recovery`
- `fix: preserve verified download`
- `chore: refresh release manifest`

Commits devem ter uma intenção clara. Evite misturar refatoração sem relação,
binários gigantes e mudanças de configuração pessoal.

Mudanças no servidor live devem vir acompanhadas de versão, impacto operacional
e evidência de saúde; esta documentação não autoriza alteração remota.

## Pull requests

Descreva o problema, a mudança, os comandos executados e qualquer impacto no
manifest ou nos overrides KubeJS. Não inclua logs pessoais, tokens ou arquivos
de perfil do Launcher.
