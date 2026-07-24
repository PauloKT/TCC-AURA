document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('register-form');
  const errorMessage = document.getElementById('error-message');
  const successMessage = document.getElementById('success-message');
  const roleSelect = document.getElementById('role');
  const matriculaGroup = document.getElementById('matricula-group');
  const cepGroup = document.getElementById('cep-group');

  // Toggle fields based on role selection
  roleSelect.addEventListener('change', function() {
    if (this.value === 'aluno') {
      matriculaGroup.style.display = 'block';
      cepGroup.style.display = 'none';
    } else {
      matriculaGroup.style.display = 'none';
      cepGroup.style.display = 'block';
    }
  });

  // Initialize based on default value
  if (roleSelect.value === 'aluno') {
    matriculaGroup.style.display = 'block';
    cepGroup.style.display = 'none';
  } else {
    matriculaGroup.style.display = 'none';
    cepGroup.style.display = 'block';
  }

  form.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Clear previous messages
    errorMessage.classList.remove('show');
    errorMessage.textContent = '';
    successMessage.classList.remove('show');
    successMessage.textContent = '';

    // Get form values
    const formData = new FormData(form);
    const username = formData.get('username').trim();
    const email = formData.get('email').trim();
    const password = formData.get('password');
    const password2 = formData.get('password2');
    const role = formData.get('role');
    const matricula = role === 'aluno' ? formData.get('matricula').trim() : undefined;
    const cep = role === 'professor' ? formData.get('cep').trim() : undefined;

    // Basic validation
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

    if (role === 'professor' && !cep) {
      showError('CEP é obrigatório para professores');
      return;
    }

    // Prepare data for API
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


    if (cep !== undefined) {
      data.cep = cep;
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
      // Redirect to login after 2 seconds
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
});