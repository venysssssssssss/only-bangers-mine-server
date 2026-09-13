# Operação

## Pré-requisitos

- Windows com PowerShell/CMD disponível.
- Minecraft Launcher instalado.
- Rede capaz de acessar as URLs HTTPS do manifest.
- Espaço livre para a instância e para o ZIP distribuível.

O instalador usa os arquivos Python embutidos no bootstrap. Não instale
dependências de terceiros para executar o kit.

## Instalação normal

1. Feche o Minecraft Launcher antes de alterar perfis.
2. Abra um PowerShell na raiz do kit.
3. Execute:

   ```powershell
   .\windows-kit\Install-AOF7.cmd
   ```

4. Aguarde a validação e os downloads.
5. Abra o perfil `AOF7-2.5.3` no Launcher.
6. Se o servidor iniciar com overrides, confira os logs do servidor para
   confirmar que o KubeJS carregou as receitas esperadas.

O PowerShell grava o transcript em `logs\\install.log`. Esse arquivo é útil
para diagnóstico local e não deve ser commitado.

## Verificar sem instalar

Use o manifest mínimo e uma pasta temporária para testar parsing e validação:

```powershell
python windows-kit/aof7_installer.py --check-only `
  --manifest tests/fixtures/manifest-minimal.json `
  --output-root C:\AOF7-check
```

O comando deve informar uma entry e não criar `C:\AOF7-check\mods`.

Para executar as verificações do próprio módulo:

```powershell
python windows-kit/aof7_installer.py --self-test
```

## Reexecução e retomada

O instalador pode ser executado novamente após uma interrupção. Arquivos que
já correspondem ao estado esperado são pulados; um arquivo parcial permanece
como `.part` durante o download e pode ser retomado com uma requisição Range.

Se a tentativa final falhar:

1. preserve a mensagem do console e `logs\\install.log`;
2. confirme espaço livre e conectividade;
3. execute novamente o instalador;
4. se o `.part` estiver claramente corrompido, remova apenas esse arquivo e
   repita, sem remover o destino validado anterior.

## Perfil do Minecraft Launcher

O perfil AOF7 é adicionado sem remover perfis existentes. Antes da escrita, o
instalador cria `launcher_profiles.json.aof7-backup`. Se o Launcher não mostrar
o perfil:

1. feche o Launcher;
2. confirme que o diretório de jogo apontado é a instância AOF7;
3. compare o perfil com o backup;
4. execute novamente o instalador.

Não substitua manualmente o arquivo inteiro por uma cópia de outra máquina:
isso pode remover perfis válidos do usuário.

## Atualizar o pack

1. Altere somente as entries necessárias em `windows-kit/manifest.json`.
2. Confirme Minecraft, Fabric Loader, URL HTTPS, caminho, tamanho e SHA-256.
3. Atualize overrides em `windows-kit/overrides/` somente quando a mudança
   de jogo exigir.
4. Rode:

   ```powershell
   python -m unittest discover -s tests -v
   python windows-kit/aof7_installer.py --self-test
   ```

5. Revise o diff completo antes de criar o ZIP em `dist/`.

## Diagnóstico por sintoma

| Sintoma | Primeiro diagnóstico | Ação segura |
| --- | --- | --- |
| Manifest rejeitado | Versão, URL ou caminho inválido | Corrigir a entry e rodar `--check-only`. |
| Download interrompido | Rede, espaço ou resposta transitória | Reexecutar e aproveitar `.part`. |
| Hash divergente | Fonte mudou ou arquivo foi alterado | Não aceitar o arquivo; confirmar a fonte e atualizar o manifest conscientemente. |
| Perfil ausente | Launcher aberto ou diretório incorreto | Fechar Launcher, conferir backup e repetir. |
| Receita ausente | Override não carregado | Conferir instância, logs do servidor e nome do script KubeJS. |
| Teste falhando | Regressão no instalador ou fixture | Ler o teste específico antes de alterar o código. |

## Testes de release

A verificação mínima antes de distribuir é:

```powershell
python -m unittest discover -s tests -v
python windows-kit/aof7_installer.py --self-test
```

Depois confira se `dist/AOF7-Windows-Kit-2.5.3.zip` corresponde aos arquivos
que serão entregues. O ZIP raiz `mine server.zip` não faz parte deste release
público porque excede o limite de arquivo do GitHub.
