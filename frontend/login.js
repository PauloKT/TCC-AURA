document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('login-form');
  const errorDiv = document.getElementById('error-message');

  form.addEventListener('submit', async function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    errorDiv.textContent = '';
    errorDiv.classList.remove('show');
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
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      const requested = new URLSearchParams(window.location.search).get('next');
      if (requested) {
        const destination = new URL(requested, window.location.origin);
        if (destination.origin === window.location.origin &&
            ['/aluno.html', '/confirmar-presenca.html'].includes(destination.pathname) &&
            data.user?.role === 'aluno') {
          window.location.href = destination.pathname + destination.search;
          return;
        }
      }
      try {
        const base64Url = access.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const payload = JSON.parse(atob(base64));
        if (payload.role === 'professor') {
          window.location.href = 'professor.html';
        } else {
          window.location.href = 'aluno.html';
        }
      } catch (e) {
        window.location.href = 'aluno.html';
      }

    } catch (error) {
      errorDiv.textContent = error.message || 'Erro ao fazer login';
      errorDiv.classList.add('show');
    }
  });
});
