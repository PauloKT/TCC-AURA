window.Aura = (() => {
  // Limpa credenciais legadas; a sessão atual usa cookie HttpOnly do Django.
  try {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  } catch { /* O navegador pode bloquear o armazenamento local. */ }

  function login() {
    const next = window.location.pathname + window.location.search;
    window.location.href = '/login.html?next=' + encodeURIComponent(next);
  }

  function csrfToken() {
    const cookie = document.cookie.split(';').map(value => value.trim()).find(value => value.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length))
      : document.querySelector('meta[name="csrf-token"]')?.content;
  }

  async function request(url, options = {}) {
    const destination = new URL(url, window.location.origin);
    if (destination.origin !== window.location.origin) throw new Error('A API deve usar o mesmo endereço do sistema.');
    const headers = { ...options.headers };
    if (!['GET', 'HEAD', 'OPTIONS'].includes((options.method || 'GET').toUpperCase())) {
      headers['X-CSRFToken'] = csrfToken() || '';
    }
    const response = await fetch(url, {
      ...options,
      credentials: 'same-origin', headers,
    });
    if (response.status === 401) {
      login();
      throw new Error('Sua sessão expirou. Faça login para continuar.');
    }
    return response;
  }

  async function json(url, options = {}) {
    const response = await request(url, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const labels = { nome: 'Nome', codigo: 'Código', carga_horaria: 'Carga horária', frequencia_minima: 'Frequência mínima', materia: 'Matéria', turma: 'Turma', hora_inicio: 'Início', hora_fim: 'Fim', data: 'Data', titulo: 'Título' };
      const message = data.detail || Object.entries(data).map(([field, errors]) => `${labels[field] || field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`).join('\n');
      throw new Error(message || 'Não foi possível concluir. Tente novamente.');
    }
    return data;
  }

  return { request, json, login };
})();
