# Operação

Este manual cobre cliente Windows e servidor OnlyBangers observado em
15/09/2026. Comandos de SSH abaixo são referências para operador autorizado;
durante a auditoria executada, nenhum comando mutável foi rodado no host.

## Estado live

| Item | Valor observado |
| --- | --- |
| Host | Ubuntu 26.04.1 LTS / Dell OptiPlex 7050 / x86-64 |
| CPU/memória | 4 CPUs / 14 GiB RAM / 3.7 GiB swap |
| Java | OpenJDK 21.0.12 |
| Minecraft | 1.20.1 |
| Fabric | Loader 0.19.5 |
| Heap | `-Xms6G -Xmx6G` |
| Serviço | `minecraft.service`, ativo e rodando |
| Jogo | `127.0.0.1:25565` atrás de proxy IPv6 |
| RCON | `127.0.0.1:25575` |
| Servidor | 648 MB; mundo com região de 265 MB |

Spark registrou TPS de 20.0 na maior parte dos intervalos, CPU do processo em
torno de 2–5% e memória Java de 1.1–2.7 GB. Saúde é variável com jogadores,
worldgen e máquinas Create; use histórico do Spark para comparar carga real.

## Acesso dos jogadores

Endereço principal:

```text
schmidt-flowers.tun.ply.gg:60986
```

Fallback IPv6: use o endereço global documentado no setup com porta `25565`.
O caminho é cliente → Playit ou IPv6 → `minecraft-ipv6-proxy.service` →
loopback → Java Fabric.

## Verificação read-only

```bash
systemctl is-active minecraft.service minecraft-ipv6-proxy.service playit.service
ss -lntup
journalctl -u minecraft.service -n 80 --no-pager
```

Confirme que o jogo está limitado ao caminho esperado, que RCON continua em
loopback e que Spark mantém TPS próximo de 20. Não publique os logs sem remover
nomes, caminhos, UUIDs e dados de jogadores.

## Autenticação

O servidor usa `online-mode=false` com EasyAuth. Primeiro acesso:

```text
/register SUA_SENHA SUA_SENHA
```

Próximos acessos:

```text
/login SUA_SENHA
```

Use senha exclusiva. Nunca copie `EasyAuth/easyauth.db`, `server.properties` ou
credenciais RCON para o cliente ou para o repositório.

## Setup Windows

1. Instale Java 21 x64.
2. Crie uma instância Fabric 1.20.1 com Loader 0.19.5.
3. Extraia o setup e rode primeiro `Install-OnlyBangers.ps1 -CheckOnly`.
4. Rode o script normal; ele valida 51 jars e SHA-512 antes de copiar.
5. Entre pelo endereço Playit e autentique com EasyAuth.

Detalhes, erros comuns e separação cliente/servidor estão em
[`SETUP-WINDOWS-TLAUNCHER.md`](SETUP-WINDOWS-TLAUNCHER.md).

## Início e parada controlados

Operador autorizado pode usar systemd:

```bash
sudo systemctl status minecraft.service
sudo systemctl stop minecraft.service
sudo systemctl start minecraft.service
sudo systemctl restart minecraft.service
```

Antes de parar, salve pelo console/RCON local e confirme que o processo fechou.
O proxy depende do serviço Minecraft e deve acompanhar seu ciclo.

### Divergência systemd encontrada

O fragmento base de `/etc/systemd/system/minecraft.service` cita
`fabric-server-mc.1.21.1-loader...`, mas `aof7.conf` substitui `ExecStart` pelo
jar 1.20.1 atualmente em execução. O systemd alertou que a unidade carregada
está desatualizada. Próxima manutenção deve reconciliar o arquivo base, o
drop-in e o estado carregado; não faça `daemon-reload` durante jogo ativo sem
janela e plano de rollback.

## Atualização segura

1. Registre versão atual, jogadores e backup do mundo.
2. Faça save e pare o serviço.
3. Preserve `world/`, `server.properties`, EasyAuth e logs localmente.
4. Atualize Fabric/mods compatíveis com 1.20.1.
5. Revise dependências e hashes do manifest cliente.
6. Inicie, leia `latest.log` e valide Spark/TPS.
7. Teste conexão Playit, IPv6 e login EasyAuth.

Não misture jars de JEI/EasyAuth no cliente. EMI é o item browser usado pelo
pack atual; SkinRestorer permanece no servidor.

## Diagnóstico rápido

| Sintoma | Checagem | Ação |
| --- | --- | --- |
| Não conecta via Playit | `systemctl status playit.service` | Conferir serviço, endpoint e logs do túnel. |
| IPv6 falha | `ss -lntup` | Confirmar proxy e porta 25565. |
| Login falha | `latest.log` + EasyAuth | Repetir `/register` ou `/login`; não apagar banco. |
| TPS cai | Spark health/profiler | Identificar chunk generation, entidades ou Create antes de mudar mods. |
| Cliente fecha | `Install-OnlyBangers.ps1 -CheckOnly` | Confirmar Java 21, Loader 0.19.5 e 51 hashes. |
| Unidade cita 1.21.1 | `systemctl cat minecraft.service` | Planejar reconciliação; não alterar live às cegas. |

## Kit AOF7 legado

O `aof7_installer.py` permanece para os testes do downloader: `--check-only`,
retomada `.part`, retry, SHA-256, escrita atômica e backup do Launcher. Esse
fluxo é histórico e não deve ser confundido com o setup OnlyBangers atual.
