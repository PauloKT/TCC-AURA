window.Aura = (() => {
  let refreshing = null;

  function login() {
    const next = window.location.pathname + window.location.search;
    window.location.href = '/login.html?next=' + encodeURIComponent(next);
  }

  async function refresh() {
    const token = localStorage.getItem('refresh_token');
    if (!token) return false;
    const response = await fetch('/api/token/refresh/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: token })
    });
    if (!response.ok) return false;
    const data = await response.json();
    localStorage.setItem('access_token', data.access);
    return true;
  }

  async function request(url, options = {}) {
    const send = () => fetch(url, {
      ...options,
      headers: { ...options.headers, Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    });
    let response = await send();
    if (response.status === 401) {
      if (!refreshing) refreshing = refresh().finally(() => { refreshing = null; });
      if (await refreshing) response = await send();
      if (response.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        login();
        throw new Error('Faça login para continuar.');
      }
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
