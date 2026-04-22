import axios from 'axios';

const api = axios.create({ baseURL: process.env.REACT_APP_API_URL || '' });

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export const authAPI = {
  login:    data => api.post('/api/auth/login', data),
  register: data => api.post('/api/auth/register', data),
};

export const accountAPI = {
  list:         ()         => api.get('/api/accounts'),
  create:       data       => api.post('/api/accounts', data),
  deposit:      (id, data) => api.post(`/api/accounts/${id}/deposit`, data),
  withdraw:     (id, data) => api.post(`/api/accounts/${id}/withdraw`, data),
  transactions: id         => api.get(`/api/accounts/${id}/transactions`),
};

export const transferAPI = {
  send: data => api.post('/api/transfer', data),
};

export default api;
