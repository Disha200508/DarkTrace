import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';
import { useTheme } from '../theme';

const INV = [
  { label: 'Dashboard', to: '/inv' },
  { label: 'New Search', to: '/inv/search' },
  { group: 'Investigations', items: [{ label: 'Active', to: '/inv/investigations?bucket=active' }, { label: 'Saved', to: '/inv/investigations?bucket=saved' }, { label: 'Closed', to: '/inv/investigations?bucket=closed' }] },
  { group: 'Intelligence', items: [{ label: 'Actors', to: '/inv/actors' }, { label: 'Relationship Graph', to: '/inv/investigations?bucket=active&tab=graph' }, { label: 'Timeline', to: '/inv/investigations?bucket=active&tab=timeline' }, { label: 'Evidence', to: '/inv/investigations?bucket=active&tab=evidence' }] },
  { label: 'Alerts', to: '/inv/alerts' }, { label: 'Reports', to: '/inv/reports' }, { label: 'Search History', to: '/inv/history' },
];
const ADMIN = [
  { label: 'Dashboard', to: '/admin' },
  { label: 'Investigators', to: '/admin/investigators' },
  { label: 'Login Activity', to: '/admin/login-activity' },
  { group: 'Intelligence', items: [{ label: 'Actors', to: '/admin/entities?type=actor' }, { label: 'Identifiers', to: '/admin/entities' }, { label: 'Relationships', to: '/admin/relationships' }, { label: 'Infrastructure', to: '/admin/entities?type=infrastructure' }, { label: 'Blockchain', to: '/admin/entities?type=wallet' }] },
  { group: 'Data Management', items: [{ label: 'Data Sources', to: '/admin/sources' }, { label: 'Import Data', to: '/admin/import' }, { label: 'Data Quality', to: '/admin/quality' }] },
  { group: 'Analysis Engine', items: [
    { label: 'AI Model Governance', to: '/admin/analysis?tab=governance' },
    { label: 'Live Model Playground', to: '/admin/analysis?tab=tester' },
    { label: 'Correlation', to: '/admin/analysis?tab=correlation' },
    { label: 'Persona Analysis', to: '/admin/analysis?tab=persona' },
    { label: 'Automated Jobs', to: '/admin/analysis?tab=jobs' }
  ] },
  { label: 'Investigations', to: '/admin/investigations' }, { label: 'Alerts', to: '/admin/alerts' }, { label: 'Reports', to: '/admin/reports' },
  { label: 'Audit Logs', to: '/admin/audit' }, { label: 'System Health', to: '/admin/health' },
];

export default function Layout({ portal, children }) {
  const { user, logout } = useAuth(); const nav = useNavigate(); const loc = useLocation();
  const { theme, toggleTheme } = useTheme();
  const items = portal === 'admin' ? ADMIN : INV;
  const isActive = (to) => {
    const [path, search] = to.split('?');
    if (loc.pathname !== path) return false;
    if (!search) return !loc.search;
    const toParams = new URLSearchParams(search);
    const currentParams = new URLSearchParams(loc.search);
    for (const [k, v] of toParams.entries()) {
      if (currentParams.get(k) !== v) return false;
    }
    if (!toParams.has('tab') && currentParams.has('tab')) return false;
    if (!toParams.has('type') && currentParams.has('type')) return false;
    return true;
  };
  const NavItem = ({ it }) => <Link to={it.to} className={isActive(it.to) ? 'nav active' : 'nav'}>{it.label}</Link>;
  return (
    <div className="shell">
      <aside>
        <div className="brand"><span className="logo">◈</span><div><b>DarkTrace</b><small>{portal === 'admin' ? 'ADMIN CONSOLE' : 'INVESTIGATOR'}</small></div></div>
        <nav>
          {items.map((it) => it.group ? (
            <div key={it.group} className="group"><div className="group-h">{it.group}</div>{it.items.map((s) => <NavItem key={s.to} it={s} />)}</div>
          ) : <NavItem key={it.to} it={it} />)}
        </nav>
      </aside>
      <div className="main">
        <header className="topbar">
          {portal === 'inv' && <button className="primary sm" onClick={() => nav('/inv/search')}>＋ New Investigation</button>}
          <div className="spacer" />
          <button className="theme-toggle" onClick={toggleTheme} title="Click to toggle Light/Dark Mode">
            {theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
          </button>
          <div className="chip"><span className="dot" />{user.fullName} · {user.role.replace('_', ' ')}</div>
          <button className="ghost" onClick={async () => { await logout(); nav(portal === 'admin' ? '/admin/login' : '/login'); }}>Logout</button>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}