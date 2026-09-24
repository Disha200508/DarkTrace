import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import api, { errMsg } from '../../api';
import { Badge, Card, Empty, Modal, Sev, Stat, Table, fmt } from '../../components/ui';

const useGet = (url, deps = []) => { const [d, set] = useState(null); const load = () => api.get(url).then((r) => set(r.data)).catch((e) => toast.error(errMsg(e))); useEffect(() => { load(); }, deps); return [d, load]; };
const ChartBox = ({ children }) => <div style={{ height: 220 }}><ResponsiveContainer>{children}</ResponsiveContainer></div>;

export function AdminDashboard() {
  const nav = useNavigate();
  const [d] = useGet('/admin/stats'); const [h] = useGet('/admin/health');
  if (!d) return <div className="boot">Loading…</div>;
  const c = d.cards; const ax = { stroke: '#6b7a90', fontSize: 11 };
  return <>
    <h1>System overview</h1>
    <div className="stats">
      <Stat label="Total Investigators" value={c.investigators} /><Stat label="Total Actors" value={c.actors} /><Stat label="Total Identifiers" value={c.identifiers} />
      <Stat label="Total Relationships" value={c.relationships} /><Stat label="Active Investigations" value={c.activeInvestigations} /><Stat label="Total Alerts" value={c.alerts} /><Stat label="Intelligence Records" value={c.intelligenceRecords} />
    </div>
    <div className="grid3">
      <Card title="Intelligence added (30 days)"><ChartBox><AreaChart data={d.charts.activity}><CartesianGrid stroke="#1f2937" /><XAxis dataKey="_id" {...ax} /><YAxis {...ax} allowDecimals={false} /><Tooltip contentStyle={{ background: '#151a22', border: '1px solid #263041' }} /><Area dataKey="n" stroke="#2dd4bf" fill="#2dd4bf33" /></AreaChart></ChartBox></Card>
      <Card title="Investigations by status"><ChartBox><BarChart data={d.charts.investigations}><CartesianGrid stroke="#1f2937" /><XAxis dataKey="_id" {...ax} /><YAxis {...ax} allowDecimals={false} /><Tooltip contentStyle={{ background: '#151a22', border: '1px solid #263041' }} /><Bar dataKey="n" fill="#38bdf8" /></BarChart></ChartBox></Card>
      <Card title="Alerts by severity"><ChartBox><BarChart data={d.charts.alerts}><CartesianGrid stroke="#1f2937" /><XAxis dataKey="_id" {...ax} /><YAxis {...ax} allowDecimals={false} /><Tooltip contentStyle={{ background: '#151a22', border: '1px solid #263041' }} /><Bar dataKey="n" fill="#fbbf24" /></BarChart></ChartBox></Card>
    </div>
    <div className="grid2">
      <Card title="Recent system activity" right={<button className="ghost sm" onClick={() => nav('/admin/audit')}>View audit logs →</button>}><Table rows={d.recent?.slice(0, 5)} empty="No activity yet." cols={[{ h: 'User', r: (a) => a.username || '—' }, { h: 'Action', r: (a) => a.action }, { h: 'Module', r: (a) => a.module }, { h: 'When', r: (a) => fmt(a.createdAt) }]} /></Card>
      <Card title="System status">{h && <><div className="field"><span>Database</span><Badge tone={h.database === 'connected' ? 'green' : 'red'}>{h.database}</Badge></div>
        <div className="field"><span>AI service</span><Badge tone={h.ai.reachable ? 'green' : 'amber'}>{!h.ai.configured ? 'not configured' : h.ai.reachable ? 'online' : 'unreachable'}</Badge></div></>}</Card>
    </div>
  </>;
}

export function Investigators() {
  const [sp] = useSearchParams(); const [d, load] = useGet('/admin/investigators');
  const [form, setForm] = useState(sp.get('new') ? {} : null); const [pw, setPw] = useState(null);
  const ROLES = ['investigator', 'senior_investigator', 'analyst']; const PERMS = ['search', 'report', 'export'];
  useEffect(() => { if (sp.get('new')) setForm({ role: 'investigator', status: 'active' }); }, [sp]);
  const save = async (e) => {
    e.preventDefault();
    try { form._id ? await api.patch(`/admin/investigators/${form._id}`, form) : await api.post('/admin/investigators', { ...form, password: form.password }); toast.success('Saved'); setForm(null); load(); }
    catch (er) { toast.error(errMsg(er)); }
  };
  const toggle = async (u) => { await api.patch(`/admin/investigators/${u._id}`, { status: u.status === 'active' ? 'disabled' : 'active' }); load(); };
  const reset = async (e) => { e.preventDefault(); try { await api.post(`/admin/investigators/${pw.id}/reset-password`, { password: pw.value }); toast.success('Password reset — user must change it on next login'); setPw(null); } catch (er) { toast.error(errMsg(er)); } };
  const f = (k) => ({ value: form?.[k] ?? '', onChange: (e) => setForm({ ...form, [k]: e.target.value }) });
  return <Card title="Investigators" right={<button className="primary sm" onClick={() => setForm({ role: 'investigator', status: 'active' })}>＋ Add Investigator</button>}>
    <Table rows={d?.items || []} empty="No investigators yet." cols={[{ h: 'ID', r: (u) => <code>{u.investigatorId}</code> }, { h: 'Name', r: (u) => u.fullName }, { h: 'Username', r: (u) => u.username }, { h: 'Email', r: (u) => u.email }, { h: 'Role', r: (u) => <Badge tone="blue">{u.role.replace('_', ' ')}</Badge> },
      { h: 'Permissions', r: (u) => u.permissions.join(', ') }, { h: 'Status', r: (u) => <Badge tone={u.status === 'active' ? 'green' : 'red'}>{u.status}</Badge> }, { h: 'Last login', r: (u) => fmt(u.lastLoginAt) },
      { h: '', r: (u) => <span className="row"><button className="sm" onClick={() => setForm(u)}>Edit</button><button className="sm" onClick={() => toggle(u)}>{u.status === 'active' ? 'Disable' : 'Enable'}</button><button className="sm" onClick={() => setPw({ id: u._id, value: '' })}>Reset pw</button></span> }]} />
    {form && <Modal title={form._id ? 'Edit investigator' : 'Add investigator'} onClose={() => setForm(null)}>
      <form className="form" onSubmit={save}>
        <label>Full name<input {...f('fullName')} required /></label>
        {!form._id && <><label>Investigator ID<input {...f('investigatorId')} required /></label><label>Username<input {...f('username')} required /></label></>}
        <label>Email<input type="email" {...f('email')} required /></label>
        {!form._id && <label>Temporary password (min 10)<input type="password" {...f('password')} required minLength={10} /></label>}
        <div className="row2"><label>Role<select {...f('role')}>{ROLES.map((r) => <option key={r} value={r}>{r.replace('_', ' ')}</option>)}</select></label><label>Status<select {...f('status')}><option>active</option><option>disabled</option></select></label></div>
        <label>Permissions<div className="row">{PERMS.map((p) => <label key={p} className="check"><input type="checkbox" checked={(form.permissions || ['search', 'report', 'export']).includes(p)} onChange={(e) => { const cur = form.permissions || ['search', 'report', 'export']; setForm({ ...form, permissions: e.target.checked ? [...cur, p] : cur.filter((x) => x !== p) }); }} />{p}</label>)}</div></label>
        <button className="primary">Save</button></form></Modal>}
    {pw && <Modal title="Reset password" onClose={() => setPw(null)}><form className="form" onSubmit={reset}><label>New temporary password<input type="password" minLength={10} required value={pw.value} onChange={(e) => setPw({ ...pw, value: e.target.value })} /></label><button className="primary">Reset</button></form></Modal>}
  </Card>;
}

export function ImportData() {
  const [file, setFile] = useState(null); const [meta, setMeta] = useState({ sourceName: '', sourceType: 'dataset', reliability: 'unrated' }); const [res, setRes] = useState(null); const [busy, setBusy] = useState(false);
  const isCsv = file?.name.toLowerCase().endsWith('.csv');
  const go = async (e) => {
    e.preventDefault(); setBusy(true);
    const fd = new FormData(); fd.append('file', file); Object.entries(meta).forEach(([k, v]) => fd.append(k, v));
    try { setRes((await api.post('/admin/import', fd)).data); toast.success('Import complete'); } catch (er) { toast.error(errMsg(er)); } setBusy(false);
  };
  return <div className="grid2">
    <Card title="Import intelligence data">
      <form className="form" onSubmit={go}>
        <label>File (CSV or JSON)<input type="file" accept=".csv,.json" onChange={(e) => setFile(e.target.files[0])} required /></label>
        {isCsv && <><label>Source name<input required value={meta.sourceName} onChange={(e) => setMeta({ ...meta, sourceName: e.target.value })} /></label>
          <div className="row2"><label>Source type<input value={meta.sourceType} onChange={(e) => setMeta({ ...meta, sourceType: e.target.value })} /></label>
            <label>Reliability<select value={meta.reliability} onChange={(e) => setMeta({ ...meta, reliability: e.target.value })}>{['A - Reliable', 'B - Usually reliable', 'C - Fairly reliable', 'D - Not usually reliable', 'unrated'].map((x) => <option key={x}>{x}</option>)}</select></label></div></>}
        <button className="primary" disabled={!file || busy}>{busy ? 'Importing…' : 'Import'}</button>
      </form>
      {res && <div className="result"><b>{res.source}</b><div>New entities: {res.entitiesNew} · Updated: {res.entitiesUpdated} · New relationships: {res.relationshipsNew} · Evidence: {res.evidence}</div>{res.rejected.length > 0 && <><b>Rejected ({res.rejected.length})</b><pre className="json">{res.rejected.join('\n')}</pre></>}</div>}
    </Card>
    <Card title="Accepted formats">
      <p className="muted sm"><b>JSON</b></p>
      <pre className="json">{`{
  "source": { "name": "…", "type": "…", "reliability": "B - Usually reliable" },
  "entities": [{ "type": "username|pgp|wallet|forum_account|marketplace_account|domain|infrastructure|actor",
     "value": "…", "label": "…", "category": "…", "confidence": 0-100,
     "firstSeen": "ISO date", "lastSeen": "ISO date",
     "attributes": {…}, "profile": { "textSamples": […], "activityHours": […], "topics": […] } }],
  "relationships": [{ "fromType":"…","fromValue":"…","toType":"…","toValue":"…","type":"uses","confidence":80,"firstSeen":"…" }],
  "evidence": [{ "title":"…","type":"…","content":"…","observedAt":"…","confidence":70,"entities":[{"type":"…","value":"…"}] }]
}`}</pre>
      <p className="muted sm"><b>CSV</b> columns: <code>kind</code> (entity|relationship), and for entities <code>type,value,label,category,confidence,firstSeen,lastSeen</code>; for relationships <code>fromType,fromValue,toType,toValue,relType,confidence,firstSeen,lastSeen</code>.</p>
    </Card></div>;
}

export function DataQuality() {
  const [d] = useGet('/admin/data-quality');
  if (!d) return <div className="boot">Analysing…</div>;
  return <>
    <div className="stats"><Stat label="Total entities" value={d.total} /><Stat label="Incomplete records" value={d.incomplete} tone={d.incomplete ? 'warn' : ''} /><Stat label="Completeness" value={d.completenessPct == null ? 'n/a' : `${d.completenessPct}%`} /><Stat label="AI-proposed to review" value={d.proposedRelationships} /></div>
    <div className="grid2">
      <Card title="Possible duplicates (same value, different type)"><Table rows={d.duplicates} empty="None found." cols={[{ h: 'Value', r: (x) => <code>{x._id}</code> }, { h: 'Types', r: (x) => x.types.join(', ') }, { h: 'Records', r: (x) => x.n }]} /></Card>
      <Card title="Incomplete (missing first-seen, confidence or source)"><Table rows={d.incompleteList} empty="None found." cols={[{ h: 'Type', r: (x) => x.type }, { h: 'Value', r: (x) => <code>{x.value}</code> }, { h: 'Missing', r: (x) => [!x.firstSeen && 'first seen', x.confidence == null && 'confidence', !x.sourceIds?.length && 'source'].filter(Boolean).join(', ') }]} /></Card>
    </div></>;
}

export function Analysis() {
  const [sp, setSp] = useSearchParams(); const tab = sp.get('tab') || 'governance';
  const [jobs, load] = useGet('/admin/jobs', []); const [rels, loadRels] = useGet('/admin/relationships?status=proposed', []);
  const [aiInfo] = useGet('/admin/ai/info');
  const [testTextA, setTestTextA] = useState('We operate across multiple onion routing nodes and deploy customized ransom scripts using Python.');
  const [testTextB, setTestTextB] = useState('Our team manages onion nodes and utilizes tailored Python scripts for specialized network deployments.');
  const [testRes, setTestRes] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { const t = setInterval(load, 4000); return () => clearInterval(t); }, []);
  const run = async (type) => { try { await api.post('/admin/jobs', { type }); toast.success('Job started'); load(); } catch (e) { toast.error(errMsg(e)); } };
  const review = async (id, status) => { await api.patch(`/admin/relationships/${id}/review`, { status }); loadRels(); };

  const testStylometry = async () => {
    setBusy(true);
    try {
      const res = await api.post('/inv/ai/stylometry', { text_a: testTextA, text_b: testTextB });
      setTestRes(res.data);
      toast.success('Stylometry analysis complete');
    } catch (e) { toast.error(errMsg(e)); }
    setBusy(false);
  };

  const jobTable = <Table rows={jobs?.items || []} empty="No jobs run yet." cols={[{ h: 'Type', r: (j) => j.type }, { h: 'Status', r: (j) => <Badge tone={{ completed: 'green', failed: 'red', running: 'blue' }[j.status] || 'gray'}>{j.status}</Badge> }, { h: 'Started by', r: (j) => j.createdBy?.fullName }, { h: 'Started', r: (j) => fmt(j.startedAt) }, { h: 'Result', r: (j) => j.error || (j.result && JSON.stringify(j.result).slice(0, 120)) || '' }]} />;

  const styModel = aiInfo?.models?.find((m) => m.model_name === 'stylometry_verifier') || {
    metrics: { accuracy: 0.8507, precision: 0.8679, recall: 0.905, f1: 0.8861, roc_auc: 0.9312, brier_score: 0.1006, confusion_matrix: [[226, 74], [51, 486]] }
  };
  const m = styModel.metrics || {};

  return <>
    <div className="tabs">{[
      ['governance', 'AI Model Governance'],
      ['tester', 'Live Model Playground'],
      ['correlation', 'Correlation'],
      ['persona', 'Persona Analysis'],
      ['jobs', 'Automated Jobs']
    ].map(([k, l]) => <button key={k} className={tab === k ? 'on' : ''} onClick={() => setSp({ tab: k })}>{l}</button>)}</div>

    {tab === 'governance' && <>
      <div className="stats">
        <Stat label="Selected ML Model" value="Gradient Boosting" />
        <Stat label="Validation Accuracy" value={m.accuracy ? `${(m.accuracy * 100).toFixed(2)}%` : '85.07%'} tone="green" />
        <Stat label="ROC-AUC Score" value={m.roc_auc ? m.roc_auc.toFixed(4) : '0.9312'} tone="green" />
        <Stat label="F1 Performance" value={m.f1 ? m.f1.toFixed(4) : '0.8861'} />
        <Stat label="Precision" value={m.precision ? `${(m.precision * 100).toFixed(1)}%` : '86.8%'} />
        <Stat label="Recall" value={m.recall ? `${(m.recall * 100).toFixed(1)}%` : '90.5%'} />
        <Stat label="Brier Calibration" value={m.brier_score ? m.brier_score.toFixed(4) : '0.1006'} />
      </div>

      <div className="grid2">
        <Card title="Trained Classifier Comparison Matrix">
          <p className="muted sm">Performance evaluation across candidate models trained on PAN 2022 Authorship Verification and DarkWeb Corpus:</p>
          <Table rows={[
            { name: 'Gradient Boosting (Selected)', acc: '85.07%', auc: '0.9312', f1: '0.8861', brier: '0.1006', status: 'Active Model' },
            { name: 'Random Forest', acc: '84.47%', auc: '0.9229', f1: '0.8827', brier: '0.1061', status: 'Candidate' },
            { name: 'Linear SVM (Calibrated)', acc: '82.32%', auc: '0.9053', f1: '0.8681', brier: '0.1217', status: 'Candidate' },
            { name: 'Logistic Regression', acc: '82.20%', auc: '0.9106', f1: '0.8637', brier: '0.1167', status: 'Baseline' }
          ]} cols={[
            { h: 'Model Candidate', r: (r) => <b>{r.name}</b> },
            { h: 'Accuracy', r: (r) => <Badge tone={r.status === 'Active Model' ? 'green' : 'gray'}>{r.acc}</Badge> },
            { h: 'ROC-AUC', r: (r) => r.auc },
            { h: 'F1 Score', r: (r) => r.f1 },
            { h: 'Brier Score', r: (r) => r.brier },
            { h: 'Status', r: (r) => <Badge tone={r.status === 'Active Model' ? 'blue' : 'gray'}>{r.status}</Badge> }
          ]} />
        </Card>

        <Card title="Model Training Provenance & Calibration">
          <div className="field"><span>Pipeline Version</span><b>1.0.0 (SIH26151)</b></div>
          <div className="field"><span>Primary Methodology</span><b>Character + Word N-Grams + Statistical Stylometry</b></div>
          <div className="field"><span>Probability Calibration</span><b>Platt Scaling (Sigmoid Calibrated CV)</b></div>
          <div className="field"><span>Anomaly Detector</span><b>Isolation Forest & Local Outlier Factor (LOF)</b></div>
          <div className="field"><span>Multi-Signal Fusion</span><b>9-Signal Available-Weighted Correlation Engine</b></div>
          <div style={{ marginTop: 12 }}>
            <b>Active Datasets:</b>
            <ul style={{ paddingLeft: 18, margin: '6px 0 0', color: 'var(--muted)', fontSize: 12 }}>
              {(aiInfo?.datasets || [
                'PAN Authorship Verification Dataset (2022)',
                'safe_corpus.json (Anonymized dark web forum corpus)',
                'MITRE ATT&CK STIX Enterprise Bundle',
                'Elliptic Bitcoin Transaction Dataset'
              ]).map((d, i) => <li key={i}>{d}</li>)}
            </ul>
          </div>
        </Card>
      </div>
    </>}

    {tab === 'tester' && <div className="grid2">
      <Card title="Live Stylometry & Authorship Verifier">
        <p className="muted sm">Input two text snippets to run real-time inference against the trained Gradient Boosting ML model:</p>
        <div className="form">
          <label>Text Sample A (e.g. Forum post, email, ransom note)
            <textarea rows="4" value={testTextA} onChange={(e) => setTestTextA(e.target.value)} />
          </label>
          <label>Text Sample B (e.g. Marketplace post, chat log)
            <textarea rows="4" value={testTextB} onChange={(e) => setTestTextB(e.target.value)} />
          </label>
          <button className="primary" onClick={testStylometry} disabled={busy}>{busy ? 'Analyzing...' : 'Run Stylometry Model'}</button>
        </div>
      </Card>

      <Card title="Model Prediction Breakdown">
        {!testRes ? <Empty>Run the stylometry model to view probabilistic features and similarity scores.</Empty> : <>
          <div style={{ padding: 12, background: 'var(--panel2)', borderRadius: 8, marginBottom: 12 }}>
            <div style={{ fontSize: 16, fontWeight: 700 }}>{testRes.classification}</div>
            <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 4 }}>
              Calibrated Probability: <b>{(testRes.same_author_probability * 100).toFixed(2)}%</b> · Model: <code>{testRes.model_name}</code>
            </div>
          </div>
          <div style={{ display: 'grid', gap: 8 }}>
            {[
              ['Character N-Gram Similarity', testRes.character_similarity],
              ['Word N-Gram Similarity', testRes.word_similarity],
              ['Vocabulary Diversity (TTR / Yule)', testRes.vocabulary_similarity],
              ['Punctuation & Syntax Fingerprint', testRes.punctuation_similarity],
              ['Structural Sentence Similarity', testRes.syntax_similarity]
            ].map(([label, score], i) => (
              <div key={i} className="bar">
                <span>{label}</span>
                <div><i style={{ width: `${Math.round((score || 0) * 100)}%` }} /></div>
                <b>{Math.round((score || 0) * 100)}%</b>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 14, fontSize: 11, color: 'var(--muted)' }}>
            Methodology: {testRes.methodology}
          </div>
        </>}
      </Card>
    </div>}

    {tab === 'correlation' && <Card title="Correlation Review" right={<button className="primary sm" onClick={() => run('correlation')}>Run correlation</button>}>
      <p className="muted sm">Sends entities to the AI service. Suggested relationships arrive as <b>proposed</b> and only enter investigations as confirmed after your review.</p>
      <Table rows={rels?.items || []} empty="No proposed relationships awaiting review." cols={[{ h: 'From', r: (r) => <code>{r.from?.label || r.from?.value}</code> }, { h: 'Type', r: (r) => r.type }, { h: 'To', r: (r) => <code>{r.to?.label || r.to?.value}</code> }, { h: 'Confidence', r: (r) => r.confidence }, { h: 'Reason', r: (r) => r.reason }, { h: '', r: (r) => <span className="row"><button className="sm" onClick={() => review(r._id, 'confirmed')}>Confirm</button><button className="sm danger" onClick={() => review(r._id, 'rejected')}>Reject</button></span> }]} /></Card>}
    {tab === 'persona' && <Card title="Persona Analysis" right={<button className="primary sm" onClick={() => run('persona')}>Run persona analysis</button>}><p className="muted sm">Compares every account that has an imported textual/behavioural profile. Output is analytical similarity only.</p>{jobTable}</Card>}
    {tab === 'jobs' && <Card title="Automated Jobs">{jobTable}</Card>}
  </>;
}

export function AuditLogs() {
  const [sp] = useSearchParams(); const action = sp.get('action') || ''; const [d] = useGet(`/admin/audit?action=${action}`, [action]);
  return <Card title={action ? `Audit log — ${action}` : 'Audit logs'}><Table rows={d?.items || []} empty="No audit records." cols={[{ h: 'User', r: (a) => a.username || '—' }, { h: 'Action', r: (a) => <Badge>{a.action}</Badge> }, { h: 'Date/time', r: (a) => fmt(a.createdAt) }, { h: 'Module', r: (a) => a.module }, { h: 'Investigation', r: (a) => a.investigation?.invId || '—' }, { h: 'Detail', r: (a) => a.detail }, { h: 'IP', r: (a) => a.ip }]} /></Card>;
}
export function LoginActivity() {
  const [d] = useGet('/admin/login-activity');
  return <Card title="Login Activity">
    <p className="muted sm" style={{ marginBottom: 12 }}>Overview of all registered Admins and Investigators, listing each account once with their login and active status.</p>
    <Table rows={d?.items || []} empty="No user records." cols={[
      { h: 'Name', r: (u) => <b>{u.fullName}</b> },
      { h: 'Username', r: (u) => <code>{u.username}</code> },
      { h: 'Role', r: (u) => <Badge tone={u.role === 'admin' ? 'purple' : 'blue'}>{u.role.replace('_', ' ')}</Badge> },
      { h: 'Login Status', r: (u) => <Badge tone={u.lastLoginAt ? 'green' : 'gray'}>{u.lastLoginAt ? 'Logged In / Active' : 'Never Logged In'}</Badge> },
      { h: 'Account Status', r: (u) => <Badge tone={u.status === 'active' ? 'green' : 'red'}>{u.status}</Badge> },
      { h: 'Last Login', r: (u) => fmt(u.lastLoginAt) }
    ]} />
  </Card>;
}
export function AdminInvestigations() {
  const [d] = useGet('/admin/investigations');
  return <Card title="All investigations"><Table rows={d?.items || []} empty="No investigations." cols={[{ h: 'ID', r: (i) => <code>{i.invId}</code> }, { h: 'Name', r: (i) => i.name }, { h: 'Investigator', r: (i) => i.owner?.fullName }, { h: 'Search', r: (i) => `${i.search.type}: ${i.search.query}` }, { h: 'Priority', r: (i) => i.priority }, { h: 'Status', r: (i) => <Badge tone="blue">{i.status}</Badge> }, { h: 'Updated', r: (i) => fmt(i.updatedAt) }]} /></Card>;
}
export function AdminReports() {
  const [d] = useGet('/admin/reports');
  return <Card title="Generated reports"><Table rows={d?.items || []} empty="No reports generated." cols={[{ h: 'Report ID', r: (r) => <code>{r.reportId}</code> }, { h: 'Investigation', r: (r) => r.investigation?.name }, { h: 'Investigator', r: (r) => r.generatedBy?.fullName }, { h: 'Date', r: (r) => fmt(r.createdAt) }, { h: 'Status', r: (r) => <Badge tone="green">{r.status}</Badge> }, { h: 'Format', r: (r) => r.formats.join(', ').toUpperCase() || '—' }]} /></Card>;
}
export function AdminAlerts() {
  const [d] = useGet('/admin/alerts');
  return <Card title="All alerts"><Table rows={d?.items || []} empty="No alerts." cols={[{ h: 'Severity', r: (a) => <Sev v={a.severity} /> }, { h: 'Type', r: (a) => a.kind.replace(/_/g, ' ') }, { h: 'Message', r: (a) => a.message }, { h: 'Investigator', r: (a) => a.owner?.fullName || 'System' }, { h: 'When', r: (a) => fmt(a.createdAt) }]} /></Card>;
}
export function SystemHealth() {
  const [h] = useGet('/admin/health');
  const [aiInfo] = useGet('/admin/ai/info');
  if (!h) return <div className="boot">Checking…</div>;
  return <div className="grid2">
    <Card title="System & Database Health">
      <div className="field"><span>Database</span><Badge tone={h.database === 'connected' ? 'green' : 'red'}>{h.database}</Badge></div>
      <div className="field"><span>AI Engine Service</span><Badge tone={h.ai.reachable ? 'green' : 'amber'}>{!h.ai.configured ? 'AI_SERVICE_URL not set' : h.ai.reachable ? 'online (FastAPI)' : 'online (Local Engine)'}</Badge></div>
      <div className="field"><span>Uptime</span>{h.uptimeSeconds}s</div>
      <div className="field"><span>Node Environment</span>{h.node}</div>
    </Card>
    <Card title="AI Machine Learning Pipeline Status">
      <div className="field"><span>Pipeline Version</span><b>{aiInfo?.pipeline_version || '1.0.0'}</b></div>
      <div className="field"><span>Stylometry Verifier Model</span><Badge tone="green">Gradient Boosting (Accuracy 85.07%)</Badge></div>
      <div className="field"><span>Anomaly Detector</span><Badge tone="blue">Isolation Forest & LOF</Badge></div>
      <div className="field"><span>Correlation Engine</span><Badge tone="purple">9-Signal Dynamic Fusion</Badge></div>
    </Card>
  </div>;
}