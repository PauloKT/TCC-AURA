document.addEventListener('DOMContentLoaded', function() {
  // DOM Elements
  const loadingDiv = document.getElementById('loading');
  const contentDiv = document.getElementById('content');
  const turmasList = document.getElementById('turmas-list');

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
      if (payload.role !== 'aluno') {
        window.location.href = 'login.html';
        return;
      }

      // Hide loading, show content
      loadingDiv.style.display = 'none';
      contentDiv.style.display = 'block';

      // Fetch student data
      fetchStudentData();
    } catch (e) {
      window.location.href = 'login.html';
    }
  }

  async function fetchStudentData() {
    try {
      // Get user ID from token
      const token = localStorage.getItem('access_token');
      const payload = JSON.parse(atob(token.split('.')[1]));
      const userId = payload.user_id;

      // Get enrollments for this student
      const response = await fetch(API_BASE + `turma-aluno/?aluno=${userId}`, {
        headers: {
          'Authorization': 'Bearer ' + token
        }
      });

      if (!response.ok) throw new Error('Failed to fetch enrollments');

      const enrollments = await response.json();
      const turmaIds = enrollments.map(enrollment => enrollment.turma);

      if (turmaIds.length === 0) {
        // No enrollments
        turmasList.innerHTML = '<p class="empty-message">Você não está matriculado em nenhuma turma.</p>';
        return;
      }

      // Fetch details for each turma
      const turmasDetails = await Promise.all(
        turmaIds.map(id =>
          fetch(API_BASE + `turmas/${id}/`, {
            headers: {
              'Authorization': 'Bearer ' + token
            }
          }).then(res => {
            if (!res.ok) throw new Error(`Failed to fetch turma ${id}`);
            return res.json();
          })
        )
      );

      // Fetch frequencies for each turma
      const freqPromises = turmaIds.map(id =>
        fetch(API_BASE + `aluno/minha-frequencia/?turma=${id}`, {
          headers: {
            'Authorization': 'Bearer ' + token
          }
        }).then(res => {
          if (!res.ok) {
            // If no frequency record, return default
            return { percentual: 0, situacao: 'sem_dados' };
          }
          return res.json();
        })
      );

      const freqResults = await Promise.all(freqPromises);

      // Render turmas
      renderTurmas(turmasDetails, freqResults);
    } catch (error) {
      console.error('Erro ao carregar dados do aluno:', error);
      turmasList.innerHTML = '<p class="error-message">Erro ao carregar dados. Por favor, tente novamente.</p>';
    }
  }

  function renderTurmas(turmas, frequencias) {
    // Clear the list
    turmasList.innerHTML = '';

    // Create a map of frequencies by turma ID for easy lookup
    const freqMap = {};
    frequencias.forEach((freq, index) => {
      if (turmas[index]) {
        freqMap[turmas[index].id] = freq;
      }
    });

    // If no frequencies were fetched (shouldn't happen, but just in case)
    if (Object.keys(freqMap).length === 0) {
      turmas.forEach(turma => {
        freqMap[turma.id] = { percentual: 0, situacao: 'sem_dados' };
      });
    }

    turmas.forEach((turma, index) => {
      const freq = freqMap[turma.id] || { percentual: 0, situacao: 'sem_dados' };

      // Determine frequency class and text
      let freqClass = '';
      let freqText = '';
      switch (freq.situacao) {
        case 'aprovado':
          freqClass = 'aprovado';
          freqText = `${freq.percentual}% (Aprovado)`;
          break;
        case 'reprovado':
          freqClass = 'reprovado';
          freqText = `${freq.percentual}% (Reprovado)`;
          break;
        default:
          freqClass = 'sem_dados';
          freqText = 'Sem dados';
      }

      const card = document.createElement('div');
      card.className = 'turma-card';

      card.innerHTML = `
        <div class="turma-header">
          <div class="turma-info">
            <div class="turma-name">${turma.nome}</div>
            <div class="turma-subject">${turma.materia.nome}</div>
            <div class="turma-period">${turma.semestre}/${turma.ano}</div>
          </div>
        </div>
        <div class="frequencia-info">
          <div class="frequencia-label">Frequência:</div>
          <div class="frequencia-value ${freqClass}">${freqText}</div>
          ${freq.situacao === 'reprovado' ? '<span class="atencao"> - Atenção!</span>' : ''}
        </div>
      `;

      turmasList.appendChild(card);
    });
  }
});