# AURA — Controle Automatizado de Chamada Universitária

> Sistema web para controle acadêmico de frequência com QR Code dinâmico, geolocalização GPS e validação de matrícula. Construído com Django e Django REST Framework.

---

## Sobre o Projeto

AURA é um sistema web desenvolvido como trabalho de conclusão de curso (TCC) para automatizar o controle de frequência em instituições de ensino superior. O sistema combina três camadas de segurança para prevenir fraudes e garantir que apenas alunos fisicamente presentes possam registrar sua frequência.

### Validação de presença
- **QR Code Dinâmico** — token único gerado por aula, com validade de 30 segundos
- **Geolocalização GPS** — valida a posição no raio configurado para a instituição (padrão de 100 metros)
- **Matrícula** — apenas alunos matriculados na turma podem registrar presença

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
├── frontend/                 # HTML, CSS e JavaScript do frontend
│   ├── aluno.html/js/css
│   ├── professor.html/js/css
│   ├── login.html/js/css
│   ├── register.html/js/css
│   └── confirmar-presenca.html/js/css
├── docs/                     # Guia técnico e registro de alterações
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

# Acesse o backend antes dos comandos Django
cd backend

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
Sistema gera QR Code dinâmico (token único, expira em 30s)
        ↓
Professor exibe QR Code no projetor
        ↓
Aluno escanea o QR Code
        ↓
GPS validado (dentro do raio institucional)
        ↓
Matrícula na turma confirmada
        ↓
Frequência registrada ✓
        ↓
Lista do professor atualizada em tempo real
```

---

## Privacidade e LGPD

O sistema armazena dados cadastrais, matrícula, presença e localização enviada no registro. Não utiliza biometria. O uso com alunos reais exige controle de acesso, HTTPS, backups e uma política de retenção e exclusão desses dados.

---

## Autores

Desenvolvido como trabalho de conclusão de curso (TCC).

- **Paulo Amaral** — [GitHub](https://github.com/PauloKT)
- **Heitor Cortes** — [GitHub](https://github.com/heitorpcrl)

---

## Licença

Este projeto é destinado exclusivamente para fins acadêmicos.

## Documentação técnica

Consulte [docs/GUIA_TECNICO.md](docs/GUIA_TECNICO.md) para a arquitetura, fluxos, endpoints, segurança, testes e limitações conhecidas. O histórico de mudanças relevantes fica em [docs/REGISTRO_ALTERACOES.md](docs/REGISTRO_ALTERACOES.md).

O roteiro para confirmar a AEMS e testar o sistema pelo celular está em [docs/TESTE_CELULAR.md](docs/TESTE_CELULAR.md).
