export const fmt = (d) => (d ? new Date(d).toLocaleString() : '—');
export const fmtD = (d) => (d ? new Date(d).toLocaleDateString() : '—');
export const Badge = ({ children, tone = 'gray' }) => <span className={`badge ${tone}`}>{children}</span>;
export const Conf = ({ v }) => v == null ? <Badge>n/a</Badge> : <Badge tone={v >= 75 ? 'green' : v >= 50 ? 'amber' : 'red'}>{v}%</Badge>;
export const Sev = ({ v }) => <Badge tone={v === 'High' ? 'red' : v === 'Medium' ? 'amber' : 'blue'}>{v}</Badge>;
export const Empty = ({ children }) => <div className="empty">{children}</div>;
export const Card = ({ title, right, children, className = '' }) => (
  <section className={`card ${className}`}>{(title || right) && <header><h3>{title}</h3><div>{right}</div></header>}{children}</section>
);
export const Stat = ({ label, value, tone }) => <div className={`stat ${tone || ''}`}><span>{label}</span><b>{value ?? 0}</b></div>;

export function Modal({ title, onClose, children, wide }) {
  return (
    <div className="overlay" onMouseDown={onClose}>
      <div className={`modal ${wide ? 'wide' : ''}`} onMouseDown={(e) => e.stopPropagation()}>
        <header><h3>{title}</h3><button className="ghost" onClick={onClose}>✕</button></header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

export function Table({ cols, rows, onRow, empty = 'No records' }) {
  if (!rows?.length) return <Empty>{empty}</Empty>;
  return (
    <div className="table-wrap"><table>
      <thead><tr>{cols.map((c) => <th key={c.h}>{c.h}</th>)}</tr></thead>
      <tbody>{rows.map((r, i) => (
        <tr key={r._id || i} className={onRow ? 'click' : ''} onClick={() => onRow?.(r)}>{cols.map((c) => <td key={c.h}>{c.r(r)}</td>)}</tr>
      ))}</tbody>
    </table></div>
  );
}
export const TYPE_LABEL = { actor: 'Actor', username: 'Username', pgp: 'PGP Key', wallet: 'Wallet', forum_account: 'Forum Account', marketplace_account: 'Marketplace Account', domain: 'Domain', infrastructure: 'Infrastructure' };
export const TYPE_COLOR = { actor: '#ff5d5d', username: '#38bdf8', pgp: '#a78bfa', wallet: '#fbbf24', forum_account: '#34d399', marketplace_account: '#f472b6', domain: '#60a5fa', infrastructure: '#94a3b8' };