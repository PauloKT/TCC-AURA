# AURA — Controle Automatizado de Chamada Universitária

Sistema acadêmico desenvolvido como TCC, com Django, QR Code rotativo, localização do navegador e validação de matrícula. Revisão: **01/10/2026**.

## O que funciona

- Professor: matérias, turmas, aulas, código de entrada na turma, chamada, lista de resultados, frequência e exportação CSV.
- Aluno: cadastro, entrada por código de 8 caracteres, turmas, frequência e confirmação pelo QR Code.
- QR válido gera um comprovante de leitura por 120 segundos, permitindo concluir o GPS após a rotação do token de 30 segundos.
- Dentro do raio: presença. Fora do raio: tentativa rejeitada, sem gravação, com possibilidade de tentar novamente na mesma chamada. Presenças confirmadas não são duplicadas ou sobrescritas.
- Frequência calculada somente com chamadas encerradas, tanto no total quanto nas presenças. O raio padrão é **100 m**, ajustável na instituição; cada chamada copia o raio vigente ao ser aberta.
- Cadastro aceita e-mails pessoais e institucionais válidos. O catálogo público de instituições não expõe endereço detalhado ou coordenadas.
- Login no navegador usa sessão Django com cookie `HttpOnly` e proteção CSRF. Sair encerra a sessão no servidor; JWT continua disponível para clientes da API.
- Resultados e chamadas disponíveis são consultados periodicamente enquanto a página está aberta; não são notificações push.

GPS informado pelo navegador pode ser impreciso ou manipulado. O sistema aplica validações, mas **não garante presença física nem elimina fraude**. Não há biometria nem verificação de Wi-Fi/IP institucional.

## Tecnologias e estrutura

Python 3.11+ e Django 5.2 LTS; Django REST Framework e JWT; SQLite local; templates Django, CSS e JavaScript sem framework ou build. O Cloudflare Tunnel pode expor temporariamente o servidor local em HTTPS para testes no celular. O Django gera o QR como SVG com `qrcode`, sem enviar tokens a terceiros.

```text
backend/
  accounts/       usuários, autenticação e frequência
  courses/        instituições, matérias, turmas e aulas
  attendance/     sessões, presença e geolocalização
  backend/        configurações, rotas e APIs dos painéis
  templates/      bases e componentes compartilhados
  manage.py
frontend/         páginas, app.css, marca e scripts
docs/             guia técnico e roteiro de testes
```

## Executar localmente (PowerShell)

Na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe backend/manage.py prepare_local
.\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

Se já existe `.env`, preserve-o e confira as novas opções de `.env.example`. `prepare_local` faz backup do SQLite existente e aplica migrations. Em outra máquina, crie um ambiente virtual novo; não copie a pasta `.venv`. Para administrar instituições, execute `python manage.py createsuperuser` e abra `/admin/`.

Acesse [o servidor local](http://127.0.0.1:8000). Para câmera/GPS no celular, siga [TESTE_CELULAR.md](docs/TESTE_CELULAR.md).

## Conferir a configuração

Na raiz, use explicitamente o Python do projeto para evitar executar outro ambiente:

```powershell
.\.venv\Scripts\python.exe -m django --version
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe backend/manage.py check
.\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe backend/manage.py test accounts.test_medium_issues attendance.test_confirmation
```

Na raiz, `node --test frontend/attendance-flow.test.cjs frontend/browser-auth.test.cjs` verifica confirmação, renovação do QR e autenticação do navegador. Os requisitos limitam Django à série 5.2; WebAuthn não é dependência do projeto.

Depois desta atualização, faça login novamente. Para o túnel HTTPS, configure `CSRF_TRUSTED_ORIGINS`, `SESSION_COOKIE_SECURE=True` e `CSRF_COOKIE_SECURE=True` conforme [TESTE_CELULAR.md](docs/TESTE_CELULAR.md).

Antes da apresentação, siga o roteiro manual de câmera, GPS, QR Code e chamada em [TESTE_CELULAR.md](docs/TESTE_CELULAR.md).

## Estado da entrega

O projeto está em fase de validação final do MVP. **Ainda não está homologado para uso institucional.**

## Documentação

- [Guia técnico](docs/GUIA_TECNICO.md): arquitetura, contratos e regras atuais.
- [Teste pelo celular](docs/TESTE_CELULAR.md): HTTPS, turma, câmera e GPS.

## Dados e autoria

O sistema armazena cadastro, matrícula, presença e coordenadas recebidas. Antes de usar dados reais, definir responsáveis pelo acesso, retenção, exclusão e recuperação por backup.

Desenvolvido como TCC por **Paulo Amaral** ([GitHub](https://github.com/PauloKT)) e **Heitor Cortes** ([GitHub](https://github.com/heitorpcrl)). Projeto destinado a fins acadêmicos.
