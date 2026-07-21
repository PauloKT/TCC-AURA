import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useParams, useNavigate } from 'react-router-dom';

const ConfirmarPresenca = () => {
  const { sessaoId, token } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [professorData, setProfessorData] = useState(null);
  const [position, setPosition] = useState(null);
  const [locationError, setLocationError] = useState('');

  // Fetch professor location and radius from sessao token endpoint
  useEffect(() => {
    const fetchProfessorData = async () => {
      try {
        const res = await api.get(`/sessoes/${sessaoId}/token/`);
        setProfessorData(res.data);
      } catch (err) {
        console.error('Erro ao obter dados da sessão', err);
        setError('Sessão inválida ou expirada');
      }
    };
    if (sessaoId && token) {
      fetchProfessorData();
    }
  }, [sessaoId, token]);

  // Request geolocation
  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocalização não suportada pelo seu navegador.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPosition({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        });
        setLocationError('');
      },
      (err) => {
        setLocationError(`Erro ao obter localização: ${err.message}`);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  }, []);

  const handleConfirm = async () => {
    if (!position) {
      setError('Aguardando obtenção da localização...');
      return;
    }
    if (!professorData) {
      setError('Dados da sessão não disponíveis.');
      return;
    }
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await api.post(`/presenca/registrar/`, {
        sessao_id: sessaoId,
        token: token,
        latitude: position.latitude,
        longitude: position.longitude,
      });
      setMessage('Presença confirmada com sucesso!');
      // Optionally redirect to aluno dashboard after a delay
      setTimeout(() => {
        navigate('/aluno');
      }, 2000);
    } catch (err) {
      let msg = 'Erro ao registrar presença';
      if (err.response && err.response.data) {
        msg = err.response.data.detail || err.response.data.erro || JSON.stringify(err.response.data);
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Confirmação de Presença</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {message && <p style={{ color: 'green' }}>{message}</p>}
      {locationError && <p style={{ color: 'orange' }}>{locationError}</p>}
      {!professorData && !loading && !error && <p>Carregando dados da sessão...</p>}
      {professorData && (
        <div>
          <p>
            Código da sessão: <strong>{sessaoId}</strong>
          </p>
          <p>
            Token válido por: <strong>{professorData.segundos_restantes}</strong> segundos
          </p>
          <p>
            Coordenadas da instituição: Latitude{' '}
            <strong>{professorData.professor_latitude?.toFixed(6)}</strong>, Longitude{' '}
            <strong>{professorData.professor_longitude?.toFixed(6)}</strong>
          </p>
          <p>
            Raio permitido: <strong>{professorData.professor_radius_meters}</strong> metros
          </p>
          {!position && !loading && (
            <p>Aguarde enquanto obtemos sua localização...</p>
          )}
          {position && (
            <p>
              Sua localização: Latitude <strong>{position.latitude.toFixed(6)}</strong>, Longitude{' '}
              <strong>{position.longitude.toFixed(6)}</strong>
            </p>
          )}
          <button
            onClick={handleConfirm}
            disabled={loading || !position || !professorData}
          >
            {loading ? 'Verificando...' : 'Confirmar Presença'}
          </button>
        </div>
      )}
    </div>
  );
};

export default ConfirmarPresenca;