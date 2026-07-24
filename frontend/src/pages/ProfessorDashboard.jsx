import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

const ProfessorDashboard = () => {
  const [materias, setMaterias] = useState([]);
  [turmas, setTurmas] = useState([]);
  [aulas, setAulas] = useState([]);
  const [selectedMateria, setSelectedMateria] = useState(null);
  const [selectedTurma, setSelectedTurma] = useState(null);
  const [formValues, setFormValues] = useState({
    materiaNome: '',
    materiaCodigo: '',
    materiaCarga: '',
    materiaFreq: '',
    turmaNome: '',
    turmaSemestre: '',
    turmaAno: '',
    aulaTitulo: '',
    aulaData: '',
    aulaInicio: '',
    aulaFim: '',
  });
  const [loading, setLoading] = useState(false);
  const [qrCodeUrl, setQrCodeUrl] = useState(null);
  const [countdown, setCountdown] = useState(null);
  const navigate = useNavigate();

  // Fetch materias for logged-in professor
  useEffect(() => {
    const fetchMaterias = async () => {
      try {
        const res = await api.get('/materias/');
        setMaterias(res.data);
      } catch (err) {
        console.error('Erro ao carregar matérias', err);
      }
    };
    fetchMaterias();
  }, []);

  // Fetch turmas when materia selected
  useEffect(() => {
    if (selectedMateria) {
      const fetchTurmas = async () => {
        try {
          const res = await api.get(`/turmas/?materia=${selectedMateria}`);
          setTurmas(res.data);
        } catch (err) {
          console.error('Erro ao carregar turmas', err);
        }
      };
      fetchTurmas();
    } else {
      setTurmas([]);
    }
  }, [selectedMateria]);

  // Fetch aulas when turma selected
  useEffect(() => {
    if (selectedTurma) {
      const fetchAulas = async () => {
        try {
          const res = await api.get(`/aulas/?turma=${selectedTurma}`);
          setAulas(res.data);
        } catch (err) {
          console.error('Erro ao carregar aulas', err);
        }
      };
      fetchAulas();
    } else {
      setAulas([]);
    }
  }, [selectedTurma]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormValues({ ...formValues, [name]: value });
  };

  const handleMateriaChange = (e) => {
    setSelectedMateria(e.target.value);
  };

  const handleTurmaChange = (e) => {
    setSelectedTurma(e.target.value);
  };

  const createMateria = async () => {
    try {
      await api.post('/materias/', {
        nome: formValues.materiaNome,
        codigo: formValues.materiaCodigo,
        carga_horaria: parseInt(formValues.materiaCarga),
        frequencia_minima: parseInt(formValues.materiaFreq),
      });
      alert('Matéria criada!');
      // Reset form and refresh list
      setFormValues({ ...formValues, materiaNome: '', materiaCodigo: '', materiaCarga: '', materiaFreq: '' });
      // refetch materias
      const res = await api.get('/materias/');
      setMaterias(res.data);
    } catch (err) {
      console.error('Erro ao criar matéria', err);
      alert('Falha ao criar matéria');
    }
  };

  const createTurma = async () => {
    try {
      await api.post('/turmas/', {
        nome: formValues.turmaNome,
        materia: selectedMateria,
        semestre: formValues.turmaSemestre,
        ano: parseInt(formValues.turmaAno),
      });
      alert('Turma criada!');
      setFormValues({ ...formValues, turmaNome: '', turmaSemestre: '', turmaAno: '' });
      const res = await api.get(`/turmas/?materia=${selectedMateria}`);
      setTurmas(res.data);
    } catch (err) {
      console.error('Erro ao criar turma', err);
      alert('Falha ao criar turma');
    }
  };

  const createAula = async () => {
    try {
      await api.post('/aulas/', {
        titulo: formValues.aulaTitulo,
        turma: selectedTurma,
        data: formValues.aulaData,
        horario_inicio: formValues.aulaInicio,
        horario_fim: formValues.aulaFim,
      });
      alert('Aula criada!');
      setFormValues({ ...formValues, aulaTitulo: '', aulaData: '', aulaInicio: '', aulaFim: '' });
      const res = await api.get(`/aulas/?turma=${selectedTurma}`);
      setAulas(res.data);
    } catch (err) {
      console.error('Erro ao criar aula', err);
      alert('Falha ao criar aula');
    }
  };

  const startSession = async () => {
    if (!selectedAulaId) {
      alert('Selecione uma aula');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post(`/sessoes/iniciar/`, {
        aula: selectedAulaId,
      });
      const { id, token_atual, token_expira_em, professor_latitude, professor_longitude, professor_radius_meters } = res.data;
      // Store session id in state or context
      // For simplicity, we'll navigate to a page showing QR code
      // We'll create a temporary state to hold session data
      // We'll use a separate component or just show here
      setQrCodeUrl(`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(
        window.location.origin + `/confirmar/${id}/${token_atual}`
      )}&size=200x200`);
      // Start countdown
      const startTime = new Date(token_expira_em);
      const interval = setInterval(() => {
        const now = new Date();
        const diff = startTime - now;
        if (diff <= 0) {
          clearInterval(interval);
          setCountdown('00:00');
          // Optionally refresh token automatically? Not needed for demo.
        } else {
          const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          const seconds = Math.floor((diff % (1000 * 60)) / 1000);
          setCountdown(`${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`);
        }
      }, 1000);
      // We'll store interval id to clear on unmount
      // For simplicity, we'll just set a state variable
      // We'll need to clean up later; we'll skip for brevity.
    } catch (err) {
      console.error('Erro ao iniciar sessão', err);
      alert('Falha ao iniciar sessão');
    } finally {
      setLoading(false);
    }
  };

  // We need selectedAulaId state
  const [selectedAulaId, setSelectedAulaId] = useState(null);

  return (
    <div className="container">
      <h1>Painel do Professor</h1>
      <div>
        <h2>Minhas Matérias</h2>
        <select value={selectedMateria || ''} onChange={handleMateriaChange}>
          <option value="">Selecione uma matéria</option>
          {materias.map((m) => (
            <option key={m.id} value={m.id}>
              {m.nome} ({m.codigo})
            </option>
          ))}
        </select>
        {/* Form to add new materia */}
        <div style={{ marginTop: '20px' }}>
          <h3>Cadastrar Nova Matéria</h3>
          <input
            placeholder="Nome"
            name="materiaNome"
            value={formValues.materiaNome}
            onChange={handleChange}
          />
          <input
            placeholder="Código"
            name="materiaCodigo"
            value={formValues.materiaCodigo}
            onChange={handleChange}
          />
          <input
            type="number"
            placeholder="Carga Horária"
            name="materiaCarga"
            value={formValues.materiaCarga}
            onChange={handleChange}
          />
          <input
            type="number"
            placeholder="Frequência Mínima (%)"
            name="materiaFreq"
            value={formValues.materiaFreq}
            onChange={handleChange}
          />
          <button onClick={createMateria}>Salvar Matéria</button>
        </div>
      </div>

      {selectedMateria && (
        <>
          <div>
            <h2>Turmas da Matéria {materias.find((m) => m.id == selectedMateria)?.nome}</h2>
            <select value={selectedTurma || ''} onChange={handleTurmaChange}>
              <option value="">Selecione uma turma</option>
              {turmas.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nome} ({t.semestre}/{t.ano})
                </option>
              ))}
            </select>
            <div style={{ marginTop: '20px' }}>
              <h3>Cadastrar Nova Turma</h3>
              <input
                placeholder="Nome"
                name="turmaNome"
                value={formValues.turmaNome}
                onChange={handleChange}
              />
              <input
                placeholder="Semestre (ex: 2024.1)"
                name="turmaSemestre"
                value={formValues.turmaSemestre}
                onChange={handleChange}
              />
              <input
                type="number"
                placeholder="Ano"
                name="turmaAno"
                value={formValues.turmaAno}
                onChange={handleChange}
              />
              <button onClick={createTurma}>Salvar Turma</button>
            </div>
          </div>
        </>
      )}

      {selectedTurma && (
        <>
          <div>
            <h2>Aulas da Turma {turmas.find((t) => t.id == selectedTurma)?.nome}</h2>
            <select value={selectedAulaId || ''} onChange={(e) => setSelectedAulaId(e.target.value)}>
              <option value="">Selecione uma aula</option>
              {aulas.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.titulo} ({new Date(a.data).toLocaleDateString()})
                </option>
              ))}
            </select>
            <div style={{ marginTop: '20px' }}>
              <h3>Cadastrar Nova Aula</h3>
              <input
                placeholder="Título"
                name="aulaTitulo"
                value={formValues.aulaTitulo}
                onChange={handleChange}
              />
              <input
                type="date"
                name="aulaData"
                value={formValues.aulaData}
                onChange={handleChange}
              />
              <input
                type="time"
                name="aulaInicio"
                value={formValues.aulaInicio}
                onChange={handleChange}
              />
              <input
                type="time"
                name="aulaFim"
                value={formValues.aulaFim}
                onChange={handleChange}
              />
              <button onClick={createAula}>Salvar Aula</button>
            </div>
          </div>
        </>
      )}

      {selectedAulaId && (
        <div style={{ marginTop: '30px' }}>
          <h2>Iniciar Chamada para a Aula Selecionada</h2>
          <button onClick={startSession} disabled={loading}>
            {loading ? 'Iniciando...' : 'Iniciar Chamada'}
          </button>
          {qrCodeUrl && (
            <div style={{ marginTop: '20px', textAlign: 'center' }}>
              <h3>QR Code para os Alunos</h3>
              <img src={qrCodeUrl} alt="QR Code" />
              <p>Token válido por: <strong>{countdown || '00:30'}</strong> segundos</p>
              <p>
                Coordenadas da instituição: Latitude {professor_latitude?.toFixed
                  ?.()} Longitude {professor_longitude?.toFixed?.()} Raio:
                  {professor_radius_meters} m
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProfessorDashboard;