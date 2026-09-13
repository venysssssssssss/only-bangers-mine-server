# AOF7 Windows Kit

Kit de instalação e distribuição de uma instância Minecraft 1.20.1 com Fabric
Loader 0.16.0, mods declarados em manifest, overrides KubeJS e testes de
integridade do instalador.

O projeto foi pensado para Windows: o usuário inicia pelo bootstrap CMD ou
PowerShell, o instalador Python valida o manifest, baixa os arquivos com
retomada e hashes, prepara uma instância isolada e preserva os perfis já
existentes do Minecraft Launcher.

## Começo rápido

1. Baixe ou clone este repositório em uma máquina Windows.
2. Execute `windows-kit/Install-AOF7.cmd`.
3. Abra o perfil `AOF7-2.5.3` criado no Minecraft Launcher.
4. Se precisar investigar uma instalação, consulte `logs\\install.log`.

Para validar um manifest pequeno sem baixar o pack real:

```powershell
python windows-kit/aof7_installer.py --check-only `
  --manifest tests/fixtures/manifest-minimal.json `
  --output-root C:\AOF7-check
```

O modo `--check-only` lê e valida as versões e entradas sem criar o diretório
`mods` da instância.

## Requisitos

- Windows compatível com o bootstrap PowerShell/CMD do kit.
- Acesso à rede para baixar os arquivos HTTPS declarados no manifest.
- Minecraft Launcher instalado para usar o perfil gerado.
- Permissão de escrita no diretório de instalação escolhido.

O bootstrap carrega uma distribuição Python embutida adequada à arquitetura do
Windows. Não é necessário instalar dependências Python de terceiros.

## Verificações locais

Executar a suíte de testes a partir da raiz:

```powershell
python -m unittest discover -s tests -v
```

Executar o self-test do instalador:

```powershell
python windows-kit/aof7_installer.py --self-test
```

O manifest completo contém 436 entradas HTTPS para Minecraft 1.20.1/Fabric
Loader 0.16.0. O downloader verifica tamanho e SHA-256, usa arquivos `.part`
para retomada e troca o destino somente depois de uma transferência válida.

## Estrutura do projeto

| Caminho | Responsabilidade |
| --- | --- |
| `windows-kit/Install-AOF7.cmd` | Entrada CMD e encaminhamento de argumentos. |
| `windows-kit/Install-AOF7.ps1` | Bootstrap Windows, Python embutido e transcript. |
| `windows-kit/aof7_installer.py` | Manifest, validação, download, estado e perfil do launcher. |
| `windows-kit/manifest.json` | Versões do pack e arquivos distribuídos. |
| `windows-kit/overrides/` | Conteúdo aplicado à instância, incluindo scripts KubeJS. |
| `tests/` | Testes de segurança, download, bootstrap e integração de perfil. |
| `dist/` | Pacote ZIP distribuível do Windows Kit. |
| `docs/` | Arquitetura, operação, segurança e publicação. |

## Documentação

- [Arquitetura e diagramas](docs/architecture.md)
- [Operação, atualização e recuperação](docs/operations.md)
- [Modelo de segurança](docs/security.md)
- [Contribuição](CONTRIBUTING.md)
- [Relato de vulnerabilidades](SECURITY.md)
- [Fronteira de publicação](docs/publication.md)

## Troubleshooting rápido

- **Falha no download:** execute novamente; arquivos `.part` permitem retomar
  transferências interrompidas e retries tratam falhas transitórias.
- **Arquivo inválido:** confirme a conectividade e o SHA-256 esperado no
  manifest; o arquivo antigo não é substituído por conteúdo incompleto.
- **Perfil não aparece:** confirme que o Launcher estava fechado durante a
  alteração e verifique o backup `launcher_profiles.json.aof7-backup`.
- **Receita não aparece:** confirme que o servidor carregou os overrides KubeJS
  da instância correta e consulte os logs do servidor.

Para o fluxo completo de diagnóstico, consulte
[`docs/operations.md`](docs/operations.md).

## Licença e distribuição

Este repositório contém o kit e sua configuração; os mods e bibliotecas
referenciados pelo manifest podem possuir licenças próprias. Verifique os
termos de cada projeto antes de redistribuir o pacote fora deste uso.
