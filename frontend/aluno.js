document.addEventListener('DOMContentLoaded', function() {
  const loading = document.getElementById('loading');
  const content = document.getElementById('content');
  const list = document.getElementById('turmas-list');
  const calls = document.getElementById('calls-list');
  const callsStatus = document.getElementById('calls-status');
  const joinForm = document.getElementById('join-form');
  const inviteInput = document.getElementById('invite-code');
  const joinMessage = document.getElementById('join-message');
  let polling = null;
  let busy = false;
  let stopped = false;
  let previousCalls = '';

  if (!localStorage.getItem('access_token') && !localStorage.getItem('refresh_token')) {
    Aura.login();
    return;
  }
  inviteInput.value = new URLSearchParams(window.location.search).get('convite') || '';

  async function loadGroups() {
    const { turmas } = await Aura.json('/api/aluno/turmas/');
    list.replaceChildren();
    if (!turmas.length) list.textContent = 'Você não está matriculado em nenhuma turma.';
    for (const turma of turmas) {
      const card = document.createElement('div');
      card.className = 'turma-card';
      const title = document.createElement('h3');
      title.textContent = turma.nome;
      const subject = document.createElement('p');
      subject.textContent = `${turma.materia.nome} — ${turma.semestre}/${turma.ano}`;
      const frequency = document.createElement('p');
      const labels = { aprovado: 'Aprovado', reprovado: 'Reprovado' };
      const label = labels[turma.situacao];
      frequency.className = 'frequencia-value ' + (label ? turma.situacao : 'sem_dados');
      frequency.textContent = label ? `Frequência: ${turma.percentual}% (${label})` : 'Frequência: sem dados';
      card.append(title, subject, frequency);
      list.appendChild(card);
    }
  }

  async function checkCalls() {
    if (busy || stopped || document.hidden) return;
    busy = true;
    try {
      const { chamadas } = await Aura.json('/api/sessoes/ativas/');
      const signature = JSON.stringify(chamadas);
      if (signature !== previousCalls) {
        calls.replaceChildren();
        for (const chamada of chamadas) {
          const notice = document.createElement('div');
          notice.className = 'turma-card';
          const title = document.createElement('h3');
          title.textContent = `Chamada iniciada: ${chamada.materia}`;
          const detail = document.createElement('p');
          detail.textContent = `${chamada.turma} — ${chamada.aula}. Leia o QR Code exibido pelo professor para confirmar sua presença.`;
          notice.append(title, detail);
          calls.appendChild(notice);
        }
        previousCalls = signature;
      }
      callsStatus.textContent = chamadas.length ? 'Há chamada aguardando sua presença.' : 'Nenhuma chamada pendente. Os avisos são atualizados automaticamente.';
    } catch (error) {
      callsStatus.textContent = 'Não foi possível atualizar os avisos. Tentaremos novamente.';
    } finally {
      busy = false;
      clearTimeout(polling);
      if (!stopped) polling = setTimeout(checkCalls, 5000);
    }
  }

  joinForm.addEventListener('submit', async event => {
    event.preventDefault();
    const button = document.getElementById('join-btn');
    button.disabled = true;
    try {
      let code = inviteInput.value.trim();
      if (/^https?:\/\//i.test(code)) code = new URL(code).searchParams.get('convite') || '';
      const invitation = /^[0-9a-f]{8}-[0-9a-f-]{27}$/i.test(code)
        ? { link_acesso: code } : { codigo_acesso: code.toUpperCase() };
      const data = await Aura.json('/api/aluno/entrar-turma/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(invitation)
      });
      joinMessage.textContent = data.detail;
      inviteInput.value = '';
      await loadGroups();
      await checkCalls();
    } catch (error) {
      joinMessage.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) { clearTimeout(polling); checkCalls(); }
  });
  window.addEventListener('pagehide', () => { stopped = true; clearTimeout(polling); });
  window.addEventListener('pageshow', () => { if (stopped) { stopped = false; checkCalls(); } });

  loadGroups().then(checkCalls).catch(error => {
    list.textContent = error.message;
  }).finally(() => {
    loading.style.display = 'none';
    content.style.display = 'block';
  });
});
