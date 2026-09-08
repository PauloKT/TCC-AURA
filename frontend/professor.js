document.addEventListener('DOMContentLoaded', function() {
  // DOM Elements
  const loadingDiv = document.getElementById('loading');
  const contentDiv = document.getElementById('content');

  const materiaSelect = document.getElementById('materia-select');
  const materiaForm = document.getElementById('materia-form');
  const materiaNomeInput = document.getElementById('materia-nome');
  const materiaCodigoInput = document.getElementById('materia-codigo');
  const materiaCargaInput = document.getElementById('materia-carga');
  const materiaFreqInput = document.getElementById('materia-freq');
  const createMateriaBtn = document.getElementById('create-materia-btn');

  const turmasSection = document.getElementById('turmas-section');
  const materiaNomeDisplay = document.getElementById('materia-nome-display');
  const turmaSelect = document.getElementById('turma-select');
  const turmaForm = document.getElementById('turma-form');
  const turmaNomeInput = document.getElementById('turma-nome');
  const turmaSemestreInput = document.getElementById('turma-semestre');
  const turmaAnoInput = document.getElementById('turma-ano');
  const createTurmaBtn = document.getElementById('create-turma-btn');

  const aulasSection = document.getElementById('aulas-section');
  const turmaNomeDisplay2 = document.getElementById('turma-nome-display');
  const aulaSelect = document.getElementById('aula-select');
  const aulaForm = document.getElementById('aula-form');
  const aulaTituloInput = document.getElementById('aula-titulo');
  const aulaDataInput = document.getElementById('aula-data');
  const aulaInicioInput = document.getElementById('aula-inicio');
  const aulaFimInput = document.getElementById('aula-fim');
  const createAulaBtn = document.getElementById('create-aula-btn');

  const sessionSection = document.getElementById('session-section');
  const startSessionBtn = document.getElementById('start-session-btn');
  const qrCodeContainer = document.getElementById('qr-code-container');
  const qrCodeImg = document.getElementById('qr-code-img');
  const countdownEl = document.getElementById('countdown');
  const locationInfoEl = document.getElementById('location-info');
  let countdownInterval = null;
  let currentAulaId = null;

  // API Base URL
  const API_BASE = '/api/';

  // Check authentication on load
  checkAuth();

  async function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      window.location.href = 'login.html';
      return;
    }

    try {
      const base64Url = token.split('.')[1];
      let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      // Pad with = to make length a multiple of 4
      while (base64.length % 4) {
        base64 += '=';
      }
      const payload = JSON.parse(atob(base64));
      if (payload.role !== 'professor') {
        window.location.href = 'login.html';
        return;
      }

      // Hide loading, show content
      loadingDiv.style.display = 'none';
      contentDiv.style.display = 'block';

      // Fetch initial data
      fetchMaterias();
    } catch (e) {
      window.location.href = 'login.html';
    }
  }

  async function fetchMaterias() {
    try {
      const response = await fetch(API_BASE + 'materias/', {
        headers: {
          'Authorization': 'Bearer ' + localStorage.getItem('access_token')
        }
      });

      if (!response.ok) throw new Error('Failed to fetch materias');

      const materias = await response.json();

      // Clear and repopulate select
      materiaSelect.innerHTML = '<option value="">Selecione uma matéria</option>';
      materias.forEach(materia => {
        const option = document.createElement('option');
        option.value = materia.id;
        option.textContent = `${materia.nome} (${materia.codigo})`;
        materiaSelect.appendChild(option);
      });
    } catch (error) {
      console.error('Erro ao carregar matérias:', error);
      alert('Erro ao carregar matérias');
    }
  }

  materiaSelect.addEventListener('change', function() {
    const materiaId = this.value;

    if (materiaId) {
      currentAulaId = null; // Reset aula selection
      fetchTurmas(materiaId);
      turmasSection.style.display = 'block';
      aulasSection.style.display = 'none';
      sessionSection.style.display = 'none';

      // Update materia name display
      const selectedOption = this.selectedOptions[0];
      materiaNomeDisplay.textContent = selectedOption.textContent.split(' (')[0];
    } else {
      turmasSection.style.display = 'none';
      aulasSection.style.display = 'none';
      sessionSection.style.display = 'none';
      resetForms();
    }
  });

  async function fetchTurmas(materiaId) {
    try {
      const response = await fetch(API_BASE + `turmas/?materia=${materiaId}`, {
        headers: {
          'Authorization': 'Bearer ' + localStorage.getItem('access_token')
        }
      });

      if (!response.ok) throw new Error('Failed to fetch turmas');

      const turmas = await response.json();

      // Clear and repopulate select
      turmaSelect.innerHTML = '<option value="">Selecione uma turma</option>';
      turmas.forEach(turma => {
        const option = document.createElement('option');
        option.value = turma.id;
        option.textContent = `${turma.nome} (${turma.semestre}/${turma.ano})`;
        turmaSelect.appendChild(option);
      });
    } catch (error) {
      console.error('Erro ao carregar turmas:', error);
      alert('Erro ao carregar turmas');
    }
  }

  turmaSelect.addEventListener('change', function() {
    const turmaId = this.value;

    if (turmaId) {
      fetchAulas(turmaId);
      aulasSection.style.display = 'block';
      sessionSection.style.display = 'none';

      // Update turma name display
      const selectedOption = this.selectedOptions[0];
      turmaNomeDisplay2.textContent = selectedOption.textContent.split(' (')[0];
    } else {
      aulasSection.style.display = 'none';
      sessionSection.style.display = 'none';
      currentAulaId = null;
    }
  });

  async function fetchAulas(turmaId) {
    try {
      const response = await fetch(API_BASE + `aulas/?turma=${turmaId}`, {
        headers: {
          'Authorization': 'Bearer ' + localStorage.getItem('access_token')
        }
      });

      if (!response.ok) throw new Error('Failed to fetch aulas');

      const aulas = await response.json();

      // Clear and repopulate select
      aulaSelect.innerHTML = '<option value="">Selecione uma aula</option>';
      aulas.forEach(aula => {
        const option = document.createElement('option');
        option.value = aula.id;
        const date = new Date(aula.data).toLocaleDateString();
        option.textContent = `${aula.titulo} (${date})`;
        aulaSelect.appendChild(option);
      });
    } catch (error) {
      console.error('Erro ao carregar aulas:', error);
      alert('Erro ao carregar aulas');
    }
  }

  aulaSelect.addEventListener('change', function() {
    const aulaId = this.value;
    currentAulaId = aulaId;
    if (currentAulaId) {
      sessionSection.style.display = 'block';
    } else {
      sessionSection.style.display = 'none';
      clearCountdown();
      hideQRCode();
    }
  });

  // Create materia
  createMateriaBtn.addEventListener('click', async function() {
    const nome = materiaNomeInput.value.trim();
    const codigo = materiaCodigoInput.value.trim();
    const carga = parseInt(materiaCargaInput.value);
    const freq = parseInt(materiaFreqInput.value);

    if (!nome || !codigo || isNaN(carga) || isNaN(freq)) {
      alert('Por favor, preencha todos os campos corretamente');
      return;
    }

    try {
      const response = await fetch(API_BASE + 'materias/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem('access_token')
        },
        body: JSON.stringify({
          nome: nome,
          codigo: codigo,
          carga_horaria: carga,
          frequencia_minima: freq
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao criar matéria');
      }

      alert('Matéria criada com sucesso!');

      // Reset form
      materiaNomeInput.value = '';
      materiaCodigoInput.value = '';
      materiaCargaInput.value = '';
      materiaFreqInput.value = '';

      // Refresh materias list
      fetchMaterias();
    } catch (error) {
      console.error('Erro ao criar matéria:', error);
      alert('Falha ao criar matéria: ' + error.message);
    }
  });

  // Create turma
  createTurmaBtn.addEventListener('click', async function() {
    const nome = turmaNomeInput.value.trim();
    const materiaId = materiaSelect.value;
    const semestre = turmaSemestreInput.value.trim();
    const ano = parseInt(turmaAnoInput.value);

    if (!nome || !materiaId || !semestre || isNaN(ano)) {
      alert('Por favor, preencha todos os campos corretamente');
      return;
    }

    try {
      const response = await fetch(API_BASE + 'turmas/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem('access_token')
        },
        body: JSON.stringify({
          nome: nome,
          materia: materiaId,
          semestre: semestre,
          ano: ano
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao criar turma');
      }

      alert('Turma criada com sucesso!');

      // Reset form
      turmaNomeInput.value = '';
      turmaSemestreInput.value = '';
      turmaAnoInput.value = '';

      // Refresh turmas list
      fetchTurmas(materiaId);
    } catch (error) {
      console.error('Erro ao criar turma:', error);
      alert('Falha ao criar turma: ' + error.message);
    }
  });

  // Create aula
  createAulaBtn.addEventListener('click', async function() {
    const titulo = aulaTituloInput.value.trim();
    const turmaId = turmaSelect.value;
    const data = aulaDataInput.value;
    const inicio = aulaInicioInput.value;
    const fim = aulaFimInput.value;

    if (!titulo || !turmaId || !data || !inicio || !fim) {
      alert('Por favor, preencha todos os campos corretamente');
      return;
    }

    try {
      const response = await fetch(API_BASE + 'aulas/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem('access_token')
        },
        body: JSON.stringify({
          titulo: titulo,
          turma: turmaId,
          data: data,
          hora_inicio: inicio,
          hora_fim: fim
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao criar aula');
      }

      alert('Aula criada com sucesso!');

      // Reset form
      aulaTituloInput.value = '';
      aulaDataInput.value = '';
      aulaInicioInput.value = '';
      aulaFimInput.value = '';

      // Refresh aulas list
      fetchAulas(turmaId);
    } catch (error) {
      console.error('Erro ao criar aula:', error);
      alert('Falha ao criar aula: ' + error.message);
    }
  });

  // Start session
  startSessionBtn.addEventListener('click', async function() {
    if (!currentAulaId) {
      alert('Selecione uma aula');
      return;
    }

    startSessionBtn.disabled = true;
    startSessionBtn.textContent = 'Iniciando...';

    try {
      const response = await fetch(API_BASE + 'sessoes/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem('access_token')
        },
        body: JSON.stringify({
          aula: currentAulaId
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao iniciar sessão');
      }

      const data = await response.json();
      const { id, token_atual, token_expira_em, professor_latitude, professor_longitude, professor_radius_meters } = data;

      // Generate QR code
      const qrData = window.location.origin + `/confirmar-presenca.html?sessaoId=${id}&token=${token_atual}`;
      qrCodeImg.src = `https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qrData)}&size=200x200`;

      // Show QR code and info
      qrCodeContainer.style.display = 'block';
      locationInfoEl.innerHTML = `
        Coordinates of the institution: Latitude <strong>${professor_latitude?.toFixed(6) ?? 'N/A'}</strong>,
        Longitude <strong>${professor_longitude?.toFixed(6) ?? 'N/A'}</strong><br>
        Allowed radius: <strong>${professor_radius_meters ?? 'N/A'}</strong> meters
      `;

      // Start countdown
      startCountdown(new Date(token_expira_em));

    } catch (error) {
      console.error('Erro ao iniciar sessão:', error);
      alert('Falha ao iniciar sessão: ' + error.message);
    } finally {
      startSessionBtn.disabled = false;
      startSessionBtn.textContent = 'Iniciar Chamada';
    }
  });

  function startCountdown(expiryTime) {
    clearCountdown();

    const updateCountdown = () => {
      const now = new Date();
      const diff = expiryTime - now;

      if (diff <= 0) {
        clearCountdown();
        countdownEl.textContent = '00:00';
        // Optionally auto-refresh or notify
        return;
      }

      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);
      countdownEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    };

    updateCountdown(); // Initial update
    countdownInterval = setInterval(updateCountdown, 1000);
  }

  function clearCountdown() {
    if (countdownInterval) {
      clearInterval(countdownInterval);
      countdownInterval = null;
    }
  }

  function hideQRCode() {
    qrCodeContainer.style.display = 'none';
    qrCodeImg.src = '';
    countdownEl.textContent = '00:30';
    locationInfoEl.innerHTML = '';
  }

  function resetForms() {
    materiaForm.reset();
    turmaForm.reset();
    aulaForm.reset();
  }

  // Cleanup on page unload
  window.addEventListener('beforeunload', function() {
    clearCountdown();
  });
});