import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './auth';
import Layout from './components/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import { InvDashboard } from './pages/inv/Dashboard';
import NewSearch from './pages/inv/NewSearch';
import Workspace from './pages/inv/Workspace';
import Report from './pages/inv/Report';
import { InvestigationsList, HistoryPage, AlertsPage, MyReports, EntityBrowser } from './pages/inv/Lists';
import { AdminDashboard, Investigators, LoginActivity, ImportData, DataQuality, Analysis, AuditLogs, AdminInvestigations, AdminReports, AdminAlerts, SystemHealth } from './pages/admin/AdminPages';
import { EntitiesPage, RelationshipsPage, SourcesPage } from './pages/admin/CrudPages';

const Guard = ({ admin, children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="boot">Loading…</div>;
  if (!user) return <Navigate to={admin ? '/admin/login' : '/login'} replace />;
  if ((user.role === 'admin') !== !!admin) return <Navigate to={user.role === 'admin' ? '/admin' : '/inv'} replace />;
  return <Layout portal={admin ? 'admin' : 'inv'}>{children}</Layout>;
};

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login portal="investigator" mode="login" />} />
      <Route path="/signup" element={<Login portal="investigator" mode="signup" />} />
      <Route path="/register" element={<Login portal="investigator" mode="signup" />} />
      <Route path="/admin/login" element={<Login portal="admin" mode="login" />} />

      <Route path="/inv" element={<Guard><InvDashboard /></Guard>} />
      <Route path="/inv/search" element={<Guard><NewSearch /></Guard>} />
      <Route path="/inv/result" element={<Guard><Workspace /></Guard>} />
      <Route path="/inv/investigation/:invId" element={<Guard><Workspace /></Guard>} />
      <Route path="/inv/investigations" element={<Guard><InvestigationsList /></Guard>} />
      <Route path="/inv/actors" element={<Guard><EntityBrowser /></Guard>} />
      <Route path="/inv/alerts" element={<Guard><AlertsPage /></Guard>} />
      <Route path="/inv/reports" element={<Guard><MyReports /></Guard>} />
      <Route path="/inv/reports/:rid" element={<Guard><Report /></Guard>} />
      <Route path="/inv/history" element={<Guard><HistoryPage /></Guard>} />

      <Route path="/admin" element={<Guard admin><AdminDashboard /></Guard>} />
      <Route path="/admin/investigators" element={<Guard admin><Investigators /></Guard>} />
      <Route path="/admin/login-activity" element={<Guard admin><LoginActivity /></Guard>} />
      <Route path="/admin/entities" element={<Guard admin><EntitiesPage /></Guard>} />
      <Route path="/admin/relationships" element={<Guard admin><RelationshipsPage /></Guard>} />
      <Route path="/admin/sources" element={<Guard admin><SourcesPage /></Guard>} />
      <Route path="/admin/import" element={<Guard admin><ImportData /></Guard>} />
      <Route path="/admin/quality" element={<Guard admin><DataQuality /></Guard>} />
      <Route path="/admin/analysis" element={<Guard admin><Analysis /></Guard>} />
      <Route path="/admin/investigations" element={<Guard admin><AdminInvestigations /></Guard>} />
      <Route path="/admin/alerts" element={<Guard admin><AdminAlerts /></Guard>} />
      <Route path="/admin/reports" element={<Guard admin><AdminReports /></Guard>} />
      <Route path="/admin/audit" element={<Guard admin><AuditLogs /></Guard>} />
      <Route path="/admin/health" element={<Guard admin><SystemHealth /></Guard>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}