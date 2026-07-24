import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';
import jwtDecode from 'jwt-decode';

const AlunoDashboard = () => {
  const [turmas, setTurmas] = useState([]);
  const [frequencias, setFrequencias] = useState({}); // map turmaId -> {percentual, situacao}
  const [loading, setLoading] = useState(true);

  // Get user role from token to ensure aluno
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      // redirect handled by PrivateRoute
      return;
    }
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.role !== 'aluno') {
      // Should not happen due to PrivateRoute
      return;
    }
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // Get enrollments (turma-aluno) for this user
      const res = await api.get('/turma-aluno/');
      const myTurmas = res.data.filter((ta) => ta.aluno === /* current user id */);
      // We'll need to get user id from token
      const token = localStorage.getItem('access_token');
      const payload = JSON.parse(atob(token.split('.')[1]));
      const userId = payload.user_id;
      const turmasResp = await api.get(`/turma-aluno/?aluno=${userId}`);
      const turmaIds = turmasResp.data.map((t) => t.turma);
      // Fetch details of those turmas
      const turmasDetails = await Promise.all(
        turmaIds.map((id) => api.get(`/turmas/${id}/`))
      );
      setTurmas(turmasDetails.map((r) => r.data));
      // For each turma, get frequencia via endpoint
      const freqPromises = turmaIds.map((id) =>
        api.get(`/aluno/minha-frequencia/?turma=${id}`)
      );
      const freqResults = await Promise.all(freqPromises);
      const freqMap = {};
      freqResults.forEach((resp, idx) => {
        freqMap[turmaIds[idx]] = resp.data;
      });
      setFrequencias(freqMap);
    } catch (err) {
      console.error('Erro ao carregar dados do aluno', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p>Carregando...</p>;

  return (
    <div className="container">
      <h1>Painel do Aluno</h1>
      <h2>Minhas Turmas</h2>
      {turmas.length === 0 ? (
        <p>Você não está matriculado em nenhuma turma.</p>
      ) : (
        <ul>
          {turmas.map((t) => {
            const freq = frequencias[t.id] || { percentual: 0, situacao: 'sem_dados' };
            return (
              <li key={t.id}>
                <strong>{t.nome}</strong> ({t.materia.nome}) - {t.semestre}/{t.ano}
                <br />
                Frequência: {freq.percentual}% ({freq.situacao})
                {freq.situacao === 'reprovado' && (
                  <span style={{ color: 'red' }}> - Atenção!</span>
                )}
              </li>
            )}
          </ul>
        )}
    </div>
  );
};

export default AlunoDashboard;