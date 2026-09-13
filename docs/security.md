# Segurança

## Modelo de ameaça

O instalador recebe um manifest local e bytes de servidores externos. O risco
principal é transformar uma entrada ou download incorreto em arquivos dentro da
instância do Minecraft, ou publicar dados privados junto do projeto.

### Entradas consideradas não confiáveis

- URLs e respostas HTTP(S) dos hosts de download.
- Caminhos de arquivos declarados no manifest.
- Arquivos parciais deixados por uma execução interrompida.
- Alterações locais no manifest antes de uma release.
- Arquivos adicionados ao stage por engano antes de um push público.

## Controles existentes

| Risco | Controle |
| --- | --- |
| Caminho escapando da instância | `safe_join` rejeita path traversal. |
| Transporte inseguro | O manifest real exige URLs HTTPS. |
| Credencial vazando na URL | URLs com usuário ou senha são rejeitadas. |
| Download incompleto | O tamanho recebido é conferido quando a resposta informa `Content-Length`; o SHA-256 recebido é registrado no estado. |
| Interrupção no meio da gravação | Download ocorre em `.part` e só depois é promovido. |
| Perda de arquivo válido | Falha de substituição preserva o destino anterior. |
| Perda de perfil do Launcher | Mesclagem cria `launcher_profiles.json.aof7-backup`. |
| Diagnóstico indisponível | Bootstrap grava transcript em `logs\\install.log`. |

Esses controles protegem o fluxo de instalação; eles não transformam hosts
externos em fontes automaticamente confiáveis. O manifest atual não contém
hashes esperados por arquivo, então o digest salvo no estado é auditoria local,
não uma prova independente de autenticidade. Uma mudança de URL ou hash deve
ser revisada como mudança de supply chain.

## Dados que nunca devem ser publicados

- tokens, senhas, cookies ou chaves de API;
- chaves privadas, certificados pessoais e credenciais de cloud;
- `launcher_profiles.json` de uma máquina real;
- logs que contenham nomes de usuário, caminhos pessoais ou tokens;
- caches, arquivos `.part` e artefatos temporários;
- `mine server.zip`, que é grande demais para o GitHub e pode conter estado
  local fora do escopo do kit;
- metadados do workspace (`.agents/`, `.codex/`, `.dual-graph*/`).

## Checklist antes de uma release

1. Leia `git status --short --ignored`.
2. Revise `git diff --cached --name-only`.
3. Procure manualmente por segredos em arquivos novos e alterados.
4. Confirme URLs HTTPS e os metadados disponíveis no manifest.
5. Rode a suíte de testes e o self-test do instalador.
6. Confirme que o arquivo grande e os logs continuam ignorados.

Se um segredo for publicado, revogue-o e faça a rotação imediatamente. Remover
o texto de um commit posterior não invalida o segredo já exposto.

## Limites conhecidos

- O projeto não assina os manifests nem verifica assinatura de metadata externa.
- O SHA-256 salvo no estado depende dos bytes recebidos; o manifest ainda não
  fornece um hash esperado para comparação independente.
- O transcript local pode conter detalhes úteis para diagnóstico; por isso ele
  é ignorado e não deve ser anexado publicamente sem revisão.
