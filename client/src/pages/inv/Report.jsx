import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import api, { download, errMsg } from '../../api';
import { Badge, Conf, Empty, Table, fmt, fmtD } from '../../components/ui';

const H = ({ n, t }) => <h2 className="rep-h"><b>{String(n).padStart(2, '0')}</b>{t}</h2>;

export default function Report() {
  const { rid } = useParams(); const [r, setR] = useState(null); const [err, setErr] = useState('');
  useEffect(() => { api.get(`/inv/reports/${rid}`).then((x) => setR(x.data)).catch((e) => setErr(errMsg(e))); }, [rid]);
  if (err) return <Empty>{err}</Empty>; if (!r) return <div className="boot">Loading report…</div>;
  const exp = async (f) => { try { await download(`/inv/reports/${rid}/export?format=${f}`, `${rid}.${f}`); } catch (e) { toast.error(errMsg(e)); } };
  const pdf = async () => { try { await api.get(`/inv/reports/${rid}/export?format=pdf`); } catch (e) { return toast.error(errMsg(e)); } window.print(); };
  const c = r.confidenceAssessment;
  return (
    <>
      <div className="rep-bar no-print"><span className="muted">{r.meta.reportId}</span><div className="row"><button onClick={() => exp('csv')}>Export CSV</button><button onClick={() => exp('json')}>Export JSON</button><button className="primary" onClick={pdf}>Print / Save PDF</button></div></div>
      <article className="report">
        <div className="rep-top"><small>DARKTRACE · INTELLIGENCE DOSSIER · {r.meta.reportId}</small><h1>{r.meta.investigation.name}</h1>
          <div className="meta"><span>Investigation <b>{r.meta.investigation.invId}</b></span><span>Priority <b>{r.meta.investigation.priority}</b></span><span>Status <b>{r.meta.investigation.status}</b></span><span>Prepared by <b>{r.meta.generatedBy}</b></span><span>Generated <b>{fmt(r.meta.generatedAt)}</b></span></div></div>

        <H n={1} t="Executive Summary" /><p>{r.executiveSummary}</p>
        <H n={2} t="Search Information" /><p>Type: <b>{r.search.type}</b> · Value: <code>{r.search.query}</code></p>
        <H n={3} t="Subject / Actor Overview" />
        <Table rows={r.actors} empty="No actor record linked." cols={[{ h: 'Actor', r: (a) => a.label || a.id }, { h: 'Category', r: (a) => a.category || '—' }, { h: 'Status', r: (a) => a.status }, { h: 'First seen', r: (a) => fmtD(a.firstSeen) }, { h: 'Last seen', r: (a) => fmtD(a.lastSeen) }, { h: 'Confidence', r: (a) => <Conf v={a.confidence} /> }]} />
        <H n={4} t="Identifiers" />
        <Table rows={r.identifiers} cols={[{ h: 'Type', r: (i) => i.type }, { h: 'Value', r: (i) => <code>{i.value}</code> }, { h: 'First seen', r: (i) => fmtD(i.firstSeen) }, { h: 'Confidence', r: (i) => <Conf v={i.confidence} /> }, { h: 'Sources', r: (i) => i.sources.join(', ') }]} />
        <H n={5} t="Relationship Graph (edge list)" />
        <Table rows={r.relationships} cols={[{ h: 'From', r: (x) => x.from }, { h: 'Relationship', r: (x) => <Badge tone={x.status === 'proposed' ? 'amber' : 'blue'}>{x.type}</Badge> }, { h: 'To', r: (x) => x.to }, { h: 'Confidence', r: (x) => <Conf v={x.confidence} /> }, { h: 'Method', r: (x) => x.method }, { h: 'Sources', r: (x) => x.sources.join(', ') }]} />
        <H n={6} t="Timeline" />
        <Table rows={r.timeline} cols={[{ h: 'Date', r: (t) => fmtD(t.date) }, { h: 'Event', r: (t) => t.title }, { h: 'Type', r: (t) => t.kind }, { h: 'Sources', r: (t) => t.sources.join(', ') }]} />
        <H n={7} t="Persona Analysis" />
        {r.persona.available ? r.persona.pairs.map((p, i) => <p key={i}>{p.a} ↔ {p.b}: overall <b>{Math.round(p.overall * 100)}%</b> — <i>analytical similarity, not identification.</i></p>) : <p className="muted">{r.persona.reason}</p>}
        <H n={8} t="Infrastructure" />
        <Table rows={r.infrastructure} cols={[{ h: 'Indicator', r: (i) => <code>{i.indicator}</code> }, { h: 'Type', r: (i) => i.type }, { h: 'Associated', r: (i) => i.associated.join(', ') }, { h: 'Confidence', r: (i) => <Conf v={i.confidence} /> }, { h: 'Sources', r: (i) => i.sources.join(', ') }]} />
        <H n={9} t="Blockchain Information" />
        <Table rows={r.blockchain} cols={[{ h: 'Wallet', r: (b) => <code>{b.wallet}</code> }, { h: 'Received', r: (b) => b.attributes.totalReceived ?? '—' }, { h: 'Sent', r: (b) => b.attributes.totalSent ?? '—' }, { h: 'Tx count', r: (b) => b.attributes.txCount ?? '—' }, { h: 'Confidence', r: (b) => <Conf v={b.confidence} /> }, { h: 'Sources', r: (b) => b.sources.join(', ') }]} />
        <H n={10} t="Evidence" />
        <Table rows={r.evidence} cols={[{ h: 'Evidence', r: (e) => e.title }, { h: 'Type', r: (e) => e.type }, { h: 'Date', r: (e) => fmtD(e.date) }, { h: 'Related', r: (e) => e.related.join(', ') }, { h: 'Confidence', r: (e) => <Conf v={e.confidence} /> }, { h: 'Source', r: (e) => e.source }]} />
        <H n={11} t="Confidence Assessment" />
        <p>Level: <Badge tone={c.level === 'high' ? 'green' : c.level === 'moderate' ? 'amber' : 'red'}>{c.level}</Badge> · Avg. relationship confidence: <b>{c.averageRelationshipConfidence ?? 'n/a'}{c.averageRelationshipConfidence != null && '%'}</b> · Independent sources: <b>{c.independentSources}</b></p><p className="muted sm">{c.method}</p>
        <H n={12} t="Sources" />
        <Table rows={r.sources} cols={[{ h: 'Source', r: (s) => s.name }, { h: 'Type', r: (s) => s.type }, { h: 'Reliability', r: (s) => s.reliability }, { h: 'Last collected', r: (s) => fmtD(s.lastImportAt) }, { h: 'Records used', r: (s) => s.recordsUsed }]} />
        <H n={13} t="Investigator Notes" /><p style={{ whiteSpace: 'pre-wrap' }}>{r.investigatorNotes || 'No notes recorded.'}</p>
      </article>
    </>
  );
}