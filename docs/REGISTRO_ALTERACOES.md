# Registro de Alterações Técnicas

Este arquivo registra mudanças relevantes do AURA para acompanhamento do desenvolvimento e uso no TCC.

## 2026-09-08 - Teste geral e documentação técnica

### Objetivo

Validar o estado geral do código e criar uma referência única para arquitetura, fluxos, endpoints, segurança, testes e limitações conhecidas.

### Verificação executada

- `python manage.py check`: aprovado, sem problemas.
- `python -m pytest --import-mode=importlib -q`: 29 testes aprovados.

### Documentação criada

- `docs/GUIA_TECNICO.md`: documentação funcional e estrutural do projeto.
- `docs/REGISTRO_ALTERACOES.md`: histórico das mudanças relevantes.
- `.github/agents/aura-functional-reviewer.agent.md`: regra para documentar futuras alterações.

### Pendência registrada

Na versão anterior, o backend possuía o fluxo WebAuthn, mas o frontend HTML/JavaScript não enviava `webauthn_token` ao registrar a presença. Essa dependência foi removida do fluxo ativo no registro de 2026-09-08 abaixo.

## 2026-09-08 - Remoção da biometria do fluxo ativo

### Objetivo

Deixar o registro de presença funcional sem depender de WebAuthn.

### Comportamento

- O login continua usando usuário, senha e JWT.
- A presença válida depende de QR Code ativo, matrícula e geolocalização dentro do raio.
- Os campos e endpoints WebAuthn permanecem no backend apenas para compatibilidade com dados e código legado, mas não bloqueiam novas presenças.

## 2026-09-08 - Instituições e endereço completo

### Objetivo

Substituir o CEP como referência principal de geolocalização por uma instituição cadastrada com endereço completo e localização confirmada.

### Alterações

- Criado o modelo `courses.Instituicao`, com endereço completo, raio, coordenadas, fonte e data de confirmação.
- Criado vínculo opcional `accounts.CustomUser.instituicao` para preservar usuários legados.
- Criada a instituição AEMS por migration com o endereço informado e raio inicial de 100 metros.
- O cadastro de professor passou a exigir instituição ativa em vez de exigir CEP.
- Criada API pública de instituições ativas.
- Criadas ações administrativas para buscar candidatos de geocodificação e confirmar latitude/longitude.
- Sessões novas usam a localização confirmada da instituição; dados legados continuam funcionando temporariamente.
- Criada integração inicial com Photon para busca de candidatos, sem aceitar o primeiro resultado automaticamente.
- Criado `docs/TESTE_CELULAR.md` com o procedimento de confirmação da AEMS, acesso pela rede local, uso de HTTPS e casos de teste prático.

### Pendência para o teste prático

A AEMS foi cadastrada sem coordenadas até que a localização seja conferida. Uma coordenada retornada por serviço público que corresponda a outro local não deve ser usada para liberar o geofence.

## 2026-09-08 - Estruturação da geolocalização

### Objetivo

Centralizar a regra de geofence no backend e impedir falsos sucessos no registro de presença.

### Alterações

- Criado `backend/attendance/geolocation.py` com validação de coordenadas, validação de raio, distância de Haversine e pré-filtro por caixa delimitadora.
- `SessaoChamadaViewSet` passou a permitir que alunos matriculados consultem os dados da sessão.
- Professores sem coordenadas válidas não podem iniciar uma sessão.
- O serializer rejeita coordenadas inválidas e posições fora do raio com HTTP 400, sem persistir uma presença inválida.
- O frontend deixou de decidir a distância; a API passou a ser a autoridade do geofence.
- Criada a migration `backend/attendance/migrations/0004_alter_presenca_latitude_alter_presenca_longitude_and_more.py` para registrar os validators de latitude, longitude e raio.

### Testes adicionados

- Aluno matriculado e não matriculado consultando o token da sessão.
- Ponto no limite do raio.
- Coordenada inválida.
- Tentativa fora do raio sem persistência e nova tentativa válida.

### Correção de migration

Durante a verificação `makemigrations --check --dry-run`, foi identificado que o índice `criado_em` de `WebAuthnChallenge` existia no model, mas não tinha migration correspondente. A migration `backend/attendance/migrations/0003_webauthnchallenge_attendance__criado__b7db6a_idx.py` foi criada para corrigir essa divergência.

## Modelo para próximos registros

### AAAA-MM-DD - Título da alteração

- **Objetivo:** por que a mudança foi feita.
- **Arquivos:** arquivos criados ou alterados.
- **Comportamento:** o que mudou no sistema.
- **Documentação:** docstrings, guia técnico ou README atualizados.
- **Testes:** comandos executados e resultado.
- **Pendências:** limitações ou próximos passos.
