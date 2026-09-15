# OnlyBangers — setup Windows + TLauncher

Setup validado para servidor atual.

## Servidor atual

O servidor live roda como serviço systemd em Linux, com Java 21 e Fabric
1.20.1. Cliente não deve receber mundo, EasyAuth, RCON ou configs server-only.

## Versões obrigatórias

- Minecraft: **1.20.1**
- Fabric Loader: **0.19.5** — nunca 0.16.0
- Java: **Temurin/OpenJDK 21 x64**
- Servidor Playit: `schmidt-flowers.tun.ply.gg:60986`
- Alternativa IPv6 direta: `[2804:14c:b531:81ef:4a4d:7eff:fefc:2587]:25565`
- Mods no cliente: 52 jars do manifesto `windows-kit/onlybangers-client-manifest.json`
- JEI: removido; o substituto é EMI
- EasyAuth: servidor-only; não copiar para o cliente
- SkinRestorer: já funciona no servidor; não exige mod adicional no cliente

## 1. Instalar Java

Baixe Java 21 x64:

<https://adoptium.net/temurin/releases/?version=21>

Instale normalmente. No TLauncher, selecione o executável Java 21 se ele não detectar sozinho.

## 2. Preparar TLauncher

1. Abra o TLauncher.
2. Crie/selecione **Fabric 1.20.1**.
3. Escolha **Fabric Loader 0.19.5**.
4. Em **Settings**, defina o diretório do jogo como:

   `C:\Users\SEU_USUARIO\Documents\OnlyBangers-1.20.1`

5. Feche o jogo antes de instalar os mods.

> Use uma pasta exclusiva. Não misture este pack com outro perfil ou mods antigos.

## 3. Instalar o pack

Obtenha o pacote completo `OnlyBangers-Windows-Setup.zip` como artefato de
release do mantenedor e extraia-o no Windows. O ZIP e os jars não entram no
Git público por tamanho; script e manifesto no clone, sozinhos, não contêm os
52 arquivos necessários. A pasta precisa conter:

```text
OnlyBangers-Windows-Setup/
  Install-OnlyBangers.ps1
  onlybangers-client-manifest.json
  client-mods/*.jar
```

Abra PowerShell na pasta extraída e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Install-OnlyBangers.ps1 -CheckOnly
.\Install-OnlyBangers.ps1
```

O primeiro comando verifica Java, versões, presença dos 52 jars e SHA-512. O segundo copia tudo para `Documents\OnlyBangers-1.20.1\mods`.

Se já houver jars nessa pasta, o instalador move-os para um backup com timestamp antes de copiar o pack novo.

## 4. Mods por função

- **Conteúdo:** Create, Botania, Malum, TechReborn, IndustrialReborn,
  Hephaestus, Farmer's Delight, Vinery, AdventureZ, Supplementaries, Waystones
  e Sophisticated Backpacks.
- **Worldgen:** Terralith, Regions Unexplored, YUNG's Better Caves, YUNG's
  Better Nether Fortresses, TerraBlender, Chunky e Nature's Compass.
- **Cliente/UX:** EMI, Jade, Trinkets, Patchouli e Cloth Config.
- **Performance:** C2ME, Lithium, FerriteCore, ModernFix, Krypton, VMP,
  ServerCore, Spark, Ksyxis, LazyDFU, Clumps, MemoryLeakFix e Fabric Carpet.

JEI não faz parte do cliente atual; use EMI. EasyAuth e SkinRestorer ficam no
servidor.

## 5. Jogar

1. No TLauncher, mantenha Fabric 1.20.1 selecionado.
2. Confirme o diretório `OnlyBangers-1.20.1`.
3. Inicie o jogo.
4. Adicione servidor:

   ```text
   schmidt-flowers.tun.ply.gg:60986
   ```

5. Primeiro acesso:

   ```text
   /register SUA_SENHA SUA_SENHA
   ```

   Próximos acessos:

   ```text
   /login SUA_SENHA
   ```

Contas originais e offline entram pelo EasyAuth. Use nick único e não compartilhe sua senha.

## 6. O que não copiar

Nunca copie do servidor para o cliente:

- `server.properties`
- `eula.txt`
- pasta `world`
- pasta `EasyAuth` ou `easyauth.db`
- senha/configuração RCON
- arquivos de backup

## 7. Erros comuns

**Incompatible mod set / missing mod**

- Confirme Fabric Loader 0.19.5.
- Execute o instalador com a pasta correta.
- Confirme que o TLauncher usa exatamente `Documents\OnlyBangers-1.20.1`.
- Não deixe JEI ou jars antigos em `mods`.

**Java version mismatch**

- Selecione Java 21 x64 no TLauncher.
- Não use Java 8, 17 ou 22 para este pack.

**Tela fecha ao iniciar**

- Abra `logs/latest.log` dentro da pasta do jogo.
- Verifique se todos os jars foram copiados.
- Rode novamente `Install-OnlyBangers.ps1 -CheckOnly`.

**Não consegue entrar**

- Playit exige a porta: `schmidt-flowers.tun.ply.gg:60986`.
- Se o Playit falhar por IPv6, use `[2804:14c:b531:81ef:4a4d:7eff:fefc:2587]:25565`.
- Depois de conectar, use `/register` ou `/login`.
- Skin personalizada é aplicada pelo servidor; cliente não precisa instalar mod de skin.

## 8. Verificação de sucesso

Instalação correta = script mostra `OK: 52 mods verificados`, TLauncher inicia Fabric 1.20.1, menu EMI aparece e conexão chega ao EasyAuth.
