# AOF7 2.5.3 — instalador Windows

Este kit instala o cliente All of Fabric 7 2.5.3 para Minecraft 1.20.1 +
Fabric Loader 0.16.0 no launcher oficial.

## Instalação

1. Instale o Minecraft Launcher oficial e entre na conta Microsoft.
2. Extraia este ZIP para uma pasta local.
3. Execute `Install-AOF7.cmd` com duplo clique.
4. Aguarde os downloads do manifesto; são 436 arquivos e o processo pode ser
   retomado executando o instalador novamente.
5. No launcher oficial, selecione o perfil `AOF7 2.5.3` e atribua 6–8 GB de
   memória RAM antes de iniciar.

O destino padrão é:

`C:\Users\<seu-usuario>\Documents\AOF7-2.5.3`

O instalador baixa um Python 3.12.10 portátil, específico da arquitetura
Windows x64, ARM64 ou x86, dentro do destino. Não altera o Python do sistema,
não usa `pip` e não requer administrador.

Para validar o manifesto sem baixar mods, execute no PowerShell:

```powershell
.\Install-AOF7.ps1 -CheckOnly
```

Pelo Prompt de Comando, a forma equivalente é:

```bat
Install-AOF7.cmd --CheckOnly
```

Os logs ficam em `logs\`; o estado de downloads fica em
`.aof7-install-state.json`. Arquivos válidos são reutilizados e downloads
parciais usam arquivos temporários atômicos.

## Acesso ao servidor Only Bangers

- IPv6: `[2804:14c:b531:81ef:4a4d:7eff:fefc:2587]:25565`
- Playit: `schmidt-flowers.tun.ply.gg:60986`

O kit não contém JARs de mods: eles são baixados pelos links HTTPS registrados
no `manifest.json`. Nenhuma credencial ou token do launcher é solicitado ou
gravado pelo instalador.
