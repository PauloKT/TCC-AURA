# Guia técnico do AURA

Referência da implementação em **17/09/2026**. O registro de alterações contém versões antigas; este guia descreve o comportamento atual.

Para estudar os conceitos, ensaiar a demonstração e preparar respostas à banca, consulte o [Guia de estudo e apresentação](GUIA_ESTUDO_APRESENTACAO.md).

## 1. Arquitetura

Django 5.2 LTS e DRF no backend; templates Django, HTML/CSS/JavaScript puro no frontend. Sem React, Bootstrap, Celery ou biometria. SQLite em desenvolvimento; PostgreSQL selecionado por variáveis `DB_*`, sem depender de Docker.

- `backend/backend/settings.py`: ambiente, banco, JWT, CORS e WhiteNoise.
- `backend/backend/urls.py`: páginas explícitas (inclusive com `DEBUG=False`), APIs e OpenAPI.
- `backend/backend/ui_api.py`: perfil e dados dos painéis; contagem de presenças agregada no banco e agrupamento de relatórios em uma passagem.
- `backend/accounts/`: usuário, cadastro, login, frequência e geocodificação legada por CEP.
- `backend/courses/`: instituição, matéria, turma, matrícula e aula.
- `backend/attendance/`: sessão de chamada, resultado e geofence.
- `backend/templates/`: bases e includes compartilhados.
- `frontend/`: cinco páginas, `app.css`, marca, componentes e scripts. Detalhes em [INTERFACE.md](INTERFACE.md).

Gunicorn executa o Django em produção; WhiteNoise entrega CSS, JavaScript e imagens coletados em `STATIC_ROOT`. `runserver` é usado somente para desenvolvimento. Não há armazenamento de uploads implementado no fluxo atual.

## 2. Autenticação e permissões

`POST /api/login/` recebe usuário e senha; devolve `access`, `refresh` e dados do usuário. Access dura 60 minutos; refresh, um dia. O frontend guarda ambos em `localStorage` e renova o access em `/api/token/refresh/`. Sair limpa os tokens locais; não há revogação de refresh no servidor.

Professor altera apenas seus recursos. Aluno consulta turmas em que está matriculado e registra sua própria presença. O catálogo `/api/materias/` ainda permite leitura de todas as matérias por alunos autenticados. A API dos painéis limita dados ao professor responsável ou aluno matriculado.

O cadastro público permite escolher professor ou aluno. Aluno informa matrícula; professor seleciona instituições ativas. Os e-mails aceitos são Gmail, Hotmail e Outlook (incluindo `.com.br`); não há verificação de e-mail, recuperação de senha ou aprovação de professor. Senha exige 5 caracteres, maiúscula, número e símbolo; não utiliza os validadores globais de senha do Django. Essas são limitações a resolver antes de uso institucional.

## 3. Instituição e turma

No cadastro de professor, é possível escolher instituições existentes ou usar **Adicionar nova instituição**. O campo opcional `nova_instituicao` em `POST /api/register/` recebe nome, logradouro, número, bairro, cidade e UF brasileira. Conta e instituição são criadas na mesma transação. Alunos não podem usar esse campo e não é permitido combinar instituição nova e existentes no mesmo envio.

A instituição nova fica ativa no catálogo, mas com localização pendente (latitude/longitude vazias e raio inicial de 100 m); campos de coordenadas e raio enviados no cadastro público não são aceitos como configuração. Ela é vinculada ao professor e não permite iniciar chamadas até a confirmação administrativa. Nomes repetidos, inclusive com diferença apenas de maiúsculas, são rejeitados.

O administrador pode acessar `/admin/courses/instituicao/`, conferir endereço, preencher latitude/longitude e raio e salvar. O formulário administrativo valida limites e o preenchimento das duas coordenadas juntas; registra data e fonte da confirmação. A ação administrativa da API continua disponível. Não há migration nova para esse fluxo.

O professor pode vincular múltiplas instituições. Ao abrir uma sessão, o backend usa a primeira instituição ativa da relação; se nenhuma for encontrada, usa o vínculo singular legado e, por último, as coordenadas legadas do professor. A interface ainda não escolhe campus por aula. O fallback singular não revalida o campo `ativa`.

A migration `courses/0004_confirm_aems_coordinates.py` grava a AEMS em latitude `-20.786820236467992`, longitude `-51.668829782798554`. Isso descreve o código de inicialização, não comprova a localização física de cada instalação; confira o banco e o raio antes do teste.

A turma possui código aleatório único de **8 caracteres**, exibido ao professor. O aluno envia `codigo_acesso` para entrar. `link_acesso` e a compatibilidade com convite antigo permanecem no backend para instalações existentes. Código da turma é diferente do token de uma chamada: não substitui o QR para registrar presença.

## 4. Fluxo de chamada

1. Professor cria matéria, turma e aula; inicia sessão da própria aula.
2. A sessão copia a localização e o raio da instituição. Alterações posteriores na instituição não mudam essa referência.
3. O token expira após 30 segundos. O painel consulta o token e a API o renova quando expirado. Rotação depende dessas consultas; não há tarefa agendada.
4. A URL do QR usa a origem em que o professor abriu a página. A imagem é gerada por `api.qrserver.com`, que recebe essa URL e seu token.
5. Aluno matriculado lê o QR. `/api/sessoes/{id}/preparar/` valida sessão/token e devolve comprovante assinado para aquele aluno e sessão, válido por 120 segundos.
6. A página solicita localização e envia comprovante e coordenadas a `/api/presenca/registrar/`. A API também aceita token atual diretamente.
7. Coordenadas válidas dentro do raio geram `valida=True`; fora do raio geram `valida=False` (**falta**). Ambos retornam HTTP 201. O primeiro resultado por aluno/sessão é preservado; reenviar coordenadas diferentes não o substitui.
8. Resultado salvo deixa de aparecer nas chamadas pendentes. Professor consulta os resultados a cada cinco segundos enquanto a tela está aberta.

Token inválido, comprovante expirado, coordenadas inválidas, falta de matrícula ou sessão encerrada são rejeitados. Negar GPS ou falhar na captura não envia resultado nem grava falta.

### Operações simultâneas

`attendance/transactions.py` centraliza transações curtas. Registro, leitura validada do QR, renovação e encerramento recarregam e bloqueiam a mesma sessão. No registro, matrícula, estado da sessão, token/comprovante e prazo são verificados novamente depois de obter o bloqueio, antes de gravar. O bloqueio da matrícula também impede sua remoção durante essa gravação no PostgreSQL.

- Se o registro obtiver o bloqueio primeiro, ele termina e o encerramento ocorre depois; o resultado é preservado.
- Se o encerramento obtiver o bloqueio primeiro, o registro encontra a sessão fechada e é rejeitado. A ordem relevante é a do banco, não a hora em que o usuário clicou.
- Duas telas consultando um token vencido não o renovam de maneira independente: a segunda lê o token que a primeira já renovou. Token válido não é trocado antecipadamente. Respostas de token e comprovante usam `Cache-Control: no-store`.
- A abertura bloqueia a aula e consulta a sessão ativa com bloqueio, evitando sessões duplicadas criadas simultaneamente pela API. Não foi adicionada restrição nova para dados históricos nem alterada a regra de reabrir após encerramento.
- PATCH/PUT de sessão recarrega seu estado sob bloqueio para não restaurar acidentalmente um estado antigo. Exclusão da sessão usa o mesmo bloqueio.
- Envios repetidos continuam preservando o primeiro resultado por aluno/sessão. Encerrar uma chamada já fechada continua retornando HTTP 400, sem mudar a data de encerramento.

No painel, respostas de seleções antigas são descartadas. Início, encerramento e renovação têm proteção contra envios sobrepostos; os resultados informam o estado da sessão para reconhecer encerramentos em outra aba. Essa coordenação não se estende a qualquer edição administrativa: trocar a turma de uma aula durante a chamada ainda exige revisão específica do CRUD.

Em PostgreSQL, `select_for_update()` bloqueia linhas. Em SQLite, essa operação não tem efeito; por isso a configuração usa `transaction_mode=IMMEDIATE` e espera de até 20 segundos para reservar a escrita. Isso serializa transações de escrita do banco local e não transforma SQLite em um banco de alta concorrência. Saturação de bloqueio nas operações protegidas retorna HTTP 503 com orientação para tentar novamente; outros erros de banco não são ocultados. Não há repetição automática do envio.

As transações não aguardam GPS, serviços externos ou interação humana. O limite de 120 segundos continua sendo o prazo do comprovante, não a duração de uma transação. Fundamentação: [transações SQLite no Django](https://docs.djangoproject.com/en/5.2/ref/databases/#transactions-behavior) e [select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).

`attendance/geolocation.py` valida coordenadas finitas, raio de 1 a 10.000 m e aplica pré-filtro geográfico seguido de Haversine. A referência é a instituição, não a posição do computador. Não há prova de autenticidade das coordenadas fornecidas pelo navegador nem validação de Wi-Fi/IP.

## 5. Frequência e histórico

A frequência é **presenças válidas / quantidade de sessões da turma × 100**. O status é `sem_dados` sem sessões, `aprovado` a partir do mínimo da matéria e `reprovado` abaixo dele.

O cálculo inclui sessões abertas, sessões anteriores à matrícula e sessões diferentes da mesma aula. Reabrir uma aula com sessão ativa a reutiliza; iniciar após encerrar cria outra sessão. O campo chamado `aulas` nos relatórios representa sessões de chamada.

As faltas do relatório são total de sessões menos presenças válidas; incluem quem não enviou resultado. A lista abaixo do QR contém apenas registros enviados, com presente/falta, horário e quantidade aguardando. Não é a mesma lista de faltas calculadas no relatório.

Exclusões de matéria, turma, aula ou sessão podem apagar o histórico relacionado por cascata. Não há justificativa de falta, alteração auditada de presença ou arquivamento acadêmico implementados.

## 6. Rotas principais

- Autenticação: `POST /api/register/`, `/api/login/`, `/api/token/refresh/`.
- Instituições: `GET /api/instituicoes/`; ações administrativas `POST /api/instituicoes/{id}/geocodificar/` e `/confirmar-localizacao/`.
- CRUD do professor: `/api/materias/`, `/api/turmas/`, `/api/aulas/`, `/api/turma-aluno/` e respectivos detalhes `{id}/`.
- Sessões: `POST /api/sessoes/`; `GET /api/sessoes/{id}/token/` e `/resultados/`; `POST /api/sessoes/{id}/encerrar/`.
- Aluno: `GET /api/sessoes/ativas/`; `POST /api/sessoes/{id}/preparar/`; `POST /api/presenca/registrar/`.
- Turmas/frequência do aluno: `GET /api/aluno/turmas/`, `/api/aluno/minha-frequencia/`; `POST /api/aluno/entrar-turma/`.
- Interface: `GET /api/interface/perfil/` e `/api/interface/painel/`.
- Documentação gerada: `/api/schema/`, `/api/schema/swagger-ui/`, `/api/schema/redoc/`. APIs personalizadas ainda precisam de anotações para um schema completo.

## 7. Configuração e manutenção

Use `.env.example` como referência. Produção exige chave forte, `DEBUG=False`, domínio exato em `ALLOWED_HOSTS`, origem HTTPS em `CSRF_TRUSTED_ORIGINS`, banco PostgreSQL e proxy confiável que controle `X-Forwarded-Proto`. HTTPS é redirecionado automaticamente em produção.

O fallback de geocodificação por CEP usa thread daemon e fecha conexões de banco ao terminar; não é tarefa durável. Não existe worker Celery configurado. O novo cadastro utiliza instituições.

Migrations antigas de WebAuthn precisam permanecer para atualizar bancos existentes; `attendance/0005_remove_webauthn.py` remove as estruturas de biometria. Não apagar migrations nem banco para limpar o projeto.

## 8. Validação

No diretório `backend`, executar `python manage.py check`, `python manage.py makemigrations --check --dry-run` e `python -m pytest -q -p no:cacheprovider`. Na raiz, `node --test frontend/regressions.test.cjs`.

Resultado em 17/09/2026: **92 testes Python e 26 JavaScript aprovados**, `check` sem problemas e nenhuma mudança de modelo detectada. Entre os testes Python, 16 cobrem concorrência e revalidação de estado; a execução local utilizou SQLite em arquivo, Python 3.14.0 e Django 5.2.17.

O pytest usa `backend.test_settings`: em SQLite, cria e remove `backend/test-aura.sqlite3`, separado de `db.sqlite3`. Um arquivo real permite testar espera de bloqueio entre conexões; o SQLite compartilhado em memória não reproduz esse comportamento. Não execute duas suítes SQLite independentes ao mesmo tempo sobre esse arquivo. Para rodar apenas os cenários simultâneos: `python -m pytest test_attendance_concurrency.py -q -p no:cacheprovider`. Com PostgreSQL configurado, os testes usam o banco de teste gerenciado pelo Django; repetir essa bateria na infraestrutura de produção antes da homologação.

O teste de produção verifica páginas, redirecionamento HTTPS e arquivos estáticos com `DEBUG=False`. Os testes de interface/JavaScript não equivalem a teste visual nem de GPS real. Ver [TESTE_CELULAR.md](TESTE_CELULAR.md), [HOSPEDAGEM.md](HOSPEDAGEM.md) e [REVISAO_FINAL.md](REVISAO_FINAL.md).
