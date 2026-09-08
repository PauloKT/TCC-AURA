document.addEventListener('DOMContentLoaded', function() {
  // DOM Elements
  const errorMessage = document.getElementById('error-message');
  const successMessage = document.getElementById('success-message');
  const loadingEl = document.getElementById('loading');
  const contentEl = document.getElementById('content');
  const sessionCodeEl = document.getElementById('session-code');
  const tokenTimeEl = document.getElementById('token-time');
  const instLatEl = document.getElementById('inst-lat');
  const instLngEl = document.getElementById('inst-lng');
  const instRadiusEl = document.getElementById('inst-radius');
  const waitingLocationEl = document.getElementById('waiting-location');
  const userLocationEl = document.getElementById('user-location');
  const userLatEl = document.getElementById('user-lat');
  const userLngEl = document.getElementById('user-lng');
  const locationErrorEl = document.getElementById('location-error');
  const confirmBtn = document.getElementById('confirm-btn');

  // Get URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const sessaoId = urlParams.get('sessaoId');
  const token = urlParams.get('token');

  if (!sessaoId || !token) {
    showError('URL inválida. Parâmetros da sessão não encontrados.');
    return;
  }

  // API Base URL
  const API_BASE = '/api/';

  // Session data
  let professorData = null;
  let userPosition = null;

  // Initialize
  init();

  function init() {
    // Show loading state
    loadingEl.style.display = 'block';
    contentEl.style.display = 'none';

    // Fetch professor data
    fetchProfessorData();

    // Get user location
    getUserLocation();
  }

  function fetchProfessorData() {
    fetch(API_BASE + `sessoes/${sessaoId}/token/`, {
      headers: {
        'Authorization': 'Bearer ' + localStorage.getItem('access_token')
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Sessão inválida ou expirada');
      }
      return response.json();
    })
    .then(data => {
      professorData = data;
      displayProfessorData();
    })
    .catch(error => {
      console.error('Erro ao obter dados da sessão:', error);
      showError('Sessão inválida ou expirada');
      loadingEl.style.display = 'none';
    });
  }

  function displayProfessorData() {
    if (!professorData) return;

    sessionCodeEl.textContent = sessaoId;
    tokenTimeEl.textContent = professorData.segundos_restantes || '0';
    instLatEl.textContent = professorData.professor_latitude?.toFixed(6) || 'N/A';
    instLngEl.textContent = professorData.professor_longitude?.toFixed(6) || 'N/A';
    instRadiusEl.textContent = professorData.professor_radius_meters || 'N/A';

    loadingEl.style.display = 'none';
    contentEl.style.display = 'block';
  }

  function getUserLocation() {
    if (!navigator.geolocation) {
      showLocationError('Geolocalização não suportada pelo seu navegador.');
      return;
    }

    waitingLocationEl.style.display = 'block';
    userLocationEl.style.display = 'none';
    locationErrorEl.style.display = 'none';

    navigator.geolocation.getCurrentPosition(
      position => {
        userPosition = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        };

        userLatEl.textContent = position.coords.latitude.toFixed(6);
        userLngEl.textContent = position.coords.longitude.toFixed(6);

        waitingLocationEl.style.display = 'none';
        userLocationEl.style.display = 'block';
        locationErrorEl.style.display = 'none';

        // Enable confirm button if we have both professor data and user position
        checkConfirmReady();
      },
      error => {
        let errorMessage = 'Erro desconhecido ao obter localização.';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Você negou o pedido de geolocalização.';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Informações de localização indisponíveis.';
            break;
          case error.TIMEOUT:
            errorMessage = 'O pedido de obter localização expirou.';
            break;
          case error.PERMISSION_DENIED:
            errorMessage = 'Geolocalização não suportada.';
            break;
        }
        showLocationError(errorMessage);
        waitingLocationEl.style.display = 'none';
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  }

  function showLocationError(message) {
    locationErrorEl.textContent = message;
    locationErrorEl.classList.add('show');
  }

  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
    // Hide success message if visible
    successMessage.classList.remove('show');
    successMessage.textContent = '';
  }

  function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.classList.add('show');
    // Hide error message if visible
    errorMessage.classList.remove('show');
    errorMessage.textContent = '';
  }

  function checkConfirmReady() {
    if (professorData && userPosition) {
      confirmBtn.disabled = false;
    } else {
      confirmBtn.disabled = true;
    }
  }

  confirmBtn.addEventListener('click', async () => {
    if (!professorData || !userPosition) {
      showError('Dados insuficientes para confirmar presença.');
      return;
    }

    // Check if we have the required data
    if (
      professorData.professor_latitude === null ||
      professorData.professor_longitude === null ||
      professorData.professor_radius_meters === null
    ) {
      showError('Dados da instituição incompletos.');
      return;
    }

    // O backend é a autoridade da regra de distância e responde com erro
    // específico quando a posição está fora do raio permitido.
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Confirmando...';

    try {
      const response = await fetch(API_BASE + 'presenca/registrar/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem('access_token')
        },
        body: JSON.stringify({
          sessao_id: sessaoId,
          token: token,
          latitude: userPosition.latitude,
          longitude: userPosition.longitude
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.erro || 'Erro ao registrar presença');
      }

      showSuccess('Presença confirmada com sucesso!');

      // Redirect to aluno dashboard after 2 seconds
      setTimeout(() => {
        window.location.href = 'aluno.html';
      }, 2000);
    } catch (error) {
      console.error('Erro ao registrar presença:', error);
      showError(error.message || 'Erro ao registrar presença');
    } finally {
      confirmBtn.disabled = false;
      confirmBtn.textContent = 'Confirmar Presença';
    }
  });
});