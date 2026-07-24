import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Register = () => {
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
    role: 'aluno',
    matricula: '',
    cep: '',
  });
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Basic validation
    const errs = {};
    if (!form.username) errs.username = 'Usuário obrigatório';
    if (!form.email) errs.email = 'E-mail obrigatório';
    if (!form.password) errs.password = 'Senha obrigatória';
    if (form.password !== form.password2) errs.password2 = 'Senhas não coincidem';
    if (form.role === 'professor' && !form.cep) errs.cep = 'CEP obrigatório para professores';
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    try {
      await axios.post('/api/register/', {
        username: form.username,
        email: form.email,
        password: form.password,
        role: form.role,
        matricula: form.role === 'aluno' ? form.matricula : undefined,
        cep: form.role === 'professor' ? form.cep : undefined,
      });
      alert('Cadastro realizado com sucesso! Faça login.');
      navigate('/login');
    } catch (err) {
      if (err.response && err.response.data) {
        setErrors(err.response.data);
      } else {
        setErrors({ submit: 'Erro ao cadastrar' });
      }
    }
  };

  return (
    <div className="container">
      <h2>Registro</h2>
      {Object.keys(errors).length > 0 && (
        <ul style={{ color: 'red' }}>
          {Object.entries(errors).map(([field, msg]) => (
            <li key={field}>{msg}</li>
          ))}
        </ul>
      )}
      <form onSubmit={handleSubmit}>
        <div>
          <label>Usuário:</label>
          <input
            type="text"
            name="username"
            value={form.username}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label>E-mail:</label>
          <input
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label>Senha:</label>
          <input
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label>Confirmar Senha:</label>
          <input
            type="password"
            name="password2"
            value={form.password2}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label>Tipo de usuário:</label>
          <select name="role" value={form.role} onChange={handleChange}>
            <option value="aluno">Aluno</option>
            <option value="professor">Professor</option>
          </select>
        </div>
        {form.role === 'aluno' && (
          <div>
            <label>Matrícula (opcional):</label>
            <input
              type="text"
              name="matricula"
              value={form.matricula}
              onChange={handleChange}
            />
          </div>
        )}
        {form.role === 'professor' && (
          <div>
            <label>CEP da Instituição:</label>
            <input
              type="text"
              name="cep"
              value={form.cep}
              onChange={handleChange}
              placeholder="00000-000"
              maxLength="9"
              required
            />
          </div>
        )}
        <button type="submit">Registrar</button>
      </form>
      <p>
        Já tem conta? <a href="/login">Faça login</a>
      </p>
    </div>
  );
};

export default Register;