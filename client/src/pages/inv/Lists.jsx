import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import api, { errMsg } from '../../api';
import { Badge, Card, Sev, Table, TYPE_LABEL, fmt, fmtD } from '../../components/ui';

const useList = (url, deps = []) => { const [items, set] = useState(null); const load = () => api.get(url).then((r) => set(r.data.items)).catch((e) => toast.error(errMsg(e))); useEffect(() => { load(); }, deps); return [items, load]; };

export function InvestigationsList() {
  const [sp] = useSearchParams(); const nav = useNavigate(); const bucket = sp.get('bucket') || 'active'; const tab = sp.get('tab');
  const [items] = useList(`/inv/investigations?bucket=${bucket}`, [bucket]);
  return <Card title={`${bucket[0].toUpperCase() + bucket.slice(1)} investigations${tab ? ` — open in ${tab}` : ''}`}>
    <Table rows={items || []} empty="No investigations here yet." onRow={(i) => nav(`/inv/investigation/${i._id}${tab ? `?tab=${tab}` : ''}`)} cols={[
      { h: 'ID', r: (i) => <code>{i.invId}</code> }, { h: 'Name', r: (i) => i.name }, { h: 'Search', r: (i) => `${i.search.type}: ${i.search.query}` }, { h: 'Priority', r: (i) => <Badge tone={['high', 'critical'].includes(i.priority) ? 'red' : 'gray'}>{i.priority}</Badge> },
      { h: 'Status', r: (i) => <Badge tone="blue">{i.status}</Badge> }, { h: 'Tags', r: (i) => i.tags.join(', ') }, { h: 'Updated', r: (i) => fmt(i.updatedAt) }]} /></Card>;
}

export function HistoryPage() {
  const nav = useNavigate(); const [items] = useList('/inv/history');
  return <Card title="Search History"><Table rows={items || []} empty="No searches yet." cols={[
    { h: 'Query', r: (s) => <code>{s.query}</code> }, { h: 'Type', r: (s) => s.type }, { h: 'Date/time', r: (s) => fmt(s.createdAt) }, { h: 'Investigation', r: (s) => s.investigation ? `${s.investigation.invId} · ${s.investigation.name}` : '—' }, { h: 'Results', r: (s) => s.resultCount }]}
    onRow={(s) => nav(s.investigation ? `/inv/investigation/${s.investigation._id}` : `/inv/result?type=${s.type}&q=${encodeURIComponent(s.query)}`)} /></Card>;
}

export function AlertsPage() {
  const nav = useNavigate(); const [items, load] = useList('/inv/alerts');
  return <Card title="Alerts"><Table rows={items || []} empty="No alerts." cols={[
    { h: 'Severity', r: (a) => <Sev v={a.severity} /> }, { h: 'Type', r: (a) => a.kind.replace(/_/g, ' ') }, { h: 'Message', r: (a) => <span style={{ opacity: a.read ? 0.55 : 1 }}>{a.message}</span> }, { h: 'Investigation', r: (a) => a.investigation?.invId || '—' }, { h: 'When', r: (a) => fmt(a.createdAt) }]}
    onRow={async (a) => { await api.patch(`/inv/alerts/${a._id}/read`); load(); if (a.investigation) nav(`/inv/investigation/${a.investigation._id}`); }} /></Card>;
}

export function MyReports() {
  const nav = useNavigate(); const [items] = useList('/inv/reports');
  return <Card title="Reports"><Table rows={items || []} empty="No reports generated yet." onRow={(r) => nav(`/inv/reports/${r.reportId}`)} cols={[
    { h: 'Report ID', r: (r) => <code>{r.reportId}</code> }, { h: 'Investigation', r: (r) => r.investigation?.name }, { h: 'Date', r: (r) => fmt(r.createdAt) }, { h: 'Exported as', r: (r) => r.formats.join(', ').toUpperCase() || '—' }]} /></Card>;
}

export function EntityBrowser() {
  const nav = useNavigate(); const [q, setQ] = useState(''); const [items] = useList(`/inv/entities?type=actor&q=${encodeURIComponent(q)}`, [q]);
  return <Card title="Actors" right={<input className="inline" placeholder="Filter…" value={q} onChange={(e) => setQ(e.target.value)} />}><Table rows={items || []} empty="No actor records in the database." onRow={(a) => nav(`/inv/result?type=actor&q=${encodeURIComponent(a.value)}`)} cols={[
    { h: 'Actor', r: (a) => a.label || a.value }, { h: 'ID', r: (a) => <code>{a.value}</code> }, { h: 'Category', r: (a) => a.category || '—' }, { h: 'First seen', r: (a) => fmtD(a.firstSeen) }, { h: 'Last seen', r: (a) => fmtD(a.lastSeen) }]} /></Card>;
}