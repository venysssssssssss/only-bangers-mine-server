# only-bangers-mine-server: Publicação e documentação

## Objetivo

Transformar o diretório atual em um repositório GitHub público chamado
`only-bangers-mine-server`, preservando o material útil do servidor e deixando
claro como instalar, operar, validar e evoluir o kit AOF7.

## Escopo

- Inicializar ou reparar o controle de versão local sem reescrever conteúdo do projeto.
- Auditar arquivos antes de torná-los públicos.
- Criar uma sequência de commits pequenos e legíveis.
- Criar o repositório público via `gh`, conectar o remoto e publicar a branch principal.
- Documentar o projeto em português, mantendo nomes de comandos, arquivos e APIs originais.
- Explicar a arquitetura existente com diagramas Mermaid nativos do GitHub.
- Registrar instalação Windows, manifest, downloads, retomada, retries, cálculo/registro SHA-256, perfis do Minecraft Launcher, overrides KubeJS, testes e troubleshooting.

## Fora do escopo

- Reescrever o instalador ou alterar receitas/mods sem um defeito comprovado.
- Criar uma aplicação web, site de documentação ou pipeline CI novo.
- Adicionar dependências apenas para gerar diagramas: Mermaid no Markdown já é suficiente.
- Publicar credenciais, tokens, arquivos de configuração pessoal, logs transitórios ou caches.
- Reescrever histórico Git existente; o diretório atual não contém um repositório utilizável.

## Decisões

1. **Documentação Markdown + Mermaid.** O GitHub renderiza os diagramas diretamente e não exige build.
2. **README como índice.** O README explica o caminho feliz e aponta para os documentos detalhados.
3. **Diagrama orientado ao fluxo real.** A documentação acompanha o caminho manifest → validação → download → verificação → instalação → launcher.
4. **Auditoria de publicação antes do `git add -A`.** A regra pública é bloquear segredos e artefatos transitórios, não esconder código do projeto.
5. **Commits por intenção.** A primeira publicação separa documentação, higiene de repositório e estado final do projeto para facilitar revisão.

## Arquitetura documentada

### Componentes

- **Bootstrap PowerShell/CMD:** entrada Windows, escolha de Python embutido, parâmetros e transcript de diagnóstico.
- **Instalador Python:** carrega o manifest, valida URLs/caminhos, baixa arquivos com retry e resume, calcula hashes para o estado e escreve o resultado.
- **Manifest:** fonte declarativa das versões Minecraft/Fabric e dos arquivos do modpack.
- **Diretório de saída:** instância isolada AOF7 com mods, overrides e estado de downloads.
- **Minecraft Launcher:** recebe ou preserva perfis existentes e aponta para a instância isolada.
- **Overrides KubeJS:** ajustes de receitas aplicados pelo servidor durante o carregamento.
- **Testes:** validam entradas, segurança de caminhos, downloads, retomada, atomicidade, bootstrap e perfil.

### Diagramas obrigatórios

`docs/architecture.md` conterá:

1. visão geral dos componentes e limites de responsabilidade;
2. sequência de uma instalação normal;
3. fluxo de falha, retry, arquivo `.part` e retomada;
4. fronteiras de confiança e controles contra traversal, URLs inseguras e credenciais;
5. ciclo de operação Windows → instância Minecraft → KubeJS → testes;
6. mapa de diretórios e responsabilidades.

## Documentos a entregar

- `README.md`: visão geral, requisitos, instalação rápida, comandos de verificação, estrutura e links.
- `docs/architecture.md`: arquitetura e diagramas didáticos.
- `docs/operations.md`: instalação, atualização, backup, diagnóstico e recuperação.
- `docs/security.md`: modelo de ameaça, dados públicos, segredos proibidos e controles existentes.
- `CONTRIBUTING.md`: fluxo de mudanças, testes mínimos e convenções de commit.
- `SECURITY.md`: canal e procedimento para relatar vulnerabilidades.
- `.gitignore`: apenas padrões para segredos, logs, caches, temporários e artefatos locais não versionáveis.

## Validação

Antes de afirmar conclusão:

1. executar a suíte existente com `python -m unittest discover -s tests -v`;
2. executar os checks nativos do instalador, quando disponíveis;
3. confirmar que nenhum arquivo público contém token, senha, chave privada ou segredo conhecido;
4. confirmar que diagramas e links locais apontam para arquivos existentes;
5. revisar `git diff --cached` e `git status` antes de cada commit;
6. após autenticação, criar o repo público exato, fazer push e validar `gh repo view`.

## Critérios de aceite

- O remoto público é `only-bangers-mine-server` no usuário autenticado do `gh`.
- A branch principal publicada contém o código, os assets e a documentação segura do projeto.
- O README permite que uma pessoa nova entenda o propósito e encontre a instalação.
- Os diagramas descrevem os fluxos reais sem inventar serviços externos.
- A suíte de testes termina com código de saída zero, ou o bloqueio fica explicitamente documentado.
- Commits e arquivos excluídos são explicados no histórico/documentação.
