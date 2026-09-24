import axios from 'axios';
const api = axios.create({ baseURL: '/api' });
api.interceptors.request.use((c) => { const t = localStorage.getItem('dt_token'); if (t) c.headers.Authorization = `Bearer ${t}`; return c; });
api.interceptors.response.use((r) => r, (e) => {
  if (e.response?.status === 401 && !e.config.url.includes('/auth/login')) { localStorage.removeItem('dt_token'); window.location.href = '/login'; }
  return Promise.reject(e);
});
export const errMsg = (e) => e.response?.data?.error || e.message || 'Request failed';

export async function download(url, filename) {
  const r = await api.get(url, { responseType: 'blob' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(r.data); a.download = filename; a.click(); URL.revokeObjectURL(a.href);
}
export default api;