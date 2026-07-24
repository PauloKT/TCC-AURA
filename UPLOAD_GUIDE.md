# Guia de Upload de Sistemas para GitHub

Este guia explica como fazer upload de cada sistema do TCC-AURA para o GitHub.

## Processo Geral

Para cada sistema, siga estes passos:

```powershell
# 1. Criar uma branch para o sistema
git checkout -b feature/nome-do-sistema

# 2. Adicionar os arquivos específicos do sistema
git add caminho/dos/arquivos

# 3. Verificar o que foi adicionado
git status

# 4. Fazer commit
git commit -m "feat: implementar nome do sistema"

# 5. Fazer push
git push -u origin feature/nome-do-sistema

# 6. Criar Pull Request no GitHub (opcional, mas recomendado)
```

---

## Sistemas Específicos

### 1. Dashboard Aluno

**Branch:** `feature/dashboard-aluno`

**Arquivos:**
```powershell
git add backend/accounts/
git add frontend/aluno.*
git add frontend/src/pages/AlunoDashboard.jsx
```

**Commit:**
```powershell
git commit -m "feat: implementar dashboard do aluno"
```

**Push:**
```powershell
git push -u origin feature/dashboard-aluno
```

---

### 2. Dashboard Professor

**Branch:** `feature/dashboard-professor`

**Arquivos:**
```powershell
git add backend/courses/
git add frontend/professor.*
git add frontend/src/pages/ProfessorDashboard.jsx
```

**Commit:**
```powershell
git commit -m "feat: implementar dashboard do professor"
```

**Push:**
```powershell
git push -u origin feature/dashboard-professor
```

---

### 3. Autenticação

**Branch:** `feature/autenticacao`

**Arquivos:**
```powershell
git add backend/accounts/serializers.py
git add backend/accounts/views.py
git add backend/accounts/urls.py
git add frontend/login.*
git add frontend/src/pages/Login.jsx
```

**Commit:**
```powershell
git commit -m "feat: implementar sistema de autenticação"
```

**Push:**
```powershell
git push -u origin feature/autenticacao
```

---

### 4. Registro de Usuários

**Branch:** `feature/registro-usuarios`

**Arquivos:**
```powershell
git add backend/accounts/models.py
git add backend/accounts/serializers.py
git add backend/accounts/views.py
git add backend/accounts/migrations/
git add frontend/register.*
git add frontend/src/pages/Register.jsx
```

**Commit:**
```powershell
git commit -m "feat: implementar sistema de registro"
```

**Push:**
```powershell
git push -u origin feature/registro-usuarios
```

---

### 5. Relatórios

**Branch:** `feature/relatorios`

**Arquivos:**
```powershell
git add backend/attendance/
git add frontend/src/pages/
```

**Commit:**
```powershell
git commit -m "feat: implementar sistema de relatórios"
```

**Push:**
```powershell
git push -u origin feature/relatorios
```

---

### 6. API Backend

**Branch:** `feature/api-backend`

**Arquivos:**
```powershell
git add backend/backend/settings.py
git add backend/backend/urls.py
git add backend/backend/wsgi.py
```

**Commit:**
```powershell
git commit -m "feat: configurar API backend"
```

**Push:**
```powershell
git push -u origin feature/api-backend
```

---

### 7. Frontend Geral

**Branch:** `feature/frontend-configuracao`

**Arquivos:**
```powershell
git add frontend/src/
git add frontend/src/services/api.js
```

**Commit:**
```powershell
git commit -m "feat: configurar frontend"
```

**Push:**
```powershell
git push -u origin feature/frontend-configuracao
```

---

## Criando Pull Requests no GitHub

Após fazer push de cada branch, siga estes passos:

1. Acesse [https://github.com/PauloKT/TCC-AURA](https://github.com/PauloKT/TCC-AURA)
2. Clique em **"Pull Requests"**
3. Clique em **"New Pull Request"**
4. Selecione:
   - **Base:** `main`
   - **Compare:** `feature/nome-do-sistema`
5. Clique em **"Create Pull Request"**
6. Adicione uma descrição detalhada
7. Clique em **"Create Pull Request"**

---

## Resumo Rápido

| Sistema | Branch | Comando |
|---------|--------|---------|
| Dashboard Aluno | `feature/dashboard-aluno` | `git checkout -b feature/dashboard-aluno` |
| Dashboard Professor | `feature/dashboard-professor` | `git checkout -b feature/dashboard-professor` |
| Autenticação | `feature/autenticacao` | `git checkout -b feature/autenticacao` |
| Registro | `feature/registro-usuarios` | `git checkout -b feature/registro-usuarios` |
| Relatórios | `feature/relatorios` | `git checkout -b feature/relatorios` |
| API Backend | `feature/api-backend` | `git checkout -b feature/api-backend` |
| Frontend | `feature/frontend-configuracao` | `git checkout -b feature/frontend-configuracao` |

---

## Dicas Importantes

✅ **Sempre verifique** o status antes de fazer commit:
```powershell
git status
```

✅ **Use mensagens de commit descritivas:**
```powershell
git commit -m "feat: descrição clara do que foi feito"
```

✅ **Uma branch por feature:** Não misture sistemas em uma mesma branch

✅ **Faça commits atômicos:** Cada commit deve representar uma mudança lógica completa

✅ **Antes de fazer push, sincronize com main:**
```powershell
git fetch origin
git rebase origin/main
```

---

## Dúvidas?

Se tiver dúvidas, execute:
```powershell
git --help
```

Ou entre em contato! 🚀
