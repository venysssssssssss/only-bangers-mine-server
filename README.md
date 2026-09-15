# OnlyBangers Minecraft Server

Servidor Minecraft Fabric 1.20.1 mantido em Linux, com cliente Windows
reprodutível, autenticação offline, túnel Playit e observabilidade via Spark.

![Ícone do servidor OnlyBangers](docs/assets/server-icon.png)

> O arquivo acima é o ícone real do servidor, não uma foto do hardware.

## Visão rápida

- **Minecraft:** 1.20.1
- **Fabric Loader:** 0.19.5
- **Java:** OpenJDK 21
- **Acesso principal:** `schmidt-flowers.tun.ply.gg:60986`
- **Acesso alternativo:** IPv6 direto na porta `25565`
- **Autenticação:** EasyAuth com `online-mode=false`
- **Administração:** RCON somente em `127.0.0.1:25575`
- **Saúde observada:** TPS próximo de 20, heap Java de 6 GB e CPU do processo
  em torno de 2–5% durante a auditoria de 15/09/2026.

O servidor ativo fica em um Dell OptiPlex 7050 com Ubuntu 26.04.1 LTS e quatro
CPUs. A unidade systemd executa o jar Fabric 1.20.1; o caminho IPv6 passa por um
proxy de loopback antes de chegar ao processo Java.

## Jogar

1. Siga o [setup Windows + TLauncher](docs/SETUP-WINDOWS-TLAUNCHER.md).
2. Use Fabric 1.20.1 com Loader 0.19.5 e Java 21 x64.
3. Instale os 52 mods do manifesto cliente.
4. Adicione `schmidt-flowers.tun.ply.gg:60986` no multiplayer.
5. Primeiro acesso: `/register SUA_SENHA SUA_SENHA`; depois: `/login SUA_SENHA`.

EMI substitui JEI no cliente. EasyAuth e SkinRestorer são server-only; não
copie banco, mundo, `server.properties` ou credenciais para o cliente.

O clone público contém script, manifesto e hashes. Os jars do cliente ficam
fora do Git por tamanho; o pacote completo precisa ser fornecido como artefato
de release pelo mantenedor.

## O que existe no projeto

| Caminho | Papel |
| --- | --- |
| `windows-kit/Install-OnlyBangers.ps1` | Verifica Java, versões, jars e SHA-512. |
| `windows-kit/onlybangers-client-manifest.json` | Manifesto atual dos 52 mods cliente. |
| `windows-kit/client-mods/` | Jars locais do pacote; não entram no release público. |
| `windows-kit/` | Kit AOF7 legado e overrides históricos do instalador. |
| `tests/` | Testes do instalador legado e contrato do kit atual. |
| `docs/` | Arquitetura, operação, segurança, setup e publicação. |

## Mods e otimização

O pack combina conteúdo e estabilidade. Create, Botania, Malum, TechReborn,
IndustrialReborn, Hephaestus, Farmer's Delight, Vinery, AdventureZ,
Supplementaries, Waystones e Sophisticated Backpacks formam o núcleo de
gameplay. Terralith, Regions Unexplored, YUNG's Better Caves e Better Nether
Fortresses ampliam worldgen.

O caminho de performance usa C2ME para geração concorrente de chunks, Lithium
para lógica do jogo, FerriteCore e ModernFix para memória/startup, Krypton e
VMP para rede, ServerCore para ajustes de servidor e Ksyxis/LazyDFU para
inicialização. Chunky ajuda na preparação de chunks; Spark mede o resultado;
Fabric Carpet, Clumps e MemoryLeakFix completam as ferramentas de operação.

Esses nomes descrevem função, não promessa de ganho fixo. A evidência live é o
Spark: TPS próximo de 20 durante o snapshot.

## Arquitetura e WebSocket

O jogo mantém uma conexão TCP persistente com o servidor. O OnlyBangers não usa
WebSocket: WebSocket seria outra opção, útil para um painel web, chat ou stream
de métricas em navegador. A diferença e o caminho real estão em
[Arquitetura e diagramas](docs/architecture.md).

## Verificar o projeto

```powershell
python -m unittest discover -s tests -v
python windows-kit/aof7_installer.py --self-test
```

Para validar o instalador sem baixar o pack legado:

```powershell
python windows-kit/aof7_installer.py --check-only `
  --manifest tests/fixtures/manifest-minimal.json `
  --output-root C:\AOF7-check
```

## Documentação

- [Arquitetura, rede e diagramas Mermaid](docs/architecture.md)
- [Operação, saúde, atualização e recuperação](docs/operations.md)
- [Segurança do cliente e servidor](docs/security.md)
- [Setup Windows + TLauncher](docs/SETUP-WINDOWS-TLAUNCHER.md)
- [Contribuição](CONTRIBUTING.md)
- [Relato de vulnerabilidades](SECURITY.md)
- [Fronteira de publicação](docs/publication.md)

## Distribuição

O repositório versiona scripts, manifestos, hashes, testes, overrides e
documentação. ZIPs, jars grandes, logs, bancos, mundo e perfis pessoais ficam
fora da publicação. Mods referenciados podem ter licenças próprias; confira os
termos de cada projeto antes de redistribuir.
