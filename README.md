# AURA — Controle Automatizado de Chamada Universitária

Sistema acadêmico desenvolvido como TCC, com Django, QR Code rotativo, localização do navegador e validação de matrícula. Revisão: **17/09/2026**.

## O que funciona

- Professor: matérias, turmas, aulas, código de entrada na turma, chamada, lista de resultados, frequência e exportação CSV.
- Aluno: cadastro, entrada por código de 8 caracteres, turmas, frequência e confirmação pelo QR Code.
- QR válido gera um comprovante de leitura por 120 segundos, permitindo concluir o GPS após a rotação do token de 30 segundos.
- Dentro do raio: presença. Fora do raio: **falta registrada**. O primeiro resultado por aluno e sessão é mantido.
- Resultados e chamadas disponíveis são consultados periodicamente enquanto a página está aberta; não são notificações push.

GPS informado pelo navegador pode ser impreciso ou manipulado. O sistema aplica validações, mas **não garante presença física nem elimina fraude**. Não há biometria nem verificação de Wi-Fi/IP institucional.

## Tecnologias e estrutura

Python 3.11+ e Django 5.2 LTS; Django REST Framework e JWT; SQLite local ou PostgreSQL; templates Django, CSS e JavaScript sem framework ou build. WhiteNoise serve os arquivos estáticos em produção. A imagem do QR ainda depende de `api.qrserver.com`.

```text
backend/
  accounts/       usuários, autenticação e frequência
  courses/        instituições, matérias, turmas e aulas
  attendance/     sessões, presença e geolocalização
  backend/        configurações, rotas e APIs dos painéis
  templates/      bases e componentes compartilhados
  manage.py
frontend/         páginas, app.css, marca e scripts
docs/             documentação, auditoria e roteiro de testes
```

## Executar localmente (PowerShell)

Na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py prepare_local
python manage.py runserver 127.0.0.1:8000
```

Se já existe `.env`, preserve-o e confira as novas opções de `.env.example`. `prepare_local` faz backup do SQLite existente e aplica migrations. Em outra máquina, crie um ambiente virtual novo; não copie a pasta `.venv`. Para administrar instituições, execute `python manage.py createsuperuser` e abra `/admin/`.

Acesse [o servidor local](http://127.0.0.1:8000). Para câmera/GPS no celular, siga [TESTE_CELULAR.md](docs/TESTE_CELULAR.md). Produção usa Gunicorn e HTTPS, conforme [HOSPEDAGEM.md](docs/HOSPEDAGEM.md).

## Verificar

No diretório `backend`:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest -q -p no:cacheprovider
```

Na raiz, com Node instalado:

```powershell
node --test frontend/regressions.test.cjs
```

Node é necessário apenas para executar os testes dos scripts JavaScript. O sistema em produção não precisa dele. Os testes simulados não substituem câmera, GPS e navegação em celulares reais.

O pytest utiliza `backend.test_settings` e um SQLite separado, `backend/test-aura.sqlite3`, para testar transações com conexões simultâneas. Não usa o banco de alunos do projeto. A suíte inclui disputas entre presença/encerramento, renovação de QR e início de chamadas. Esses cenários devem ser repetidos em PostgreSQL antes da homologação da hospedagem.

## Estado da entrega

O projeto está em fase de validação final do MVP. **Ainda não está homologado para uso institucional.** Consulte [REVISAO_FINAL.md](docs/REVISAO_FINAL.md) para os problemas priorizados, alterações feitas e critérios para encerrar o TCC.

## Documentação

- [Guia de estudo para a apresentação](docs/GUIA_ESTUDO_APRESENTACAO.md): funcionamento, decisões técnicas, exemplos e perguntas da banca.
- [Guia técnico](docs/GUIA_TECNICO.md): arquitetura, contratos e regras atuais.
- [Interface](docs/INTERFACE.md): componentes e roteiro visual.
- [Teste pelo celular](docs/TESTE_CELULAR.md): HTTPS, turma, câmera e GPS.
- [Hospedagem](docs/HOSPEDAGEM.md): recomendação e configuração.
- [Revisão final](docs/REVISAO_FINAL.md): melhorias e pendências.
- [Histórico](docs/REGISTRO_ALTERACOES.md): entradas antigas descrevem versões anteriores.

## Dados e autoria

O sistema armazena cadastro, matrícula, presença e coordenadas recebidas. Antes de usar dados reais, definir responsáveis pelo acesso, retenção, exclusão e recuperação por backup.

Desenvolvido como TCC por **Paulo Amaral** ([GitHub](https://github.com/PauloKT)) e **Heitor Cortes** ([GitHub](https://github.com/heitorpcrl)). Projeto destinado a fins acadêmicos.
