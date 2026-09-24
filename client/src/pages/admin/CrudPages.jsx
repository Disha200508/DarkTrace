import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import api, { errMsg } from '../../api';
import { Badge, Card, Conf, Modal, Table, TYPE_LABEL, fmtD } from '../../components/ui';

const ENTITY_TYPES = Object.keys(TYPE_LABEL);
const toInput = (v, t) => (t === 'date' && v ? new Date(v).toISOString().slice(0, 10) : v ?? '');

function CrudPage({ title, endpoint, params = {}, columns, fields, header }) {
  const [data, setData] = useState({ items: [], total: 0 }); const [q, setQ] = useState(''); const [page, setPage] = useState(1);
  const [edit, setEdit] = useState(null); const [form, setForm] = useState({});
  const key = JSON.stringify(params);
  const load = () => api.get(endpoint, { params: { ...params, q, page } }).then((r) => setData(r.data)).catch((e) => toast.error(errMsg(e)));
  useEffect(() => { load(); }, [endpoint, key, q, page]);
  const open = (row) => { setEdit(row || {}); setForm(row ? Object.fromEntries(fields.map((f) => [f.name, toInput(row[f.name], f.type)])) : { ...params }); };
  const save = async (e) => {
    e.preventDefault();
    try { edit._id ? await api.put(`${endpoint}/${edit._id}`, form) : await api.post(endpoint, form); toast.success('Saved'); setEdit(null); load(); }
    catch (er) { toast.error(errMsg(er)); }
  };
  const del = async (row) => { if (!confirm('Delete this record?')) return; await api.delete(`${endpoint}/${row._id}`); toast.success('Deleted'); load(); };
  return (
    <Card title={`${title} (${data.total})`} right={<div className="row"><input className="inline" placeholder="Search…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} /><button className="primary sm" onClick={() => open()}>＋ Add</button></div>}>
      {header}
      <Table rows={data.items} empty="No records. Import a dataset or add one manually." cols={[...columns, { h: '', r: (r) => <span className="row"><button className="sm" onClick={() => open(r)}>Edit</button><button className="sm danger" onClick={() => del(r)}>Delete</button></span> }]} />
      <div className="pager"><button disabled={page < 2} onClick={() => setPage(page - 1)}>‹ Prev</button><span>Page {page}</span><button disabled={page * 25 >= data.total} onClick={() => setPage(page + 1)}>Next ›</button></div>
      {edit && <Modal title={edit._id ? 'Edit record' : 'Add record'} onClose={() => setEdit(null)}>
        <form className="form" onSubmit={save}>{fields.map((f) => (
          <label key={f.name}>{f.label}
            {f.options ? <select value={form[f.name] || ''} onChange={(e) => setForm({ ...form, [f.name]: e.target.value })} disabled={f.lock && edit._id}>{[['', '—'], ...f.options].map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
              : <input type={f.type || 'text'} value={form[f.name] ?? ''} required={f.required} disabled={f.lock && edit._id} onChange={(e) => setForm({ ...form, [f.name]: e.target.value })} />}
          </label>))}<button className="primary">Save</button></form></Modal>}
    </Card>
  );
}

export function EntitiesPage() {
  const [sp] = useSearchParams(); const type = sp.get('type');
  return <CrudPage key={type || 'all'} title={type ? TYPE_LABEL[type] + 's' : 'Identifiers'} endpoint="/admin/entities" params={type ? { type } : {}}
    columns={[{ h: 'Type', r: (e) => <Badge>{TYPE_LABEL[e.type]}</Badge> }, { h: 'Value', r: (e) => <code>{e.value}</code> }, { h: 'Label', r: (e) => e.label || '—' }, { h: 'Category', r: (e) => e.category || '—' }, { h: 'First seen', r: (e) => fmtD(e.firstSeen) }, { h: 'Confidence', r: (e) => <Conf v={e.confidence} /> }, { h: 'Sources', r: (e) => e.sourceIds?.length || 0 }]}
    fields={[{ name: 'type', label: 'Type', options: ENTITY_TYPES.map((t) => [t, TYPE_LABEL[t]]), required: true, lock: true }, { name: 'value', label: 'Value', required: true, lock: true }, { name: 'label', label: 'Label / display name' }, { name: 'category', label: 'Category' }, { name: 'status', label: 'Status' },
      { name: 'confidence', label: 'Confidence (0–100)', type: 'number' }, { name: 'firstSeen', label: 'First observed', type: 'date' }, { name: 'lastSeen', label: 'Last observed', type: 'date' }]} />;
}

export const RelationshipsPage = () => (
  <CrudPage title="Relationships" endpoint="/admin/relationships"
    columns={[{ h: 'From', r: (r) => <code>{r.from?.label || r.from?.value}</code> }, { h: 'Type', r: (r) => <Badge tone="blue">{r.type}</Badge> }, { h: 'To', r: (r) => <code>{r.to?.label || r.to?.value}</code> }, { h: 'Confidence', r: (r) => <Conf v={r.confidence} /> }, { h: 'Method', r: (r) => r.method }, { h: 'Status', r: (r) => <Badge tone={r.status === 'proposed' ? 'amber' : r.status === 'rejected' ? 'red' : 'green'}>{r.status}</Badge> }]}
    fields={[{ name: 'fromType', label: 'From type', options: ENTITY_TYPES.map((t) => [t, TYPE_LABEL[t]]) }, { name: 'fromValue', label: 'From value' }, { name: 'toType', label: 'To type', options: ENTITY_TYPES.map((t) => [t, TYPE_LABEL[t]]) }, { name: 'toValue', label: 'To value' },
      { name: 'type', label: 'Relationship type', required: true }, { name: 'confidence', label: 'Confidence (0–100)', type: 'number' }, { name: 'status', label: 'Status', options: [['confirmed', 'confirmed'], ['proposed', 'proposed'], ['rejected', 'rejected']] }]} />
);

export const SourcesPage = () => (
  <CrudPage title="Data Sources" endpoint="/admin/sources"
    columns={[{ h: 'Name', r: (s) => s.name }, { h: 'Type', r: (s) => s.type }, { h: 'Reliability', r: (s) => <Badge>{s.reliability}</Badge> }, { h: 'Last import', r: (s) => fmtD(s.lastImportAt) }]}
    fields={[{ name: 'name', label: 'Name', required: true }, { name: 'type', label: 'Type' }, { name: 'reliability', label: 'Reliability', options: ['A - Reliable', 'B - Usually reliable', 'C - Fairly reliable', 'D - Not usually reliable', 'unrated'].map((x) => [x, x]) }, { name: 'description', label: 'Description' }]} />
);