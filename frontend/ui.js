window.UI = (() => {
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  function notify(message, kind = 'info') {
    const region = document.getElementById('toast-region');
    if (!region) return;
    const toast = document.createElement('div');
    toast.className = 'toast'; toast.dataset.kind = kind; toast.textContent = message;
    region.appendChild(toast); setTimeout(() => toast.remove(), 6500);
  }
  const date = value => value ? new Date(value.length === 10 ? value + 'T12:00:00' : value).toLocaleDateString('pt-BR') : '—';
  const percent = value => value == null ? 'Sem dados' : Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + '%';
  function badge(situation) {
    const options = { aprovado: ['good', 'Regular'], reprovado: ['warning', 'Atenção'], sem_dados: ['', 'Sem chamadas'], presente: ['good','Presente'], falta: ['bad','Falta'] };
    const [style, label] = options[situation] || ['', situation];
    return `<span class="badge ${style}">${escape(label)}</span>`;
  }
  const empty = (title, description = '', action = '') => `<div class="empty-state"><span class="empty-symbol" aria-hidden="true">▦</span><h3>${escape(title)}</h3><p>${escape(description)}</p>${action}</div>`;
  function setMenu(open, restoreFocus = false) {
    const menu = document.getElementById('navigation-menu');
    const toggle = document.getElementById('menu-toggle');
    if (!menu || !toggle) return;
    menu.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Fechar menu de navegação' : 'Abrir menu de navegação');
    if (restoreFocus) toggle.focus();
  }
  function route() {
    const name = location.hash.slice(1).split('/')[0] || 'inicio';
    const panels = [...document.querySelectorAll('[data-panel]')];
    if (!panels.length) return;
    const actual = panels.some(panel => panel.dataset.panel === name) ? name : 'inicio';
    for (const panel of panels) panel.hidden = panel.dataset.panel !== actual;
    for (const link of document.querySelectorAll('[data-nav]')) {
      if (link.dataset.nav === actual || (actual === 'detalhe' && link.dataset.nav === 'turmas')) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    setMenu(false);
  }
  document.addEventListener('DOMContentLoaded', async () => {
    route(); window.addEventListener('hashchange', route);
    document.getElementById('menu-toggle')?.addEventListener('click', event => {
      setMenu(event.currentTarget.getAttribute('aria-expanded') !== 'true');
    });
    document.getElementById('menu-toggle')?.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown') {
        event.preventDefault(); setMenu(true);
        document.querySelector('#navigation-menu nav a')?.focus();
      }
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && document.getElementById('menu-toggle')?.getAttribute('aria-expanded') === 'true') setMenu(false, true);
    });
    document.addEventListener('focusin', event => {
      if (!event.target.closest('#navigation-menu, #menu-toggle')) setMenu(false);
    });
    document.addEventListener('click', event => {
      if (event.target.closest('#navigation-menu a')) setMenu(false, true);
      else if (!event.target.closest('#navigation-menu, #menu-toggle')) setMenu(false);
      if (event.target.closest('[data-close]')) event.target.closest('dialog')?.close();
    });
    document.getElementById('logout-btn')?.addEventListener('click', async () => {
      try {
        await Aura.json('/api/auth/logout/', { method: 'POST' });
        location.href = '/login.html';
      } catch (error) { notify(error.message, 'error'); }
    });
    const today = document.getElementById('today-label');
    if (today) today.textContent = new Date().toLocaleDateString('pt-BR', { day:'numeric', month:'long', year:'numeric' });
    if (!document.body.dataset.role) return;
    try {
      const profile = await Aura.json('/api/interface/perfil/');
      if (profile.role !== document.body.dataset.role) { location.href = profile.role === 'professor' ? '/professor.html' : '/aluno.html'; return; }
      document.getElementById('user-name').textContent = profile.nome;
      document.getElementById('user-avatar').textContent = profile.nome.slice(0, 2).toUpperCase();
      const details = document.getElementById('profile-details');
      if (details) details.innerHTML = Object.entries({ Nome: profile.nome, Usuário: profile.username, 'E-mail': profile.email, Perfil: profile.role === 'professor' ? 'Professor' : 'Aluno', ...(profile.role === 'aluno' ? {'Matrícula': profile.matricula} : {'Instituições': profile.instituicoes.join(', ')}) }).map(([key,value]) => `<dt>${escape(key)}</dt><dd>${escape(value || 'Não informado')}</dd>`).join('');
    } catch (error) {
      notify(error.message, 'error');
      const details = document.getElementById('profile-details');
      if (details) details.innerHTML = '<dt>Não foi possível carregar</dt><dd>Confira a conexão e atualize esta página.</dd>';
    }
  });
  return { escape, notify, date, percent, badge, empty };
})();
