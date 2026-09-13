# Arquitetura

Este documento descreve o fluxo real do AOF7 Windows Kit. O projeto é um
instalador local: não há API própria, banco de dados ou serviço intermediário.
O manifest declara o que deve ser baixado; o instalador valida, materializa e
registra a instância do Minecraft.

## 1. Visão geral dos componentes

```mermaid
flowchart LR
    User[Usuário Windows]
    Cmd[Install-AOF7.cmd]
    Ps[Install-AOF7.ps1<br/>bootstrap + transcript]
    Py[aof7_installer.py]
    Manifest[manifest.json<br/>Minecraft 1.20.1<br/>Fabric 0.16.0]
    Sources[URLs HTTPS dos arquivos]
    Output[Instância AOF7 isolada<br/>mods + overrides + state]
    Launcher[Minecraft Launcher<br/>launcher_profiles.json]
    Server[Servidor Minecraft<br/>KubeJS carrega overrides]
    Tests[tests/<br/>unittest]

    User --> Cmd --> Ps --> Py
    Py --> Manifest
    Manifest --> Sources
    Sources --> Py
    Py --> Output
    Py --> Launcher
    Output --> Launcher
    Launcher --> Server
    Tests -.verifica.-> Py
    Tests -.verifica.-> Ps
```

### Responsabilidade de cada componente

| Componente | Faz | Não faz |
| --- | --- | --- |
| `Install-AOF7.cmd` | Oferece uma entrada simples e repassa argumentos. | Não baixa arquivos nem interpreta o manifest. |
| `Install-AOF7.ps1` | Prepara Python embutido, chama o instalador e grava `logs\\install.log`. | Não substitui a validação do instalador Python. |
| `aof7_installer.py` | Valida entradas, baixa, verifica, grava estado e mescla o perfil. | Não é um servidor web nem gerencia contas do Minecraft. |
| `manifest.json` | Declara versões e arquivos esperados. | Não executa código. |
| `overrides/` | Fornece alterações da instância, como scripts KubeJS. | Não altera o código do instalador. |
| `tests/` | Exercita segurança, downloads e bootstrap. | Não substitui uma instalação real no Windows. |

## 2. Sequência de uma instalação normal

```mermaid
sequenceDiagram
    actor U as Usuário
    participant B as Bootstrap CMD/PowerShell
    participant I as Instalador Python
    participant M as Manifest
    participant H as Hosts HTTPS
    participant O as Diretório de saída
    participant L as Minecraft Launcher

    U->>B: Executa Install-AOF7.cmd
    B->>B: Seleciona Python embutido e inicia transcript
    B->>I: Repassa argumentos
    I->>M: Carrega versões e entries
    M-->>I: URLs, caminhos e versões
    I->>I: Valida HTTPS, host, caminho e versão
    loop Cada arquivo
        I->>H: GET do arquivo ou Range após .part
        H-->>I: Bytes
        I->>I: Confere tamanho recebido e calcula SHA-256
        I->>O: Renomeia .part para o destino validado
    end
    I->>O: Grava estado da instalação
    I->>L: Faz backup e mescla perfil AOF7
    L-->>U: Perfil isolado disponível
    B->>B: Fecha transcript
```

O destino só é substituído depois que a resposta termina conforme o tamanho
declarado quando esse cabeçalho existe. O SHA-256 é registrado no estado local;
o manifest atual não fornece um digest esperado para rejeição independente.
Isso permite repetir a instalação sem destruir um arquivo válido.

## 3. Falhas, retry e retomada

```mermaid
flowchart TD
    Start[Arquivo necessário] --> Existing{Destino já está válido?}
    Existing -- Sim --> Skip[Pula download]
    Existing -- Não --> Part{Existe arquivo .part?}
    Part -- Sim --> Range[Solicita bytes restantes com Range]
    Part -- Não --> Full[Inicia download completo]
    Range --> Response{Resposta válida?}
    Full --> Response
    Response -- Não/transitória --> Retry{Ainda há tentativas?}
    Retry -- Sim --> Backoff[Tenta novamente]
    Backoff --> Response
    Retry -- Não --> Cleanup[Remove .part incompleto]
    Cleanup --> Fail[Erro sem substituir destino antigo]
    Response -- Sim --> Hash[Calcula tamanho e SHA-256]
    Hash --> Atomic[Move .part para o destino]
    Atomic --> State[Atualiza estado]
    Skip --> State
    State --> Done[Próximo arquivo]
```

O arquivo `.part` é temporário e não é um resultado publicável. Em uma falha
definitiva, o arquivo anterior permanece intacto e a exceção torna o problema
visível ao operador.

## 4. Fronteiras de confiança e controles

```mermaid
flowchart LR
    subgraph Local[Máquina local confiável]
        Cli[Argumentos e manifest local]
        Validate[Validação de versão,<br/>URL e caminho]
        Download[Downloader atômico]
        State[Estado e perfil com backup]
    end
    subgraph Internet[Internet não confiável]
        URL[Servidor de download]
        Payload[Bytes recebidos]
    end
    subgraph Reject[Entradas rejeitadas]
        Traversal[path traversal]
        Insecure[URL não HTTPS]
        Credentials[Credenciais embutidas na URL]
        HashMismatch[Resposta curta]
    end

    Cli --> Validate
    Validate -->|HTTPS + host sem credenciais| URL
    Validate -. rejeita .-> Traversal
    Validate -. rejeita .-> Insecure
    Validate -. rejeita .-> Credentials
    URL --> Payload --> Download
    Download -->|resposta completa| State
    Download -. resposta curta .-> HashMismatch
```

Controles importantes:

- `safe_join` impede que o caminho de uma entry escape do diretório de saída.
- URLs com esquema inseguro ou credenciais são rejeitadas antes do download.
- O tamanho da resposta detecta downloads curtos; o SHA-256 recebido é
  registrado no estado para auditoria local.
- O manifest atual não contém hashes esperados, portanto o digest não é uma
  prova independente de autenticidade.
- A gravação usa arquivo temporário e substituição atômica.
- O perfil existente do Launcher recebe backup antes da mesclagem.

## 5. Ciclo de operação

```mermaid
stateDiagram-v2
    [*] --> Bootstrap
    Bootstrap --> Validacao: argumentos e manifest
    Validacao --> Download: entradas válidas
    Download --> Instancia: arquivos verificados
    Download --> Download: retry ou retomada
    Download --> Diagnostico: falha definitiva
    Instancia --> Launcher: perfil AOF7 isolado
    Launcher --> Servidor: iniciar Minecraft
    Servidor --> KubeJS: carregar overrides
    KubeJS --> Jogabilidade: receitas e regras ativas
    Jogabilidade --> Testes: validar mudança
    Testes --> Validacao: novo manifest ou release
    Diagnostico --> Bootstrap: corrigir ambiente e repetir
```

O diretório de saída é a fronteira da instância. Os overrides KubeJS são
carregados pelo servidor Minecraft durante o ciclo normal; eles não são
executados pelo bootstrap nem pelo downloader.

## 6. Mapa de diretórios

```mermaid
flowchart TB
    Root[Raiz do projeto]
    Root --> Kit[windows-kit/]
    Root --> Test[tests/]
    Root --> Dist[dist/]
    Root --> Docs[docs/]
    Kit --> Entry[Install-AOF7.cmd + Install-AOF7.ps1]
    Kit --> Installer[aof7_installer.py]
    Kit --> Manifest[manifest.json]
    Kit --> Overrides[overrides/]
    Test --> Fixtures[fixtures/]
    Test --> Suite[test_aof7_installer.py]
    Dist --> Zip[AOF7-Windows-Kit-2.5.3.zip]
    Docs --> Architecture[architecture.md]
    Docs --> Operations[operations.md]
    Docs --> Security[security.md]
```

O manifest completo contém 436 entries; ele é uma fonte de dados e por isso
fica agrupado no mapa em vez de ser expandido em um diagrama ilegível.

## Decisões e limites

- A arquitetura é local e orientada a arquivos; não há serviço central a
  manter.
- O retry é deliberadamente limitado ao downloader existente; observabilidade
  detalhada de cada host ou uma fila distribuída não fazem parte do kit.
- Mermaid foi escolhido porque é renderizado pelo GitHub e mantém os diagramas
  revisáveis como texto.
