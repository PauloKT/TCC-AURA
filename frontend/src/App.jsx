import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import ProfessorDashboard from './pages/ProfessorDashboard';
import AlunoDashboard from './pages/AlunoDashboard';
import ConfirmarPresenca from './pages/ConfirmarPresenca';
import './App.css';

const PrivateRoute = ({ children, role }) => {
  const token = localStorage.getItem('access_token');
  if (!token) return <Navigate to="/login" replace />;
  // Decode token to check role (simple)
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.role !== role) {
      return <Navigate to="/" replace />;
    }
  } catch (e) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/professor"
            element={
              <PrivateRoute role="professor">
                <ProfessorDashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/aluno"
            element={
              <PrivateRoute role="aluno">
                <AlunoDashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/confirmar/:sessaoId/:token"
            element={<ConfirmarPresenca />}
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;