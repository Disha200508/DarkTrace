import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const TYPES = [
  ['username', 'Username / Handle', 'e.g. ShadowX or DarkVortex'],
  ['pgp', 'PGP Fingerprint', 'e.g. 4A8F 90B2 12C3 D4E5 F6A7 B8C9 0123 4567 89AB CDEF'],
  ['wallet', 'Cryptocurrency Wallet', 'e.g. bc1qShadowX9947xy2kgdygjrsqtzq2n0yrf249'],
  ['forum', 'Forum Account', 'e.g. ShadowX_Dread'],
  ['marketplace', 'Marketplace Account', 'e.g. ShadowX'],
  ['domain', 'Domain', 'e.g. shadow-drop.is'],
  ['infrastructure', 'Infrastructure Indicator', 'e.g. vortex-leak-portal.onion'],
  ['actor', 'Actor ID', 'e.g. ShadowX or DarkVortex']
];

export default function NewSearch() {
  const [type, setType] = useState('username'); const [q, setQ] = useState(''); const nav = useNavigate();
  const t = TYPES.find((x) => x[0] === type);
  return (
    <div className="search-page">
      <h1>New Investigation</h1><p className="muted">Choose the identifier type, then enter the value you have.</p>
      <div className="type-grid">{TYPES.map(([k, l]) => <button key={k} className={`type ${type === k ? 'on' : ''}`} onClick={() => setType(k)}>{l}</button>)}</div>
      <form className="search-bar" onSubmit={(e) => { e.preventDefault(); if (q.trim()) nav(`/inv/result?type=${type}&q=${encodeURIComponent(q.trim())}`); }}>
        <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder={t[2]} maxLength={256} />
        <button className="primary">SEARCH</button>
      </form>
      <p className="muted sm">Only records that exist in the intelligence database are returned. Nothing is inferred or fabricated.</p>
    </div>
  );
}