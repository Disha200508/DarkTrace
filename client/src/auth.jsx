import { createContext, useContext, useEffect, useState } from 'react';
import api from './api';

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!localStorage.getItem('dt_token'));
  useEffect(() => {
    if (!localStorage.getItem('dt_token')) return;
    api.get('/auth/me').then((r) => setUser(r.data)).catch(() => localStorage.removeItem('dt_token')).finally(() => setLoading(false));
  }, []);
  const login = async (portal, identifier, password) => {
    const r = await api.post('/auth/login', { portal, identifier, password });
    localStorage.setItem('dt_token', r.data.token); setUser(r.data.user); return r.data.user;
  };
  const register = async (payload) => {
    const r = await api.post('/auth/register', payload);
    localStorage.setItem('dt_token', r.data.token); setUser(r.data.user); return r.data.user;
  };
  const logout = async () => { try { await api.post('/auth/logout'); } catch {} localStorage.removeItem('dt_token'); setUser(null); };
  return <Ctx.Provider value={{ user, loading, login, logout, register }}>{children}</Ctx.Provider>;
}