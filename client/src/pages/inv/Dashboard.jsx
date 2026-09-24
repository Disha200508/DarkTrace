import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import { Card, Stat, Table, fmt } from '../../components/ui';

export function InvDashboard() {
  const [d, setD] = useState(null); const nav = useNavigate();
  useEffect(() => { api.get('/inv/dashboard').then((r) => setD(r.data)); }, []);
  if (!d) return <div className="boot">Loading…</div>;
  return (
    <>
      <div className="hero">
        <div><h1>Investigator Dashboard</h1><p>Search any identifier to correlate every related actor, wallet, account and piece of evidence.</p></div>
        <button className="primary xl" onClick={() => nav('/inv/search')}>START NEW INVESTIGATION</button>
      </div>
      <div className="stats">
        <Stat label="Active Investigations" value={d.active} /><Stat label="Saved Investigations" value={d.saved} />
        <Stat label="New Alerts" value={d.alerts} tone={d.alerts ? 'warn' : ''} /><Stat label="Reports Generated" value={d.reports} />
      </div>
      <Card title="Recent Searches">
        <Table rows={d.recent} empty="No searches yet — start your first investigation."
          cols={[{ h: 'Query', r: (r) => <code>{r.query}</code> }, { h: 'Type', r: (r) => r.type }, { h: 'Results', r: (r) => r.resultCount }, { h: 'When', r: (r) => fmt(r.createdAt) }]}
          onRow={(r) => nav(`/inv/result?type=${r.type}&q=${encodeURIComponent(r.query)}`)} />
      </Card>
    </>
  );
}