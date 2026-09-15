# OnlyBangers: auditoria do servidor live e documentação pública

## Objetivo

Alinhar documentação e README ao servidor OnlyBangers realmente ativo, usando
evidências do repositório e do host Minecraft. O host não será
alterado; somente o GitHub CLI pode ser instalado/autenticado no diretório do
usuário para permitir publicação.

## Estado técnico documentado

- Host: Ubuntu 26.04.1 LTS em Dell OptiPlex 7050, x86-64, quatro CPUs.
- Runtime: OpenJDK 21, Minecraft 1.20.1, Fabric Loader 0.19.5, heap Java de 6 GB.
- Rede: Playit para acesso público e caminho IPv6 direto; proxy IPv6 encaminha
  para o Minecraft em loopback `127.0.0.1:25565`.
- Administração: RCON limitado a `127.0.0.1:25575`; EasyAuth protege contas
  quando `online-mode=false`.
- Saúde observada: Spark registra TPS próximo de 20, CPU do processo em torno
  de 2–5% e servidor ativo via systemd.
- Otimização: C2ME, Lithium, FerriteCore, ModernFix, Krypton, VMP, ServerCore,
  Spark, Chunky, Ksyxis, LazyDFU, Clumps e MemoryLeakFix, além de dependências.

## Achados e limites

- O fragmento base de `minecraft.service` cita 1.21.1, enquanto o drop-in ativo
  executa 1.20.1; systemd também alerta que a unidade carregada está defasada.
  O documento registra o risco, mas não executa `daemon-reload` nem muda o host.
- Nenhum WebSocket foi encontrado. A narrativa explica WebSocket por contraste:
  o protocolo Minecraft mantém uma conexão TCP persistente, enquanto WebSocket
  seria apropriado para painel, chat ou monitoramento em navegador.
- Nenhuma foto física foi encontrada. O README usa o `server-icon.png` real e
  o identifica como ícone, não como fotografia do hardware.
- `gh` não existia no host; foi instalado no espaço do usuário.
  O login web falhou porque o host não alcançou `github.com`; autenticação ainda
  depende de ação manual do usuário ou correção de egress.
- Tailscale, IDs de máquina, logs, banco EasyAuth, RCON e credenciais não entram
  no repositório público.

## Entregáveis

- README de entrada para OnlyBangers, com instalação, conexão, mods, otimização,
  segurança, saúde e links para a documentação.
- `docs/architecture.md` com topologia live, fluxo de instalação, limites de
  confiança e diagramas Mermaid renderizáveis no GitHub.
- `docs/operations.md`, `docs/security.md`, `docs/publication.md` e setup
  Windows reconciliados com versões, rede e limites atuais.
- Asset pequeno `docs/assets/server-icon.png` copiado do ícone existente do host.
- Branch publicada em PR, quando autenticação remota estiver disponível; ZIPs de
  distribuição, jars grandes, estado, logs e bancos permanecem fora do commit.

## Validação

1. Executar `python -m unittest discover -s tests -v` com permissão para os
   testes HTTP locais.
2. Executar `python windows-kit/aof7_installer.py --self-test`.
3. Validar JSON, contagem de mods, hashes SHA-512, links relativos e ausência
   de segredos.
4. Revisar `git diff --cached --check` e lista de arquivos antes do commit.
5. Confirmar branch, push e PR com `gh` no remoto já configurado.
