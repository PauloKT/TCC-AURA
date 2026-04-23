# AURA — Automated University Roll-call and Attendance

> Sistema web para controle de presença acadêmica utilizando QR Code dinâmico, geolocalização GPS e autenticação biométrica via WebAuthn. Desenvolvido com Django e Django REST Framework.

---

## Sobre o projeto

O AURA é um sistema web acadêmico desenvolvido como Trabalho de Conclusão de Curso (TCC) para automatizar o controle de presença em instituições de ensino superior. O sistema combina três camadas de segurança para prevenir fraudes e garantir que somente alunos fisicamente presentes possam registrar presença.

**Camadas de segurança:**
- **QR Code dinâmico** — token único gerado por aula, expira em 60 segundos
- **Geolocalização GPS** — valida que o aluno está dentro de um raio de 50 metros da sala
- **WebAuthn** — autenticação biométrica (Face ID / impressão digital) realizada localmente no dispositivo, nenhum dado biométrico é enviado ou armazenado no servidor

---

## Funcionalidades

### Professor
- Cadastrar e gerenciar matérias e turmas
- Definir percentual mínimo de presença por matéria
- Iniciar e encerrar chamadas
- Exibir QR Code dinâmico para os alunos escanear
- Visualizar lista de presença em tempo real
- Acompanhar alertas de risco de reprovação por falta
- Acessar relatórios de frequência

### Aluno
- Realizar cadastro no sistema
- Entrar em turmas via link gerado pelo professor
- Registrar presença escaneando o QR Code
- Acompanhar frequência e status por matéria

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Framework | Django + Django REST Framework |
| Banco de dados | SQLite (desenvolvimento) |
| Frontend | HTML, CSS, JavaScript, Bootstrap 5 |
| Geração de QR Code | biblioteca `qrcode` (Python) |
| Geolocalização | Geolocation API (nativa do navegador) |
| Autenticação biométrica | WebAuthn via `pywebauthn` |
| Versionamento | Git + GitHub |

---

## Estrutura do projeto

```
aura/
├── core/               # Configurações do projeto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/              # Gerenciamento de usuários (professor e aluno)
├── subjects/           # Matérias e turmas
├── attendance/         # Sessões e registros de presença
├── qrcodes/            # Geração e validação do QR Code
├── reports/            # Relatórios de frequência e alertas
├── manage.py
└── requirements.txt
```

---

## Como executar

### Pré-requisitos

- Python 3.11+
- Git

### Instalação

```bash
# Clonar o repositório
git clone https://github.com/PauloKT/aura.git
cd aura

# Criar e ativar o ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Instalar as dependências
pip install -r requirements.txt

# Aplicar as migrações
python manage.py migrate

# Criar superusuário (opcional)
python manage.py createsuperuser

# Iniciar o servidor de desenvolvimento
python manage.py runserver
```

Acesse o sistema em `http://127.0.0.1:8000`

---

## Dependências (para rodar localmente)

> Se você ainda não tiver um `requirements.txt` completo, use a instalação rápida abaixo para instalar tudo de uma vez.

### Instalação rápida (tudo de uma vez)

```bash
python -m pip install django djangorestframework "qrcode[pil]" pillow py-webauthn python-dotenv psycopg2-binary djangorestframework-simplejwt django-cors-headers
```

### O que cada pacote faz no projeto

- **django** — framework principal (models, templates, admin, autenticação, etc.)
- **djangorestframework** — API REST para o frontend consumir
- **qrcode[pil]** — geração do QR Code; o extra **[pil]** inclui suporte de renderização via Pillow
- **pillow** — manipulação/renderização de imagens (necessário junto do QR code)
- **py-webauthn** — fluxo WebAuthn (chaves públicas) para autenticação biométrica no dispositivo
- **python-dotenv** — carrega variáveis do `.env` (segredos fora do código)
- **psycopg2-binary** — driver do PostgreSQL (caso migre do SQLite no futuro)
- **djangorestframework-simplejwt** — autenticação por tokens JWT na API
- **django-cors-headers** — habilita CORS para o frontend acessar a API

### Salvar as dependências no `requirements.txt`

```bash
python -m pip freeze > requirements.txt
```

---

## Fluxo de registro de presença

```
Professor inicia a chamada
        |
Sistema gera QR Code dinâmico (token único, expira em 60s)
        |
Professor exibe o QR Code no projetor
        |
Aluno escaneia o QR Code
        |
GPS validado (raio de 50m da sala)
        |
Biometria confirmada (WebAuthn — Face ID / impressão digital)
        |
Presença registrada
        |
Lista do professor atualizada em tempo real
```

---

## Privacidade e LGPD

O AURA foi desenvolvido com atenção à privacidade dos dados dos alunos. O protocolo WebAuthn garante que os dados biométricos (impressão digital, Face ID) nunca saiam do dispositivo do aluno e nunca sejam transmitidos ou armazenados no servidor. Apenas uma assinatura criptográfica é utilizada para confirmar a identidade, em conformidade com a Lei Geral de Proteção de Dados (LGPD).

---

## Autores

Desenvolvido como Trabalho de Conclusão de Curso (TCC).

- **Paulo Amaral** — [GitHub](https://github.com/PauloKT)
- **Heitor Cortes** — [GitHub](https://github.com/heitorpcrl)

---

## Licença

Este projeto foi desenvolvido para fins acadêmicos.