# Guia Técnico do AURA

## 1. Objetivo

O AURA é um sistema web acadêmico para controle de frequência. O backend fornece uma API Django REST Framework e o frontend atual utiliza HTML, CSS e JavaScript puro.

O fluxo ativo valida a presença por:

1. QR Code dinâmico associado a uma sessão de aula.
2. Localização GPS do aluno em relação ao local registrado pelo professor.
3. Matrícula do aluno na turma.

A biometria foi removida. O registro exige login, matrícula, QR Code válido e localização dentro do raio institucional.

A geolocalização é centralizada no backend. O navegador coleta a posição e a
envia à API; qualquer cálculo visual no frontend não é usado para autorizar a
presença.

## 2. Arquitetura

```text
Navegador
  |
  | HTML + CSS + JavaScript / fetch
  v
Django URLs (/api/)
  |
  +-- accounts    -> usuários, cadastro, login JWT e frequência do aluno
  +-- courses     -> matérias, turmas, aulas e matrículas
  +-- attendance  -> sessões, QR Code, presença e GPS
  |
  v
SQLite (desenvolvimento) ou PostgreSQL (Docker)
```

O projeto não possui mais uma segunda implementação React. A entrada web em desenvolvimento é servida por `frontend/login.html`, conforme a configuração de URLs do Django.

## 3. Organização do código

### `backend/backend/`

- `settings.py`: configurações de ambiente, apps instalados, autenticação JWT, CORS e banco de dados.
- `urls.py`: rotas administrativas, API, documentação OpenAPI e servidor de arquivos do frontend em desenvolvimento.
- `asgi.py` e `wsgi.py`: pontos de entrada para servidores ASGI e WSGI.

### `backend/accounts/`

- `models.py`: modelo `CustomUser`, papéis de professor/aluno e geocodificação do CEP.
- `serializers.py`: validação de cadastro e inclusão de dados do usuário nos tokens JWT.
- `views.py`: cadastro, login e consultas de frequência do aluno.
- `tasks.py`: execução assíncrona da geocodificação quando necessário.
- `urls.py`: cadastro, login, refresh JWT e endpoints de frequência.
- `tests.py`: validações de cadastro, geocodificação, login e refresh de tokens.

### `backend/courses/`

- `models.py`: `Instituicao`, `Materia`, `Turma`, `TurmaAluno` e `Aula`.
- `geocoding.py`: busca candidatos de localização para um endereço completo; o primeiro resultado não é aceito automaticamente.
- `serializers.py`: representação e validação dos recursos acadêmicos.
- `views.py`: ViewSets e filtros por papel do usuário.
- `urls.py`: rotas REST de matérias, turmas, aulas e matrículas.
- A API `GET /api/instituicoes/` lista instituições ativas. Administradores podem buscar candidatos em `POST /api/instituicoes/{id}/geocodificar/` e confirmar uma coordenada em `POST /api/instituicoes/{id}/confirmar-localizacao/`.
- `tests.py`: regras de criação, unicidade e associação entre entidades.

### `backend/attendance/`

- `models.py`: sessão de chamada e presença.
- `serializers.py`: tokens da sessão e validação do registro de presença.
- `views.py`: criação, consulta, renovação e encerramento de sessões; registro de presença.
- `tests.py`: tokens, GPS, idempotência, API de presença.

### `frontend/`

- `login.html` e `login.js`: autenticação e armazenamento dos tokens JWT.
- `register.html` e `register.js`: cadastro de usuários.
- `professor.html` e `professor.js`: matérias, turmas, aulas e sessão de chamada.
- `aluno.html` e `aluno.js`: turmas e situação de frequência.
- `confirmar-presenca.html` e `confirmar-presenca.js`: leitura dos parâmetros do QR Code, geolocalização e envio do registro.
- Arquivos CSS: apresentação visual das telas tradicionais.

## 4. Autenticação

O login é feito em `POST /api/login/` com `username` e `password`. A resposta contém:

- `access`: token de acesso JWT.
- `refresh`: token usado para obter novo access token.
- `user`: id, username, email e papel do usuário.

O frontend guarda os tokens em `localStorage`. As requisições protegidas enviam `Authorization: Bearer <access>`.

Professores selecionam uma instituição ativa no cadastro. A instituição fornece
o endereço, as coordenadas confirmadas e o raio padrão do geofence.

A renovação é feita em `POST /api/token/refresh/` com o refresh token. Essa rota é necessária para evitar que a sessão termine quando o access token expira.

## 5. Fluxo de presença

### Professor

1. Está associado a uma instituição ativa com coordenadas confirmadas.
2. Cria uma sessão vinculada a uma aula autorizada.
3. O backend copia para a sessão a latitude, longitude e raio da instituição.
4. O backend gera token aleatório com validade de 30 segundos.
5. O frontend monta o QR Code contendo a sessão e o token.
6. O professor pode consultar o token atual e encerrar a sessão.

### Aluno

1. Faz login e entra na turma pelo convite compartilhado pelo professor.
2. Mantém o painel aberto para receber avisos de chamadas pendentes, consultados a cada cinco segundos.
3. Lê o QR Code com a câmera do celular, abrindo a confirmação no navegador.
4. A página valida o QR em `POST /api/sessoes/{id}/preparar/`. O servidor exige matrícula e devolve um comprovante assinado, vinculado ao aluno e à sessão, com validade de dois minutos.
5. O navegador pede permissão de localização e envia automaticamente o comprovante e as coordenadas para `POST /api/presenca/registrar/`.
6. O backend exige sessão aberta, comprovante válido e GPS dentro do raio. A presença é única por aluno e sessão.
7. A confirmação aparece na tela e a chamada deixa de constar como pendente para aquele aluno.

Os avisos funcionam com o painel aberto. Não há push em segundo plano. Os tokens do QR são consultados apenas pelo professor; a API de avisos não os fornece.

### Cálculo de distância

`attendance/geolocation.py` aplica primeiro uma caixa delimitadora aproximada e só calcula a distância completa de Haversine quando necessário. A distância é calculada em metros usando o raio médio da Terra de 6.371.000 metros. Latitude, longitude e raio são validados antes do cálculo.

## 6. Remoção de biometria

As rotas, dependências e modelos WebAuthn foram removidos. A migration 0005 remove as tabelas antigas e o campo de verificação, preservando alunos, turmas, sessões e presenças. Faça backup antes de aplicar migrations a um banco existente.

## 7. Rotas principais

| Método | Rota | Finalidade |
|---|---|---|
| POST | `/api/register/` | Cadastrar usuário |
| GET | `/api/instituicoes/` | Listar instituições ativas |
| POST | `/api/instituicoes/{id}/geocodificar/` | Buscar candidatos de coordenada |
| POST | `/api/instituicoes/{id}/confirmar-localizacao/` | Confirmar coordenada oficial |
| POST | `/api/login/` | Obter tokens JWT |
| POST | `/api/token/refresh/` | Renovar access token |
| GET/POST | `/api/materias/` | Consultar/criar matérias |
| GET/POST | `/api/turmas/` | Consultar/criar turmas |
| GET/POST | `/api/aulas/` | Consultar/criar aulas |
| GET/POST | `/api/sessoes/` | Consultar/criar sessões |
| GET | `/api/sessoes/{id}/token/` | Consultar ou renovar QR Code |
| POST | `/api/sessoes/{id}/encerrar/` | Encerrar sessão |
| POST | `/api/presenca/registrar/` | Registrar presença |
| GET | `/api/aluno/turmas/` | Listar turmas do aluno |
| GET | `/api/aluno/minha-frequencia/` | Consultar frequência por turma |
| POST | `/api/aluno/entrar-turma/` | Entrar em turma por convite |

## 8. Segurança e integridade

- JWT é usado nas rotas protegidas.
- Professores e alunos possuem permissões separadas.
- Um professor só cria sessão para aula de sua própria matéria.
- Um aluno só registra presença pelo endpoint protegido para alunos.
- A matrícula possui unicidade por turma e aluno.
- A presença possui unicidade por sessão e aluno.
- Segredos e configurações de produção devem ser fornecidos por variáveis de ambiente.
- A AEMS é a instituição inicial de teste, com o endereço informado e raio inicial de 100 metros.
- A coordenada da AEMS precisa ser confirmada antes do teste prático, pois os serviços públicos consultados não retornaram um resultado inequívoco.

## 9. Testes

Na raiz do projeto, execute os testes JavaScript com `node --test frontend/regressions.test.cjs`. No diretório `backend`, execute `python -m pytest -q -p no:cacheprovider` e `python manage.py check`. Os apps possuem `__init__.py` para permitir a descoberta dos testes.

## 10. Limitações conhecidas

- O ambiente verificado usa Django 4.2 com Python 3.14 e apresentou erro de compatibilidade na renderização de páginas de erro. Antes da publicação, atualizar o Django para uma versão suportada e testar com a versão de Python escolhida.
- As páginas do frontend são servidas apenas com `DEBUG=True`. A publicação exige configurar páginas e arquivos estáticos para `DEBUG=False`, sem usar o servidor de desenvolvimento.

- Os testes JavaScript simulam o navegador. O fluxo completo ainda deve ser validado em celulares reais.
- SQLite é adequado para desenvolvimento e demonstração pequena em disco persistente. Para chamadas simultâneas em uso real, prefira PostgreSQL. Docker é opcional e não determina a escolha do banco.
- A tela de cadastro lista instituições, mas desabilita instituições sem coordenada confirmada.
- A documentação de API OpenAPI está disponível pelas rotas `/api/schema/` e `/api/schema/swagger-ui/` durante a execução do Django.

## 11. Critério de documentação para novas alterações

Toda alteração funcional deve atualizar, quando aplicável:

1. Docstring da função, classe ou módulo criado/alterado.
2. Este guia técnico, se houver mudança de fluxo, contrato, segurança ou arquitetura.
3. `docs/REGISTRO_ALTERACOES.md`, com data, arquivos, motivo e validação.
4. Teste automatizado ou registro explícito da razão pela qual o teste não é possível.
