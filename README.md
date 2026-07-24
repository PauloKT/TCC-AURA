# AURA — Controle Automatizado de Chamada Universitária

> Sistema web para controle acadêmico de frequência utilizando QR Code dinâmico, geolocalização GPS e autenticação biométrica WebAuthn. Construído com Django e Django REST Framework.

---

## Sobre o Projeto

AURA é um sistema web desenvolvido como trabalho de conclusão de curso (TCC) para automatizar o controle de frequência em instituições de ensino superior. O sistema combina três camadas de segurança para prevenir fraudes e garantir que apenas alunos fisicamente presentes possam registrar sua frequência.

### Três Camadas de Segurança
- **QR Code Dinâmico** — token único gerado por aula, com validade de 60 segundos
- **Geolocalização GPS** — valida se o estudante está dentro de um raio de 50 metros da sala de aula
- **Autenticação Biométrica WebAuthn** — autenticação por impressão digital ou reconhecimento facial realizada localmente no dispositivo, nenhum dado biométrico é enviado ou armazenado no servidor

---

## Funcionalidades

### Para Professores
- Cadastrar e gerenciar disciplinas e turmas
- Definir percentual mínimo de frequência por disciplina
- Iniciar e encerrar sessões de aula
- Exibir QR Code dinâmico para escaneamento
- Visualizar lista de presença em tempo real
- Monitorar alertas de risco de frequência
- Acessar relatórios de frequência

### Para Alunos
- Auto-registro na plataforma
- Entrar em turmas via link de convite do professor
- Registrar presença escaneando o QR Code
- Acompanhar frequência pessoal e status por disciplina

---

## Pilha de Tecnologia

| Camada | Tecnologia |
|--------|------------|
| Linguagem | Python 3.11+ |
| Framework | Django + Django REST Framework |
| Banco de Dados | SQLite (desenvolvimento) |
| Frontend | HTML, CSS, JavaScript, Bootstrap 5 |
| Geração de QR Code | Biblioteca Python `qrcode` |
| Geolocalização | API do Navegador (browser-native) |
| Autenticação Biométrica | WebAuthn via `py_webauthn` |
| Controle de Versão | Git + GitHub |

---

## Estrutura do Projeto

```
TCC-AURA/
├── backend/                  # Backend Django
│   ├── accounts/             # Gestão de usuários (professor/aluno)
│   ├── attendance/           # Registro de frequência
│   ├── courses/              # Gestão de disciplinas/turmas
│   ├── db.sqlite3            # Banco de dados SQLite
│   └── manage.py             # Script de gerenciamento Django
├── frontend/                 # Assets do frontend
│   ├── assets/               # CSS, JS, imagens
│   ├── pages/                # Páginas HTML
│   │   ├── aluno/            # Interface do aluno
│   │   │   ├── frequencia.html
│   │   │   ├── frequenciaConfirmada.html
│   │   │   ├── home.html
│   │   │   ├── login.html
│   │   │   ├── registro.html
│   │   │   └── sair.html
│   │   └── professor/        # Interface do professor
│   │       ├── home.html
│   │       ├── lista.html
│   │       ├── login.html
│   │       ├── registro.html
│   │       └── sair.html
│   └── templates/            # Templates HTML
├── .venv/ & venv/            # Ambientes virtuais Python
├── .git/                     # Repositório Git
├── .claude/                  # Configuração do Claude Code
└── README.md                 # Documentação do projeto
```

---

## Como Começar

### Pré-requisitos
- Python 3.11+
- Git

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/aura.git
cd aura

# Crie e ative o ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Aplique as migrações
python manage.py migrate

# Crie superusuário (opcional)
python manage.py createsuperuser

# Inicie o servidor de desenvolvimento
python manage.py runserver
```

Acesse o sistema em: http://127.0.0.1:8000

---

## Fluxo de Frequência

```
Professor inicia sessão
        ↓
Sistema gera QR Code dinâmico (token único, expira em 60s)
        ↓
Professor exibe QR Code no projetor
        ↓
Aluno escanea o QR Code
        ↓
GPS validado (dentro de 50m da sala)
        ↓
Autenticação biométrica confirmada (WebAuthn — Face ID / impressão digital)
        ↓
Frequência registrada ✓
        ↓
Lista do professor atualizada em tempo real
```

---

## Privacidade e LGPD

O sistema foi projetado pensando na privacidade do aluno. O protocolo WebAuthn garante que dados biométricos (impressão digital, Face ID) **nunca deixem o dispositivo do usuário** e **não sejam transmitidos ou armazenados no servidor**. Apenas uma assinatura criptográfica é utilizada para confirmar identidade, em total conformidade com a Lei Geral de Proteção de Dados (LGPD) brasileira.

---

## Autores

Desenvolvido como trabalho de conclusão de curso (TCC).

- **Paulo Amaral** — [GitHub](https://github.com/PauloKT)
- **Heitor Cortes** — [GitHub](https://github.com/heitorpcrl)

---

## Licença

Este projeto é destinado exclusivamente para fins acadêmicos.