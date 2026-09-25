import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import api, { errMsg } from '../../api';
import Graph from '../../components/Graph';
import { Badge, Card, Conf, Empty, Modal, Table, TYPE_LABEL, fmt, fmtD } from '../../components/ui';

const TABS = [['overview', 'Overview'], ['identifiers', 'Identifiers'], ['graph', 'Relationship Graph'], ['timeline', 'Timeline'], ['persona', 'AI Persona & Stylometry'],
  ['infrastructure', 'Infrastructure'], ['blockchain', 'Blockchain'], ['evidence', 'Evidence'], ['sources', 'Sources']];

export default function Workspace() {
  const { invId } = useParams(); const [sp, setSp] = useSearchParams(); const nav = useNavigate();
  const [ws, setWs] = useState(null); const [inv, setInv] = useState(null); const [searchId, setSearchId] = useState(null);
  const [err, setErr] = useState(''); const [saveOpen, setSaveOpen] = useState(false);
  const tab = sp.get('tab') || 'overview';
  const type = sp.get('type'), q = sp.get('q');

  useEffect(() => {
    setWs(null); setErr('');
    const p = invId ? api.get(`/inv/investigations/${invId}`).then((r) => { setInv(r.data.investigation); setWs(r.data.workspace); })
      : api.post('/inv/search', { type, query: q }).then((r) => { setSearchId(r.data.searchId); setWs(r.data.workspace); });
    p.catch((e) => setErr(errMsg(e)));
  }, [invId, type, q]);

  const byId = useMemo(() => Object.fromEntries((ws?.entities || []).map((e) => [e._id, e])), [ws]);
  const srcById = useMemo(() => Object.fromEntries((ws?.sources || []).map((s) => [s._id, s])), [ws]);
  const nameOf = (id) => byId[id]?.label || byId[id]?.value || id;
  const srcNames = (ids) => (ids || []).map((i) => srcById[i]?.name).filter(Boolean).join(', ') || '—';
  const setTab = (t) => { const n = new URLSearchParams(sp); n.set('tab', t); setSp(n, { replace: true }); };

  const expand = async (id) => {
    const { data } = await api.get(`/inv/entities/${id}/neighbors`);
    setWs((w) => {
      const ents = new Map(w.entities.map((e) => [e._id, e])); data.entities.forEach((e) => ents.set(e._id, e));
      const rels = new Map(w.relationships.map((r) => [r._id, r])); data.relationships.forEach((r) => rels.set(r._id, r));
      const srcs = new Map(w.sources.map((s) => [s._id, s])); data.sources.forEach((s) => !srcs.has(s._id) && srcs.set(s._id, s));
      return { ...w, entities: [...ents.values()], relationships: [...rels.values()], sources: [...srcs.values()] };
    });
    toast.success('Related entities expanded');
  };

  const generate = async () => {
    let targetInv = inv;
    if (!targetInv) {
      const t0 = toast.loading('Saving investigation for report…');
      try {
        const { data } = await api.post('/inv/investigations', {
          name: `Investigation: ${ws.query.query}`, priority: 'medium', status: 'Active',
          search: { type: ws.query.type, query: ws.query.query }, searchId, saved: true
        });
        targetInv = data;
        setInv(data);
        toast.dismiss(t0);
      } catch (e) {
        toast.error(errMsg(e), { id: t0 });
        return setSaveOpen(true);
      }
    }
    const t = toast.loading('Generating report…');
    try { const { data } = await api.post(`/inv/investigations/${targetInv._id}/report`); toast.success('Report ready', { id: t }); nav(`/inv/reports/${data.reportId}`); }
    catch (e) { toast.error(errMsg(e), { id: t }); }
  };

  const toggleClose = async () => {
    if (inv) {
      const isClosed = inv.status === 'Closed';
      const nextStatus = isClosed ? 'Active' : 'Closed';
      const t = toast.loading(isClosed ? 'Reopening investigation…' : 'Closing investigation…');
      try {
        const { data } = await api.patch(`/inv/investigations/${inv._id}`, { status: nextStatus });
        setInv(data);
        toast.success(isClosed ? 'Investigation reopened' : 'Investigation closed & moved to Closed tab', { id: t });
        if (!isClosed) nav('/inv/investigations?bucket=closed');
      } catch (e) { toast.error(errMsg(e), { id: t }); }
    } else {
      const t = toast.loading('Closing investigation…');
      try {
        const { data } = await api.post('/inv/investigations', {
          name: `Investigation: ${ws.query.query}`, priority: 'medium', status: 'Closed',
          search: { type: ws.query.type, query: ws.query.query }, searchId, saved: true
        });
        toast.success('Investigation saved & moved to Closed tab', { id: t });
        nav('/inv/investigations?bucket=closed');
      } catch (e) { toast.error(errMsg(e), { id: t }); }
    }
  };

  if (err) return <Empty>{err}</Empty>;
  if (!ws) return <div className="boot">Correlating intelligence…</div>;
  const query = ws.query;
  const isClosed = inv?.status === 'Closed';

  return (
    <>
      <div className="ws-head">
        <div>
          <div className="crumb">{inv ? inv.invId : 'Unsaved search'} · {TYPE_LABEL[{ forum: 'forum_account', marketplace: 'marketplace_account' }[query.type] || query.type] || query.type}</div>
          <h1><code>{query.query}</code></h1>
          <div className="row">{inv && <><Badge tone={isClosed ? 'gray' : 'blue'}>{inv.status}</Badge><Badge tone={inv.priority === 'critical' || inv.priority === 'high' ? 'red' : 'gray'}>{inv.priority}</Badge>{inv.tags.map((t) => <Badge key={t}>{t}</Badge>)}</>}
            <span className="muted sm">{ws.entities.length} entities · {ws.relationships.length} relationships · {ws.evidence.length} evidence</span></div>
        </div>
        <div className="row">
          {!inv && <button onClick={() => setSaveOpen(true)} disabled={!ws.entities.length}>Save as Investigation</button>}
          <button
            className={isClosed ? 'btn-reopen-inv' : 'btn-close-inv'}
            onClick={toggleClose}
            disabled={!ws.entities.length}
            title={isClosed ? 'Reopen Investigation' : 'Close Investigation'}
          >
            {isClosed ? '🔓 REOPEN INVESTIGATION' : '🔒 CLOSE INVESTIGATION'}
          </button>
          <button className="primary" onClick={generate} disabled={!ws.entities.length}>GENERATE FULL REPORT</button>
        </div>
      </div>

      {!ws.entities.length ? <Empty>No matching intelligence exists for this identifier in the database.</Empty> : <>
        <div className="tabs">{TABS.map(([k, l]) => <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>)}</div>
        {tab === 'overview' && <Overview ws={ws} q={query} srcNames={srcNames} />}
        {tab === 'identifiers' && <Identifiers ws={ws} srcNames={srcNames} />}
        {tab === 'graph' && <GraphTab ws={ws} byId={byId} nameOf={nameOf} srcNames={srcNames} expand={expand} />}
        {tab === 'timeline' && <Timeline ws={ws} srcNames={srcNames} />}
        {tab === 'persona' && <Persona ws={ws} nameOf={nameOf} />}
        {tab === 'infrastructure' && <Infra ws={ws} nameOf={nameOf} srcNames={srcNames} />}
        {tab === 'blockchain' && <Chain ws={ws} nameOf={nameOf} srcNames={srcNames} />}
        {tab === 'evidence' && <Evidence ws={ws} nameOf={nameOf} srcById={srcById} />}
        {tab === 'sources' && <Sources ws={ws} />}
      </>}
      {saveOpen && <SaveModal query={query} searchId={searchId} onClose={() => setSaveOpen(false)} onSaved={(i) => nav(`/inv/investigation/${i._id}`)} />}
    </>
  );
}

const Field = ({ k, v }) => <div className="field"><span>{k}</span><div>{v || <em>—</em>}</div></div>;
const list = (arr) => arr.length ? arr.map((e) => <div key={e._id}><code>{e.label ? `${e.label} · ` : ''}{e.value}</code></div>) : null;

function Overview({ ws, q, srcNames }) {
  const s = ws.summary; const of = (t) => ws.entities.filter((e) => e.type === t);
  const a = s.actors[0]; const c = s.confidence;
  return (
    <div className="grid2">
      <Card title="Subject">
        <Field k="Search identifier" v={<code>{q.query}</code>} /><Field k="Actor" v={s.actors.map((x) => x.label || x.value).join(', ')} />
        <Field k="Category" v={s.category} /><Field k="Status" v={s.status && <Badge tone="blue">{s.status}</Badge>} />
        <Field k="First observed" v={fmtD(s.firstSeen)} /><Field k="Last observed" v={fmtD(s.lastSeen)} />
        <Field k="Actor confidence" v={a?.confidence != null && <Conf v={a.confidence} />} />
      </Card>
      <Card title="Confidence assessment">
        <Field k="Level" v={<Badge tone={c.level === 'high' ? 'green' : c.level === 'moderate' ? 'amber' : 'red'}>{c.level}</Badge>} />
        <Field k="Avg. relationship confidence" v={c.averageRelationshipConfidence != null && `${c.averageRelationshipConfidence}%`} />
        <Field k="Independent sources" v={c.independentSources} /><Field k="Relationships" v={c.relationshipCount} />
        <p className="muted sm">{c.method} Analytical association — not proof of identity.</p>
      </Card>
      <Card title="Known usernames">{list(of('username')) || <em>None recorded</em>}</Card>
      <Card title="Known PGP keys">{list(of('pgp')) || <em>None recorded</em>}</Card>
      <Card title="Known wallets">{list(of('wallet')) || <em>None recorded</em>}</Card>
      <Card title="Known platforms">{list([...of('forum_account'), ...of('marketplace_account')]) || <em>None recorded</em>}</Card>
      <Card title="Related infrastructure" className="span2">{list([...of('domain'), ...of('infrastructure')]) || <em>None recorded</em>}</Card>
    </div>
  );
}

const Identifiers = ({ ws, srcNames }) => (
  <Card title="Identifiers"><Table rows={ws.entities.filter((e) => e.type !== 'actor')} cols={[
    { h: 'Type', r: (e) => <Badge>{TYPE_LABEL[e.type]}</Badge> }, { h: 'Value', r: (e) => <code>{e.value}</code> }, { h: 'Label', r: (e) => e.label || '—' },
    { h: 'First seen', r: (e) => fmtD(e.firstSeen) }, { h: 'Last seen', r: (e) => fmtD(e.lastSeen) }, { h: 'Confidence', r: (e) => <Conf v={e.confidence} /> }, { h: 'Source', r: (e) => srcNames(e.sourceIds) }]} /></Card>
);

function GraphTab({ ws, byId, nameOf, srcNames, expand }) {
  const [sel, setSel] = useState(null);
  const node = sel?.kind === 'node' && byId[sel.id]; const edge = sel?.kind === 'edge' && ws.relationships.find((r) => r._id === sel.id);
  return (
    <div className="graph-layout">
      <Graph entities={ws.entities} relationships={ws.relationships} onSelect={setSel} onExpand={expand} />
      <Card title={node ? 'Node details' : edge ? 'Relationship details' : 'Details'} className="side">
        {!sel && <p className="muted">Click a node or edge. Double-click a node to expand its related entities.</p>}
        {node && <><Field k="Type" v={TYPE_LABEL[node.type]} /><Field k="Value" v={<code>{node.value}</code>} /><Field k="Label" v={node.label} /><Field k="Confidence" v={<Conf v={node.confidence} />} />
          <Field k="First / last seen" v={`${fmtD(node.firstSeen)} → ${fmtD(node.lastSeen)}`} /><Field k="Source" v={srcNames(node.sourceIds)} />
          <button className="sm" onClick={() => expand(node._id)}>Expand related entities</button></>}
        {edge && <><Field k="Relationship" v={edge.type} /><Field k="From" v={nameOf(edge.from)} /><Field k="To" v={nameOf(edge.to)} /><Field k="Confidence" v={<Conf v={edge.confidence} />} />
          <Field k="Method" v={edge.method} /><Field k="Status" v={<Badge tone={edge.status === 'proposed' ? 'amber' : 'green'}>{edge.status}</Badge>} /><Field k="Reason" v={edge.reason} /><Field k="Source" v={srcNames(edge.sourceIds)} /></>}
      </Card>
    </div>
  );
}

function Timeline({ ws, srcNames }) {
  const [sel, setSel] = useState(null);
  if (!ws.timeline.length) return <Empty>No dated events in the dataset for this investigation.</Empty>;
  return (
    <Card title="Timeline">
      <div className="timeline">{ws.timeline.map((t, i) => (
        <div key={i} className="tl-item" onClick={() => setSel(t)}><i className={`tl-dot ${t.kind}`} /><time>{fmtD(t.date)}</time><div><b>{t.title}</b><small>{t.kind}</small></div></div>
      ))}</div>
      {sel && <Modal title="Event details" onClose={() => setSel(null)}>
        <Field k="Event" v={sel.title} /><Field k="Date" v={fmt(sel.date)} /><Field k="Type" v={sel.kind} /><Field k="Confidence" v={<Conf v={sel.confidence} />} /><Field k="Source" v={srcNames(sel.sourceIds)} />
        {sel.detail && <pre className="json">{JSON.stringify(sel.detail, null, 2)}</pre>}</Modal>}
    </Card>
  );
}

function Persona({ ws, nameOf }) {
  const [mode, setMode] = useState('multi');
  const [res, setRes] = useState(null);
  const [hypRes, setHypRes] = useState(null);
  const [styRes, setStyRes] = useState(null);
  const [busy, setBusy] = useState(false);

  const [styA, setStyA] = useState('We operate across multiple onion routing nodes and deploy customized ransom scripts using Python.');
  const [styB, setStyB] = useState('Our team manages onion nodes and utilizes tailored Python scripts for specialized network deployments.');

  const runMulti = async () => {
    setBusy(true);
    try { setRes((await api.post('/inv/persona', { entityIds: ws.entities.map((e) => e._id) })).data); }
    catch (e) { toast.error(errMsg(e)); }
    setBusy(false);
  };

  const runHypothesis = async () => {
    setBusy(true);
    try {
      const pA = ws.entities[0] ? { name: ws.entities[0].value, posts: [ws.entities[0].label || ''] } : { name: 'Target Alpha' };
      const pB = ws.entities[1] ? { name: ws.entities[1].value, posts: [ws.entities[1].label || ''] } : { name: 'Target Beta' };
      const r = await api.post('/inv/ai/hypothesis', { persona_a: pA, persona_b: pB });
      setHypRes(r.data);
      toast.success('Hypothesis evaluation complete');
    } catch (e) { toast.error(errMsg(e)); }
    setBusy(false);
  };

  const runStylometry = async () => {
    setBusy(true);
    try {
      const r = await api.post('/inv/ai/stylometry', { text_a: styA, text_b: styB });
      setStyRes(r.data);
      toast.success('Stylometry verification complete');
    } catch (e) { toast.error(errMsg(e)); }
    setBusy(false);
  };

  const pct = (v) => (v == null ? '—' : `${Math.round(v * 100)}%`);
  const rows = [['text', 'Text similarity'], ['vocabulary', 'Vocabulary'], ['topic', 'Topic'], ['activity', 'Activity pattern'], ['behavioral', 'Behavioural']];

  return (
    <>
      <div className="tabs" style={{ marginBottom: 12 }}>
        {[
          ['multi', 'Multi-Signal Correlation'],
          ['stylometry', 'AI Stylometry Model'],
          ['hypothesis', 'Formal Hypothesis Test']
        ].map(([k, l]) => <button key={k} className={mode === k ? 'on' : ''} onClick={() => setMode(k)}>{l}</button>)}
      </div>

      {mode === 'multi' && (
        <Card title="Multi-Signal Persona Correlation" right={<button className="primary sm" onClick={runMulti} disabled={busy}>{busy ? 'Analysing…' : 'Run correlation'}</button>}>
          <p className="muted sm">Correlates accounts across 9 threat dimensions (stylometry, PGP keys, wallets, TTPs, temporal activity patterns):</p>
          {!res && <Empty>Run correlation to evaluate connected persona identity features.</Empty>}
          {res && !res.available && <Empty>{res.reason}</Empty>}
          {res?.available && res.pairs.map((p, i) => (
            <div key={i} className="pair">
              <h4>{nameOf(p.a)} <span>↔</span> {nameOf(p.b)} <Badge tone="blue">overall {pct(p.overall)}</Badge></h4>
              {rows.map(([k, l]) => <div key={k} className="bar"><span>{l}</span><div><i style={{ width: pct(p.scores?.[k]) }} /></div><b>{pct(p.scores?.[k])}</b></div>)}
              {p.explanation && <p className="muted sm">{p.explanation}</p>}
            </div>
          ))}
        </Card>
      )}

      {mode === 'stylometry' && (
        <div className="grid2">
          <Card title="Stylometry Authorship Verifier (Trained Model)">
            <p className="muted sm">Compares character/word n-grams, vocabulary richness, punctuation & syntax against trained Gradient Boosting model:</p>
            <div className="form">
              <label>Text Sample A (Forum / Ransom note / Email)
                <textarea rows="4" value={styA} onChange={(e) => setStyA(e.target.value)} />
              </label>
              <label>Text Sample B (Marketplace / Chat snippet)
                <textarea rows="4" value={styB} onChange={(e) => setStyB(e.target.value)} />
              </label>
              <button className="primary" onClick={runStylometry} disabled={busy}>{busy ? 'Analyzing...' : 'Run Stylometry Verification'}</button>
            </div>
          </Card>

          <Card title="Prediction Breakdown & Probabilities">
            {!styRes ? <Empty>Execute stylometry verification to view feature breakdowns.</Empty> : <>
              <div style={{ padding: 12, background: 'var(--panel2)', borderRadius: 8, marginBottom: 12 }}>
                <div style={{ fontSize: 16, fontWeight: 700 }}>{styRes.classification}</div>
                <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 4 }}>
                  Same-Author Calibrated Probability: <b>{((styRes.same_author_probability || 0) * 100).toFixed(2)}%</b>
                </div>
              </div>
              <div style={{ display: 'grid', gap: 8 }}>
                {[
                  ['Character N-Grams', styRes.character_similarity],
                  ['Word N-Grams', styRes.word_similarity],
                  ['Vocabulary Diversity (TTR)', styRes.vocabulary_similarity],
                  ['Punctuation Pattern', styRes.punctuation_similarity],
                  ['Syntax & Sentence Structure', styRes.syntax_similarity]
                ].map(([label, score], i) => (
                  <div key={i} className="bar">
                    <span>{label}</span>
                    <div><i style={{ width: `${Math.round((score || 0) * 100)}%` }} /></div>
                    <b>{Math.round((score || 0) * 100)}%</b>
                  </div>
                ))}
              </div>
              <p className="muted sm" style={{ marginTop: 12 }}>Methodology: {styRes.methodology}</p>
            </>}
          </Card>
        </div>
      )}

      {mode === 'hypothesis' && (
        <Card title="Formal Analytical Hypothesis Test" right={<button className="primary sm" onClick={runHypothesis} disabled={busy}>{busy ? 'Testing...' : 'Test Hypothesis'}</button>}>
          <p className="muted sm">Formulates and tests a structured intelligence hypothesis on persona migration and cross-forum association:</p>
          {!hypRes ? <Empty>Click 'Test Hypothesis' to evaluate supporting and contradictory evidence for this investigation.</Empty> : <>
            <div style={{ padding: 12, background: 'var(--panel2)', borderRadius: 8, marginBottom: 14 }}>
              <b>Hypothesis:</b>
              <div style={{ fontStyle: 'italic', margin: '4px 0 8px' }}>"{hypRes.hypothesis}"</div>
              <div className="row">
                <Badge tone="blue">Classification: {hypRes.classification}</Badge>
                <Badge tone="green">Confidence: {Math.round((hypRes.confidence || 0.85) * 100)}%</Badge>
                <Badge tone="gray">Evidence Coverage: {Math.round((hypRes.evidence_coverage || 0.78) * 100)}%</Badge>
              </div>
            </div>

            <div className="grid2">
              <div>
                <b>Supporting Evidence Signals:</b>
                <ul style={{ paddingLeft: 18, color: 'var(--green)' }}>
                  {(hypRes.supporting_signals || []).map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
              <div>
                <b>Contradictory / Discrepancy Signals:</b>
                <ul style={{ paddingLeft: 18, color: 'var(--red)' }}>
                  {(hypRes.contradictory_signals || []).length ? hypRes.contradictory_signals.map((s, i) => <li key={i}>{s}</li>) : <li>No direct contradictions observed.</li>}
                </ul>
              </div>
            </div>
            <p className="muted sm" style={{ marginTop: 12 }}>{hypRes.safety_notice}</p>
          </>}
        </Card>
      )}
    </>
  );
}



function Infra({ ws, nameOf, srcNames }) {
  const rows = ws.entities.filter((e) => ['infrastructure', 'domain'].includes(e.type));
  const assoc = (id) => ws.relationships.filter((r) => r.from === id || r.to === id).map((r) => nameOf(r.from === id ? r.to : r.from)).join(', ') || '—';
  return <Card title="Infrastructure"><Table rows={rows} empty="No infrastructure intelligence linked." cols={[
    { h: 'Indicator', r: (e) => <code>{e.value}</code> }, { h: 'Type', r: (e) => TYPE_LABEL[e.type] }, { h: 'Associated entity', r: (e) => assoc(e._id) },
    { h: 'First seen', r: (e) => fmtD(e.firstSeen) }, { h: 'Last seen', r: (e) => fmtD(e.lastSeen) }, { h: 'Confidence', r: (e) => <Conf v={e.confidence} /> }, { h: 'Source', r: (e) => srcNames(e.sourceIds) }]} /></Card>;
}

function Chain({ ws, nameOf, srcNames }) {
  const wallets = ws.entities.filter((e) => e.type === 'wallet');
  const [liveInfo, setLiveInfo] = useState({});
  const [busyAddr, setBusyAddr] = useState({});

  const fetchOnChain = async (addr) => {
    setBusyAddr((b) => ({ ...b, [addr]: true }));
    try {
      const res = await api.get(`/inv/ai/blockchain/address/${encodeURIComponent(addr)}`);
      setLiveInfo((prev) => ({ ...prev, [addr]: res.data }));
      toast.success(`On-chain data loaded for ${addr.slice(0, 10)}...`);
    } catch (e) { toast.error(errMsg(e)); }
    setBusyAddr((b) => ({ ...b, [addr]: false }));
  };

  const assoc = (id) => ws.relationships.filter((r) => r.from === id || r.to === id).map((r) => nameOf(r.from === id ? r.to : r.from)).join(', ') || '—';
  if (!wallets.length) return <Empty>No wallets linked to this investigation.</Empty>;

  return wallets.map((w) => {
    const a = w.attributes || {};
    const live = liveInfo[w.value];
    const s = live?.summary || {};
    const bp = live?.behavior_profile || {};
    const prov = live?.provenance || {};

    return (
      <Card key={w._id} title={<code>{w.value}</code>} right={<span className="row"><Conf v={w.confidence} /><button className="primary sm" onClick={() => fetchOnChain(w.value)} disabled={busyAddr[w.value]}>{busyAddr[w.value] ? 'Querying...' : 'Fetch Live On-Chain Data'}</button></span>}>
        {prov.mode && <div style={{ marginBottom: 10 }}><Badge tone={prov.mode === 'LIVE' ? 'green' : 'amber'}>[{prov.source || 'Read-Only Blockchain Data'}] · Mode: {prov.mode}</Badge></div>}

        <div className="grid3">
          <Field k="Related entities" v={assoc(w._id)} />
          <Field k="First / last seen" v={`${fmtD(w.firstSeen)} → ${fmtD(w.lastSeen)}`} />
          <Field k="Source" v={srcNames(w.sourceIds)} />
          <Field k="Bitcoin Balance" v={s.balance_btc != null ? `${s.balance_btc} BTC` : (a.balance || '—')} />
          <Field k="Total Received" v={s.total_received_btc != null ? `${s.total_received_btc} BTC` : (a.totalReceived || '—')} />
          <Field k="Total Sent" v={s.total_sent_btc != null ? `${s.total_sent_btc} BTC` : (a.totalSent || '—')} />
          <Field k="On-Chain Tx Count" v={s.transaction_count != null ? s.transaction_count : (a.txCount || '—')} />
          {bp.risk_level && <Field k="AI Behavior Risk" v={<Badge tone={bp.risk_level === 'High' || bp.risk_level === 'Critical' ? 'red' : 'green'}>{bp.risk_level} ({bp.category})</Badge>} />}
        </div>

        {a.transactions?.length ? (
          <Table rows={a.transactions} cols={[{ h: 'Time', r: (t) => fmt(t.time) }, { h: 'Hash', r: (t) => <code>{t.hash}</code> }, { h: 'Direction', r: (t) => t.direction }, { h: 'Amount', r: (t) => t.amount }, { h: 'Counterparty', r: (t) => <code>{t.counterparty}</code> }]} />
        ) : (
          <p className="muted sm" style={{ marginTop: 8 }}>Strictly read-only public Bitcoin ledger observation (no private key handling, credentials, or signing).</p>
        )}
      </Card>
    );
  });
}

function Evidence({ ws, nameOf, srcById }) {
  const [sel, setSel] = useState(null);
  const open = (x) => { setSel(x); api.post(`/inv/evidence/${x._id}/view`).catch(() => {}); };
  return (
    <Card title="Evidence">
      <Table rows={ws.evidence} empty="No evidence records attached." onRow={open} cols={[{ h: 'Evidence', r: (x) => x.title }, { h: 'Type', r: (x) => <Badge>{x.type}</Badge> }, { h: 'Source', r: (x) => srcById[x.sourceId]?.name || '—' },
        { h: 'Date', r: (x) => fmtD(x.observedAt) }, { h: 'Related', r: (x) => (x.entityIds || []).map(nameOf).join(', ') }, { h: 'Confidence', r: (x) => <Conf v={x.confidence} /> }]} />
      {sel && <Modal title={sel.title} onClose={() => setSel(null)} wide><Field k="Type" v={sel.type} /><Field k="Date" v={fmt(sel.observedAt)} /><Field k="Source" v={srcById[sel.sourceId]?.name} />
        <Field k="Related entities" v={(sel.entityIds || []).map(nameOf).join(', ')} /><Field k="Confidence" v={<Conf v={sel.confidence} />} /><pre className="json">{sel.content || 'No additional content.'}</pre></Modal>}
    </Card>
  );
}

const Sources = ({ ws }) => <Card title="Sources"><Table rows={ws.sources} cols={[{ h: 'Source', r: (s) => s.name }, { h: 'Type', r: (s) => s.type }, { h: 'Last collected', r: (s) => fmtD(s.lastImportAt) }, { h: 'Reliability', r: (s) => <Badge>{s.reliability}</Badge> }, { h: 'Records used', r: (s) => s.recordsUsed }]} /></Card>;

function SaveModal({ query, searchId, onClose, onSaved }) {
  const [f, setF] = useState({ name: '', priority: 'medium', status: 'Active', tags: '', notes: '' });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const save = async (e) => {
    e.preventDefault();
    try { const { data } = await api.post('/inv/investigations', { ...f, tags: f.tags.split(',').map((t) => t.trim()).filter(Boolean), search: query, searchId }); toast.success(`Saved as ${data.invId}`); onSaved(data); }
    catch (er) { toast.error(errMsg(er)); }
  };
  return (
    <Modal title="Save as investigation" onClose={onClose}>
      <form onSubmit={save} className="form">
        <label>Name<input value={f.name} onChange={set('name')} required /></label>
        <div className="row2"><label>Priority<select value={f.priority} onChange={set('priority')}>{['low', 'medium', 'high', 'critical'].map((p) => <option key={p}>{p}</option>)}</select></label>
          <label>Status<select value={f.status} onChange={set('status')}>{['New', 'Active', 'Under Review', 'Closed', 'Archived'].map((p) => <option key={p}>{p}</option>)}</select></label></div>
        <label>Tags (comma-separated)<input value={f.tags} onChange={set('tags')} /></label>
        <label>Investigator notes<textarea rows="4" value={f.notes} onChange={set('notes')} /></label>
        <button className="primary">Save investigation</button>
      </form>
    </Modal>
  );
}