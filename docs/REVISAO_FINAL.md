# Revisão final do AURA

**Revisão inicial: 16/09/2026. Atualização: 17/09/2026.** Escopo: código Django/DRF, templates, CSS/JS, dependências, configuração, testes e documentação do repositório. Esta revisão não é certificação de segurança nem homologação institucional.

Atualização do cadastro: professor pode adicionar um campus com endereço ao criar a conta. A instituição fica sem coordenadas até confirmação administrativa pelo Admin ou API. Isso não implementa aprovação de professor nem seleção explícita de campus por aula; as pendências abaixo permanecem.

## Parecer

**MVP: pronto para ensaio final orientado, ainda não para encerrar a validação. Uso oficial pela faculdade: não homologado.**

O fluxo principal está implementado e há testes automatizados para autenticação, permissões, seleção de matéria/turma/aula, QR, GPS, falta fora do raio, duplicidade e interface. O usuário relatou um teste real fora do raio. Falta registrar o percurso completo dentro do campus, conferir frequência com dados conhecidos e exercitar a instalação final.

Para concluir o TCC, alinhar o escopo com o orientador, executar o roteiro de aceite e explicitar as limitações abaixo. Aprovação acadêmica depende dos critérios da instituição; testes aprovados não são garantia de segurança ou capacidade para uso oficial.

## Melhorias por prioridade

### P1 — corrigir ou decidir antes de uma entrega definitiva

1. **Frequência pode representar algo diferente de aulas realizadas.**
   - Evidência: [accounts/views.py](../backend/accounts/views.py), `frequency_result` e `_calcular_frequencia`; [ui_api.py](../backend/backend/ui_api.py), `WorkspaceView`.
   - Hoje entram todas as sessões, inclusive abertas e anteriores à matrícula. Encerrar e iniciar outra chamada da mesma aula aumenta o denominador novamente. Exemplo: aluno com uma presença em uma aula passa a 50% se essa aula receber uma segunda sessão sem presença.
   - Melhor opção: definir formalmente a unidade da frequência (aula ou sessão), quando consolidar faltas e como tratar matrícula tardia. Depois centralizar a consulta e testar todas as telas. **Regra preservada nesta revisão**, pois exige decisão acadêmica.

2. **Concorrência corrigida na API; homologação em PostgreSQL ainda pendente.**
   - [transactions.py](../backend/attendance/transactions.py), serializers e views agora usam transação e bloqueio compartilhado entre registro, leitura do QR, renovação e encerramento. Validações são repetidas no momento de salvar; bloqueio da aula serializa aberturas simultâneas.
   - Testes com conexões independentes em SQLite de arquivo cobrem os dois resultados possíveis da disputa registro/encerramento, token, matrícula e comprovante que mudam após validação, renovação simultânea, abertura repetida e duplicatas com GPS diferentes. PATCH com instância antiga não reabre sessão.
   - No SQLite, BEGIN IMMEDIATE e espera limitada coordenam as escritas; no PostgreSQL, SELECT FOR UPDATE é o mecanismo previsto. Ainda é necessário repetir a bateria com PostgreSQL real e medir a carga esperada. Nenhum teste de pequeno lote garante capacidade para uma faculdade.
   - O escopo é o fluxo de chamada da API. Alterações administrativas simultâneas, como trocar a turma de uma aula durante a chamada, não receberam a mesma coordenação. O tratamento de banco ocupado cobre as operações dentro de `chamada_atomic`, não toda consulta da aplicação.

3. **Cadastro de professor sem aprovação e autenticação com proteção limitada.**
   - Evidência: [accounts/serializers.py](../backend/accounts/serializers.py), `UserRegistrationSerializer`; `RegisterView`; [settings.py](../backend/backend/settings.py).
   - Qualquer visitante pode escolher professor e instituição. Isso não dá acesso às matérias de outros professores, mas permite criar turmas com essa identificação institucional. Não há limitação de tentativas de login/cadastro/código, confirmação de e-mail ou recuperação de senha.
   - Melhor opção: convite/aprovação administrativa para professores, política de senha usando validadores Django, limites de tentativas e recuperação verificada. O filtro de e-mail atual aceita apenas Gmail/Hotmail/Outlook e impede endereços acadêmicos; deve ser revisto junto dessa política.

4. **QR depende de terceiro e envia o token da chamada para ele.**
   - Evidência: [frontend/professor.js](../frontend/professor.js), `showQR`, atribui imagem de `api.qrserver.com` contendo a URL completa.
   - A queda/bloqueio desse domínio impede exibir o QR; o fornecedor recebe o token, ainda que ele sozinho não dispense login e matrícula.
   - Melhor opção: gerar SVG localmente no backend, com endpoint restrito ao professor e sem cache do token. `qrcode` e Pillow estavam declarados, mas não eram utilizados: foram retirados dos requisitos atuais; adicionar somente a biblioteca necessária quando a geração local for implementada.

5. **Campus da chamada pode ser escolhido implicitamente.**
   - Evidência: [attendance/views.py](../backend/attendance/views.py), `perform_create`.
   - Com várias instituições, usa a primeira ativa; não há seleção por turma/aula. O vínculo singular de fallback pode estar inativo.
   - Melhor opção: vínculo explícito da turma/aula com instituição autorizada e confirmação visível do local antes da chamada. Para demonstração, usar professor vinculado apenas à instituição do ensaio.

### P2 — necessárias antes de operação institucional contínua

6. **Preservar histórico acadêmico.** [courses/models.py](../backend/courses/models.py) e [attendance/models.py](../backend/attendance/models.py) usam exclusão em cascata. Excluir matéria/turma/aula pode remover presenças. Preferir arquivamento ou proteção quando há histórico, correções com motivo e autoria e política para justificativas. Hoje a primeira tentativa GPS é definitiva; não há fluxo auditado de revisão.

7. **Validar matrícula pelo papel correto.** `TurmaAlunoSerializer` restringe a turma ao professor, mas o campo `aluno` aceita qualquer usuário. Restringir o queryset a contas de aluno e testar rejeição de professor como matriculado. Rever também o catálogo global de matérias visível a alunos e a exposição do código de turma na API geral.

8. **Completar OpenAPI.** `check --deploy --fail-level WARNING` encontrou seis avisos do drf-spectacular: falta de tipo de `Instituicao.endereco_completo` e serializers/contratos de `AlunoEntrarTurmaView`, `AlunoMinhaFrequenciaView`, `AlunoTurmasView`, `ProfileView` e `WorkspaceView`. As rotas funcionam, mas parte da documentação gerada é omitida. Documentar requests/responses reais com serializers ou anotações; não silenciar os avisos.

9. **Limitar volume de consultas e respostas.** O painel ainda carrega todo o histórico de aulas/sessões e matrículas. Paginar listas, filtrar por período e buscar detalhes sob demanda. Consolidar carregamentos duplicados do painel do aluno, manter pausa de polling quando a aba estiver oculta e medir antes de acrescentar cache/WebSockets. A cada 5 s, 100 painéis fazem aproximadamente 20 consultas HTTP/s apenas de polling; isso é uma estimativa, não um teste de carga.

10. **Operação e reprodutibilidade.** Adicionar CI com testes Python/JS e PostgreSQL, fixar versões resolvidas para a entrega, verificar dependências conhecidas vulneráveis e testar backup/restauração. Os intervalos em `requirements.txt` ainda permitem que instalações futuras resolvam versões diferentes. Medir latência e memória na hospedagem real; não presumir que SQLite ou um plano pequeno suportará uma turma inteira simultaneamente.

### P3 — manutenção e evolução

- Dividir e formatar funções longas de `workspace.js`/`student-workspace.js`, separando renderização, consulta e formulário sem adicionar framework.
- Ampliar testes reais de navegador para foco, teclado, acessibilidade, telas pequenas, câmera e renovação de login.
- Avaliar cookies HttpOnly para autenticação e revogação de sessão; hoje JWT fica em `localStorage` e logout não revoga o refresh no servidor.
- Rever a precisão GPS exibida, o tratamento de leituras imprecisas e a retenção de coordenadas. Não apresentar GPS como prova antifraude. Definir a finalidade e quem pode acessar os dados antes de uso com alunos reais.

## Limpeza e otimizações já executadas

- Excluídos cinco CSS sem referência: `frontend/login.css`, `register.css`, `aluno.css`, `professor.css` e `confirmar-presenca.css`. `app.css` continua como estilo compartilhado.
- Removidas dependências Python diretas sem uso: `qrcode` e Pillow. Não foram desinstaladas à força dos ambientes existentes.
- Retirados o serviço Celery que não tinha aplicativo/broker configurado e o ramo de tarefa dinâmica. O fallback legado de CEP usa thread e agora fecha conexões ao concluir.
- Retirados a permissão não usada `CanViewSessionToken`, wrappers duplicados de Haversine, imports sem uso, configuração de raio não consultada e opção de blacklist inoperante. Removido o catch-all de arquivos frontend em DEBUG; páginas explícitas e `/static/` permanecem.
- Padronizado Django 5.2.17+ em todas as versões de Python suportadas. A seleção anterior podia instalar Django 4.2 no Docker com Python 3.11. [Django 4.2 encerrou suporte em abril de 2026](https://www.djangoproject.com/download/).
- Integrados WhiteNoise, compressão estática, origem CSRF configurável, redirecionamento HTTPS em produção e rejeição de chave curta/placeholder. `.env` existente foi preservado.
- Criado `.dockerignore` para excluir banco local, backups, segredos e ambientes do contexto de build. Docker coleta estáticos sem templates e testes JS.
- Presenças válidas agregadas com `COUNT` no banco, em vez de trazer uma linha por presença para contar em Python. Relatórios indexados por turma em uma passagem, evitando varrer todas as matrículas para cada turma. `select_related('aula')` evita uma consulta extra na validação de presença.
- Nenhum campo de modelo, migration, dado acadêmico, cálculo de frequência ou regra de GPS foi alterado. Não foram apagados banco, backups, ambientes ou configurações pessoais.

## Documentação corrigida

- `README.md`: tecnologias reais, comandos locais, código de turma, falta persistida, limites do GPS e links atuais.
- `GUIA_TECNICO.md`: arquitetura, endpoints, autenticação, instituições, cálculo atual e produção.
- `TESTE_CELULAR.md`: notebook/rede, comandos sem Markdown na URL, entrada por código e aceite de presença/falta.
- `INTERFACE.md`: barra superior, estilos atuais, Django 5.2 e WhiteNoise.
- `REGISTRO_ALTERACOES.md`: entradas novas separadas do histórico.
- `AURA_Analysis.md`: substituído por ponteiro para esta revisão; não recomenda mais WebAuthn removido nem descreve ausência de testes já existentes.
- Criados `HOSPEDAGEM.md` e este relatório.

Os documentos agora distinguem implementação, limitações e funcionalidades futuras. OpenAPI automático continua com os avisos descritos acima.

## Validação e limites

- Suíte Python em 17/09/2026: **92 testes aprovados**, incluindo 16 de concorrência, em Python 3.14.0 / Django 5.2.17.
- JavaScript: **26 testes aprovados**, incluindo respostas atrasadas, cliques repetidos e encerramento por outra aba.
- `manage.py check`: sem problemas.
- `makemigrations --check --dry-run`: nenhuma mudança de modelo detectada.
- `collectstatic`: coleta e compressão concluídas.
- Teste de produção adicionado para páginas e estáticos com `DEBUG=False`, incluindo redirecionamento HTTPS.
- `check --deploy --fail-level WARNING`: seis avisos de schema OpenAPI; não é uma verificação integralmente aprovada.
- `check --deploy --tag security --fail-level WARNING`: sem problemas, com `DEBUG=False` e chave temporária de teste. Isso valida configurações do Django, não elimina os riscos de negócio/autenticação descritos acima.
- Testes locais usam SQLite e Python 3.14/Django 5.2.17. PostgreSQL real, build Docker, carga, restauração de backup, console/visual em navegador e câmera/GPS físicos não foram validados nesta revisão.

## Critério para concluir o MVP do TCC

- [ ] Registrar sucesso dentro do raio e falta fora dele, com aparelhos reais.
- [ ] Conferir frequência esperada contra relatórios e CSV, incluindo aula reaberta e aluno recém-matriculado; corrigir ou documentar a política aprovada.
- [ ] Repetir o encerramento próximo ao envio em celulares e PostgreSQL; os cenários automatizados locais já cobrem a disputa de bloqueios.
- [ ] Ensaiar o cenário completo de professor e aluno na rede da faculdade.
- [ ] Repetir o fluxo na hospedagem escolhida com PostgreSQL, HTTPS e `DEBUG=False`, caso a entrega inclua hospedagem.
- [ ] Definir com o orientador quais limitações serão apresentadas como trabalho futuro, sem prometer funções não implementadas.
- [ ] Guardar backup restaurável, versão de entrega e roteiro da apresentação.

**Recomendação prática:** terminar primeiro os ensaios de aceite e a decisão de frequência. Para disponibilizar publicamente com contas reais, priorizar também autenticação de professor, geração local de QR e validação de concorrência/capacidade no PostgreSQL de implantação. O guia de hospedagem não substitui essas etapas.
