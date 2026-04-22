import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api';
import './Auth.css';

export default function Login() {
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handle = e => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async e => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const { data } = await authAPI.login(form);
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="auth-card card">
        <div className="auth-logo">⎈</div>
        <h2>K8s Bank</h2>
        <p className="auth-sub">Sign in to your account</p>
        <form onSubmit={submit}>
          <div className="field">
            <label>Username</label>
            <input name="username" value={form.username} onChange={handle}
                   placeholder="demo" required />
          </div>
          <div className="field">
            <label>Password</label>
            <input name="password" type="password" value={form.password}
                   onChange={handle} placeholder="••••••••" required />
          </div>
          {error && <p className="error-msg">{error}</p>}
          <button className="btn-primary" style={{width:'100%',marginTop:12}}
                  disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
        <p className="auth-footer">
          No account? <Link to="/register">Register</Link>
        </p>
        <p className="auth-hint">Demo: username <b>demo</b> / password <b>demo1234</b></p>
      </div>
    </div>
  );
}
