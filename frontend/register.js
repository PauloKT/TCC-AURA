document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('register-form');
  const errorMessage = document.getElementById('error-message');
  const successMessage = document.getElementById('success-message');
  const roleSelect = document.getElementById('role');
  const matriculaGroup = document.getElementById('matricula-group');
  const institutionGroup = document.getElementById('institution-group');
  const institutionSelect = document.getElementById('instituicao');

  loadInstitutions();
  roleSelect.addEventListener('change', function() {
    if (this.value === 'aluno') {
      matriculaGroup.style.display = 'block';
      institutionGroup.style.display = 'none';
    } else {
      matriculaGroup.style.display = 'none';
      institutionGroup.style.display = 'block';
    }
  });
  if (roleSelect.value === 'aluno') {
    matriculaGroup.style.display = 'block';
    institutionGroup.style.display = 'none';
  } else {
    matriculaGroup.style.display = 'none';
    institutionGroup.style.display = 'block';
  }

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    errorMessage.classList.remove('show');
    errorMessage.textContent = '';
    successMessage.classList.remove('show');
    successMessage.textContent = '';
    const formData = new FormData(form);
    const username = formData.get('username').trim();
    const email = formData.get('email').trim();
    const password = formData.get('password');
    const password2 = formData.get('password2');
    const role = formData.get('role');
    const matricula = role === 'aluno' ? formData.get('matricula').trim() : undefined;
    const instituicoes = role === 'professor'
      ? Array.from(institutionSelect.selectedOptions)
        .map(option => Number(option.value))
        .filter(Boolean)
      : undefined;
    if (!username) {
      showError('Usuário é obrigatório');
      return;
    }

    if (!email) {
      showError('E-mail é obrigatório');
      return;
    }

    if (!password) {
      showError('Senha é obrigatória');
      return;
    }

    if (password !== password2) {
      showError('Senhas não coincidem');
      return;
    }

    if (role === 'aluno' && !matricula) {
      showError('Matrícula é obrigatória para alunos');
      return;
    }

    if (role === 'professor' && !instituicoes.length) {
      showError('Selecione ao menos uma instituição');
      return;
    }
    const data = {
      username: username,
      email: email,
      password: password,
      password2: password2,
      role: role
    };

    if (matricula !== undefined) {
      data.matricula = matricula;
    }


    if (instituicoes !== undefined) {
      data.instituicoes = instituicoes;
    }

    try {
      const response = await fetch('/api/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const firstError =
          errorData.detail ||
          errorData.erro ||
          Object.values(errorData).flat().find(Boolean) ||
          'Erro ao cadastrar';
        throw new Error(firstError);
      }

      showSuccess('Cadastro realizado com sucesso! Faça login.');
      setTimeout(() => {
        window.location.href = 'login.html';
      }, 2000);
    } catch (error) {
      showError(error.message);
    }
  });

  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
  }

  function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.classList.add('show');
  }

  async function loadInstitutions() {
    try {
      const response = await fetch('/api/instituicoes/');
      if (!response.ok) throw new Error('Não foi possível carregar as instituições.');
      const data = await response.json();
      institutionSelect.innerHTML = '<option value="" disabled>Selecione uma instituição</option>';
      data.forEach(institution => {
        const option = document.createElement('option');
        option.value = institution.id;
        option.textContent = `${institution.nome} - ${institution.cidade}/${institution.estado}`;
        option.disabled = institution.latitude === null || institution.longitude === null;
        if (option.disabled) option.textContent += ' (localização pendente)';
        institutionSelect.appendChild(option);
      });
    } catch (error) {
      institutionSelect.innerHTML = '<option value="">Erro ao carregar instituições</option>';
      showError(error.message);
    }
  }
});