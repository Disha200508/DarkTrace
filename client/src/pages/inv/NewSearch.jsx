import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const TYPES = [['username', 'Username / Handle', 'e.g. alpha_user'], ['pgp', 'PGP Fingerprint', 'Full fingerprint or key ID'], ['wallet', 'Cryptocurrency Wallet', 'Wallet address'],
  ['forum', 'Forum Account', 'Account name'], ['marketplace', 'Marketplace Account', 'Vendor / account name'], ['domain', 'Domain', 'example.onion / example.com'],
  ['infrastructure', 'Infrastructure Indicator', 'IP, hostname, certificate hash…'], ['actor', 'Actor ID', 'Actor identifier or name']];

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