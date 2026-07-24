document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('login-form');
  const errorDiv = document.getElementById('error-message');

  form.addEventListener('submit', async function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    // Clear previous errors
    errorDiv.textContent = '';
    errorDiv.classList.remove('show');

    // Basic validation
    if (!username || !password) {
      errorDiv.textContent = 'Por favor, preencha todos os campos';
      errorDiv.classList.add('show');
      return;
    }

    try {
      const response = await fetch('/api/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          password: password
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Credenciais inválidas');
      }

      const data = await response.json();
      const { access, refresh } = data;

      // Store tokens
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      // Decode token to get role (simple base64)
      try {
        const payload = JSON.parse(atob(access.split('.')[1]));
        if (payload.role === 'professor') {
          window.location.href = 'professor.html';
        } else {
          window.location.href = 'aluno.html';
        }
      } catch (e) {
        // Fallback if token parsing fails
        window.location.href = 'aluno.html';
      }

    } catch (error) {
      errorDiv.textContent = error.message || 'Erro ao fazer login';
      errorDiv.classList.add('show');
    }
  });
});