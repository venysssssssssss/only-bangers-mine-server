# Segurança

## Modelo de ameaça

Há duas superfícies: cliente Windows recebe jars de manifestos; servidor Linux
aceita conexões públicas e contas offline. O risco principal é misturar estado
privado com release público, aceitar payload incorreto ou tratar autenticação
offline como identidade Mojang.

## Controles do servidor

| Risco | Controle observado |
| --- | --- |
| RCON exposto | Listener limitado a `127.0.0.1:25575`. |
| Processo privilegiado | systemd usa usuário `venys1`, `NoNewPrivileges` e `PrivateTmp`. |
| Escrita ampla | `UMask=0077`; arquivos de estado ficam privados. |
| Acesso público | Jogo passa por Playit/IPv6; administração não usa a porta do jogo. |
| Contas offline | EasyAuth exige `/register` e `/login`; senha deve ser exclusiva. |
| Diagnóstico | Spark e health log permitem medir TPS sem expor banco. |

`online-mode=false` é escolha operacional para contas offline, não mecanismo de
identidade forte. EasyAuth precisa permanecer server-only. Nunca publique
`EasyAuth/easyauth.db`, senhas, `server.properties` ou comandos RCON.

## Controles do kit Windows

- Manifesto cliente fixa Minecraft 1.20.1 e Fabric Loader 0.19.5.
- Script exige Java 21 x64 e valida SHA-512 de cada um dos 52 jars.
- JEI e EasyAuth são rejeitados no conjunto cliente.
- O instalador legado rejeita URLs não HTTPS, credenciais em URL e path
  traversal; baixa em `.part` e promove arquivo completo atomicamente.
- Perfil do Launcher recebe backup antes de mesclagem.
- Falha de download não substitui um destino válido anterior.

SHA-512 do manifest cliente confirma o arquivo esperado no kit, mas não assina
o manifest. SHA-256 calculado pelo instalador legado registra bytes recebidos;
sem digest esperado externo, não é prova independente de supply chain.

## O que nunca publicar

- senhas, tokens, cookies, chaves privadas e credenciais de cloud;
- `EasyAuth/easyauth.db`, perfis locais e RCON;
- `world/`, `server.properties`, backups e arquivos `.part`;
- logs com nomes, UUIDs, caminhos pessoais ou mensagens privadas;
- IPs Tailscale, machine ID, boot ID e configuração interna do host;
- ZIPs e diretórios com jars grandes ou estado local;
- metadados `.agents/`, `.codex/`, `.dual-graph*/` e arquivos do workspace.

O endpoint público do jogo pode aparecer na documentação operacional; dados de
administração permanecem privados.

## Revisão antes do push

```bash
git status --short --ignored
git diff --cached --name-only
git diff --cached --stat
git diff --cached --check
```

Revise arquivos novos visualmente. Se um segredo for publicado, revogue-o e
faça rotação imediata; apagar em commit posterior não remove o histórico.

## Achado operacional

O host tem fragmento systemd base com referência 1.21.1, drop-in ativo 1.20.1
e alerta de unidade carregada defasada. Isso é risco de manutenção e deve ser
reconciliado em janela controlada; esta auditoria não executou `daemon-reload`
nem alterou serviço.
