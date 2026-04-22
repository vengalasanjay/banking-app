import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api';
import './Auth.css';

export default function Register() {
  const [form, setForm] = useState({ username:'', email:'', password:'', full_name:'' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handle = e => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async e => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const { data } = await authAPI.register(form);
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="auth-card card">
        <div className="auth-logo">⎈</div>
        <h2>Create Account</h2>
        <p className="auth-sub">Join K8s Bank today</p>
        <form onSubmit={submit}>
          {[['full_name','Full Name','John Doe'],['username','Username','johndoe'],
            ['email','Email','john@example.com'],['password','Password','••••••••','password']]
            .map(([name,label,ph,type='text']) => (
              <div className="field" key={name}>
                <label>{label}</label>
                <input name={name} type={type} value={form[name]}
                       onChange={handle} placeholder={ph} required />
              </div>
            ))}
          {error && <p className="error-msg">{error}</p>}
          <button className="btn-primary" style={{width:'100%',marginTop:12}}
                  disabled={loading}>
            {loading ? 'Creating…' : 'Create Account'}
          </button>
        </form>
        <p className="auth-footer">
          Have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
