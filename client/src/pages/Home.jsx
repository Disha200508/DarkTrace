import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';
import { useTheme } from '../theme';

export default function Home() {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const nav = useNavigate();
  const [sampleQuery, setSampleQuery] = useState('DarkWolf');
  const [demoResult, setDemoResult] = useState(null);
  const [searching, setSearching] = useState(false);
  const [activeTab, setActiveTab] = useState('actor');

  const handleDemoSearch = (e) => {
    e.preventDefault();
    if (!sampleQuery.trim()) return;
    setSearching(true);
    setTimeout(() => {
      setDemoResult({
        query: sampleQuery,
        actor: sampleQuery.toLowerCase().includes('wolf') ? 'DarkWolf' : 'GhostNode_99',
        confidence: 94,
        connectedEntities: 14,
        sources: ['Darkweb Forum (XSS)', 'Telegram Channel', 'BTC Wallet Trans'],
        attributes: {
          primaryHandle: sampleQuery,
          pgpFingerprint: '4A2B 88F1 90CC E310',
          wallet: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
          activityHours: '18:00 - 04:00 UTC',
          riskLevel: 'HIGH THREAT',
        }
      });
      setSearching(false);
    }, 500);
  };

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="home-container">
      {/* BACKGROUND CYBER GRID OVERLAY */}
      <div className="home-cyber-grid" />

      {/* TOP NAVBAR (NO BOTTOM LINE) */}
      <nav className="home-nav clean-nav">
        <div className="home-nav-left">
          <span className="logo neon-glow">◈</span>
          <span className="home-brand">DarkTrace <small className="glow-badge">INTELLIGENCE</small></span>
        </div>

        <div className="home-nav-links">
          <a href="#hero" onClick={(e) => { e.preventDefault(); scrollTo('hero'); }}>Overview</a>
          <a href="#capabilities" onClick={(e) => { e.preventDefault(); scrollTo('capabilities'); }}>Capabilities</a>
          <a href="#pipeline" onClick={(e) => { e.preventDefault(); scrollTo('pipeline'); }}>Pipeline</a>
          <a href="#radar" onClick={(e) => { e.preventDefault(); scrollTo('radar'); }}>Threat Radar</a>
          <a href="#platform" onClick={(e) => { e.preventDefault(); scrollTo('platform'); }}>Live Demo</a>
        </div>

        <div className="home-nav-right">
          <button className="theme-toggle" onClick={toggleTheme} type="button">
            {theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
          </button>
          {user ? (
            <button className="vibrant-sign-btn" onClick={() => nav(user.role === 'admin' ? '/admin' : '/inv')}>
              Go to Dashboard →
            </button>
          ) : (
            <div className="row" style={{ gap: '10px' }}>
              
              <Link to="/login" className="vibrant-sign-btn">
                Sign In →
              </Link>
            </div>
          )}
        </div>
      </nav>

      {/* HERO SECTION WITH VECTOR SVG GRAPHIC & COMPACT FLOATING BADGES */}
      <section id="hero" className="home-hero-section">
        {/* SVG BACKGROUND NETWORK GRAPHIC */}
        <div className="hero-svg-bg">
          <svg width="100%" height="100%" viewBox="0 0 1000 400" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M150,200 Q300,100 500,200 T850,200" stroke="var(--accent)" strokeWidth="1.5" strokeDasharray="6 6" opacity="0.4" />
            <path d="M100,150 Q400,300 900,150" stroke="#10b981" strokeWidth="1" opacity="0.3" />
            <circle cx="150" cy="200" r="6" fill="#10b981" className="glow-circle" />
            <circle cx="500" cy="200" r="8" fill="#3b82f6" className="glow-circle" />
            <circle cx="850" cy="200" r="6" fill="#8b5cf6" className="glow-circle" />
            <circle cx="300" cy="130" r="4" fill="#06b6d4" />
            <circle cx="700" cy="270" r="4" fill="#10b981" />
          </svg>
        </div>

        <div className="hero-status-pill">
          <span className="status-dot-pulse" />
          <span>SYSTEM ONLINE · THREAT INTELLIGENCE ENVIRONMENT</span>
        </div>

        <div className="hero-content-wrapper">
          {/* FLOATING SIDE BADGE 1 (COMPACT UP-DOWN FLOAT) */}
          <div className="hero-compact-float float-left-badge">
            <div className="float-badge-icon green">🟢</div>
            <div className="float-badge-info">
              <span className="float-tag">ACTOR DETECTED</span>
              <div className="float-val">DarkWolf <span className="float-pct">94%</span></div>
            </div>
          </div>

          {/* MAIN HERO TEXT */}
          <div className="hero-text-center">
            <h1 className="hero-title">
              See Beyond the <span className="highlight-text neon-gradient">Anonymous.</span>
            </h1>

            <p className="hero-subtitle">
              DarkTrace connects fragmented dark-web signals, digital identities, infrastructure,
              and blockchain traces to uncover hidden threat relationships and support actor attribution.
            </p>

            <div className="hero-actions">
              <button className="primary xl glow-btn" onClick={() => nav(user ? (user.role === 'admin' ? '/admin' : '/inv') : '/login')}>
                Start Investigation →
              </button>
              <button className="xl ghost-btn" onClick={() => scrollTo('capabilities')}>
                Explore Platform ↓
              </button>
            </div>
          </div>

          {/* FLOATING SIDE BADGE 2 (COMPACT DOWN-UP FLOAT) */}
          <div className="hero-compact-float float-right-badge">
            <div className="float-badge-icon blue">◈</div>
            <div className="float-badge-info">
              <span className="float-tag">RELATIONSHIPS</span>
              <div className="float-val">12 Entities <span className="float-pct highlight">+12</span></div>
            </div>
          </div>
        </div>

        <div className="hero-feature-tags">
          <span>• SIMULATED INTELLIGENCE</span>
          <span>• RELATIONSHIP ANALYSIS</span>
          <span>• ACTOR ATTRIBUTION</span>
          <span>• BLOCKCHAIN TRACING</span>
        </div>
      </section>

      {/* INTELLIGENCE CAPABILITIES SECTION WITH GRAPHIC ILLUSTRATION */}
      <section id="capabilities" className="home-section">
        <div className="section-tag">INTELLIGENCE CAPABILITIES</div>
        <h2 className="section-title">
          Understand the threat. <span className="highlight-blue">Connect the evidence.</span>
        </h2>
        <p className="section-subtitle">
          DarkTrace brings multiple investigation capabilities together in one unified intelligence environment.
        </p>

        <div className="capabilities-grid">
          {/* Card 1 */}
          <div className="cap-card glow-card">
            <div className="cap-card-head">
              <div className="cap-icon blue">⬢</div>
              <span className="cap-num">01</span>
            </div>
            <div className="cap-tag">INFRASTRUCTURE</div>
            <h3>Infrastructure Intelligence</h3>
            <p>
              Discover domains, IP indicators, hosting patterns, and network topology associated with suspicious threat activity.
            </p>
            {/* SVG Graphic */}
            <div className="cap-svg-visual">
              <svg width="100%" height="50" viewBox="0 0 200 50">
                <rect x="10" y="15" width="40" height="20" rx="4" fill="var(--panel2)" stroke="var(--blue)" strokeWidth="1.5"/>
                <line x1="50" y1="25" x2="90" y2="25" stroke="var(--line)" strokeDasharray="3 3"/>
                <rect x="90" y="15" width="40" height="20" rx="4" fill="var(--panel2)" stroke="var(--accent)" strokeWidth="1.5"/>
                <line x1="130" y1="25" x2="170" y2="25" stroke="var(--line)" strokeDasharray="3 3"/>
                <rect x="170" y="15" width="20" height="20" rx="4" fill="var(--green-bg)" stroke="var(--green)" strokeWidth="1.5"/>
              </svg>
            </div>
            <div className="cap-badges">
              <span>IP</span>
              <span>DNS</span>
              <span>OSINT</span>
              <span className="accent">INFRA →</span>
            </div>
          </div>

          {/* Card 2 */}
          <div className="cap-card active-card glow-card">
            <div className="cap-card-head">
              <div className="cap-icon purple">◈</div>
              <span className="cap-num">02</span>
            </div>
            <div className="cap-tag">RELATIONSHIP GRAPH</div>
            <h3>Actor Relationship Mapping</h3>
            <p>
              Connect handles, crypto wallets, PGP keys, forums, marketplaces, and infrastructure into a structured relationship graph.
            </p>
            <div className="mini-graph-demo">
              <div className="graph-dot g1" />
              <div className="graph-line l1" />
              <div className="graph-dot g2" />
              <div className="graph-line l2" />
              <div className="graph-dot g3" />
            </div>
          </div>

          {/* Card 3 */}
          <div className="cap-card glow-card">
            <div className="cap-card-head">
              <div className="cap-icon green">◎</div>
              <span className="cap-num">03</span>
            </div>
            <div className="cap-tag">AI ANALYSIS</div>
            <h3>Persona & Behaviour Analysis</h3>
            <p>
              Examine behavioural patterns, writing samples, and digital identifiers to calculate similarity scores between threat personas.
            </p>
            <div className="progress-bars">
              <div className="bar-row">
                <span>Writing Pattern</span>
                <div className="bar-track"><div className="bar-fill" style={{ width: '88%' }} /></div>
                <span>88%</span>
              </div>
              <div className="bar-row">
                <span>Activity Pattern</span>
                <div className="bar-track"><div className="bar-fill" style={{ width: '92%' }} /></div>
                <span>92%</span>
              </div>
              <div className="bar-row">
                <span>Identity Match</span>
                <div className="bar-track"><div className="bar-fill highlight" style={{ width: '95%' }} /></div>
                <span>95%</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* RADAR MONITORING SECTION */}
      <section id="radar" className="home-section dark-bg">
        <div className="section-tag">LIVE THREAT MONITORING</div>
        <h2 className="section-title">Threat Radar & Node Matrix</h2>
        <p className="section-subtitle">
          Real-time spatial correlation scanning across darknet intelligence feeds.
        </p>

        <div className="radar-grid-wrapper">
          {/* Animated Radar Widget */}
          <div className="radar-widget-card glow-card">
            <div className="radar-header">
              <span className="status-dot-pulse" />
              <h4>SPATIAL RADAR SCANNER</h4>
            </div>
            <div className="radar-circle-outer">
              <div className="radar-sweep-line" />
              <div className="radar-target t1" title="DarkWolf (Actor)" />
              <div className="radar-target t2" title="1A1zP... (Wallet)" />
              <div className="radar-target t3" title="185.220... (IP Node)" />
            </div>
            <div className="radar-footer">
              <span>ACTIVE TARGET: <b>DarkWolf</b></span>
              <span className="radar-freq">FREQ: 2.4 GHz</span>
            </div>
          </div>

          {/* Threat Matrix Breakdown */}
          <div className="radar-matrix-card glow-card">
            <h4>Correlated Threat Matrix</h4>
            <p className="sm muted">Select threat category to inspect live entity signals</p>

            <div className="matrix-tabs">
              <button className={activeTab === 'actor' ? 'on' : ''} onClick={() => setActiveTab('actor')}>
                Actors
              </button>
              <button className={activeTab === 'wallet' ? 'on' : ''} onClick={() => setActiveTab('wallet')}>
                Wallets
              </button>
              <button className={activeTab === 'infra' ? 'on' : ''} onClick={() => setActiveTab('infra')}>
                Infrastructure
              </button>
            </div>

            <div className="matrix-content-box">
              {activeTab === 'actor' && (
                <div className="matrix-details">
                  <div className="matrix-row"><span>Persona Handle:</span> <b>DarkWolf</b></div>
                  <div className="matrix-row"><span>PGP Key ID:</span> <code>4A2B 88F1 90CC E310</code></div>
                  <div className="matrix-row"><span>Forum Presence:</span> <span>XSS.is, BreachForums, RaidForums</span></div>
                  <div className="matrix-row"><span>Risk Rating:</span> <span className="badge red">CRITICAL THREAT (94%)</span></div>
                </div>
              )}
              {activeTab === 'wallet' && (
                <div className="matrix-details">
                  <div className="matrix-row"><span>BTC Address:</span> <code>1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa</code></div>
                  <div className="matrix-row"><span>Total Volume:</span> <b>48.25 BTC (~$3.1M)</b></div>
                  <div className="matrix-row"><span>Transaction Count:</span> <span>142 Transactions</span></div>
                  <div className="matrix-row"><span>Mixer Usage:</span> <span className="badge amber">Tornado Cash / CoinJoin</span></div>
                </div>
              )}
              {activeTab === 'infra' && (
                <div className="matrix-details">
                  <div className="matrix-row"><span>Exit Node IP:</span> <code>185.220.101.5</code></div>
                  <div className="matrix-row"><span>Host Location:</span> <b>Offshore / Bulletproof VPS</b></div>
                  <div className="matrix-row"><span>Associated Domain:</span> <code>shadow-market.onion</code></div>
                  <div className="matrix-row"><span>Status:</span> <span className="badge green">ACTIVE SIGNAL</span></div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* PIPELINE SECTION */}
      <section id="pipeline" className="home-section">
        <div className="section-tag">INVESTIGATION PIPELINE</div>
        <h2 className="section-title">
          From signal <span className="highlight-purple">to attribution.</span>
        </h2>
        <p className="section-subtitle">
          Follow the investigation pipeline as DarkTrace transforms fragmented signals into structured threat intelligence.
        </p>

        <div className="pipeline-grid">
          {/* Step 1 */}
          <div className="pipe-card glow-card">
            <span className="pipe-num">01</span>
            <div className="pipe-icon">⚡</div>
            <div className="pipe-tag">INPUT</div>
            <h4>Collect</h4>
            <p>Gather relevant signals from darkweb markets, forums, and leak sources.</p>
            <div className="pipe-pills">
              <span>Forums</span><span>Leaks</span><span>Markets</span>
            </div>
          </div>

          {/* Step 2 */}
          <div className="pipe-card glow-card">
            <span className="pipe-num">02</span>
            <div className="pipe-icon">◈</div>
            <div className="pipe-tag">EXTRACTION</div>
            <h4>Extract</h4>
            <p>Identify handles, crypto wallets, PGP fingerprints, and domain indicators.</p>
            <div className="pipe-pills">
              <span>Actors</span><span>Wallets</span><span>Domains</span>
            </div>
          </div>

          {/* Step 3 */}
          <div className="pipe-card active-pipe glow-card">
            <span className="pipe-num">03</span>
            <div className="pipe-icon">⬡</div>
            <div className="pipe-tag">CORRELATION</div>
            <h4>Connect</h4>
            <p>Discover relationships between seemingly unrelated digital entities.</p>
            <div className="pipe-graph-viz">
              <span className="viz-dot" />
              <span className="viz-line" />
              <span className="viz-dot active" />
              <span className="viz-line" />
              <span className="viz-dot" />
            </div>
          </div>

          {/* Step 4 */}
          <div className="pipe-card glow-card">
            <span className="pipe-num">04</span>
            <div className="pipe-icon">🎯</div>
            <div className="pipe-tag">ANALYSIS</div>
            <h4>Analyze</h4>
            <p>Evaluate threat risk, activity times, confidence, and behavioral match.</p>
            <div className="pipe-meter">
              <span>CONFIDENCE</span>
              <b>91%</b>
            </div>
          </div>

          {/* Step 5 */}
          <div className="pipe-card glow-card">
            <span className="pipe-num">05</span>
            <div className="pipe-icon">❖</div>
            <div className="pipe-tag">OUTPUT</div>
            <h4>Attribute</h4>
            <p>Build an evidence-backed actor profile for official investigation.</p>
            <div className="pipe-badge-box">
              <span>DARKWOLF</span>
              <small>91% MATCH</small>
            </div>
          </div>
        </div>

        <div className="pipeline-status-bar glow-card">
          <span className="status-dot-pulse" />
          <b>PIPELINE ACTIVE</b>
          <div className="pipeline-flow-steps">
            <span>SIGNAL</span> ➔ <span>ENTITY</span> ➔ <span>RELATIONSHIP</span> ➔ <span>ANALYSIS</span> ➔ <span className="highlight">ATTRIBUTION</span>
          </div>
        </div>
      </section>

      {/* LIVE DEMO SEARCH PLAYGROUND */}
      <section id="platform" className="home-section dark-bg">
        <div className="section-tag">INTERACTIVE DEMO</div>
        <h2 className="section-title">Test Threat Correlation</h2>
        <p className="section-subtitle">
          Type an example identifier below to test real-time threat intelligence correlation.
        </p>

        <div className="demo-box glow-card">
          <form className="demo-search-form" onSubmit={handleDemoSearch}>
            <input
              type="text"
              value={sampleQuery}
              onChange={(e) => setSampleQuery(e.target.value)}
              placeholder="e.g. DarkWolf, 1A1zP1eP..., darkwolf@proton.me"
              required
            />
            <button className="primary glow-btn" type="submit" disabled={searching}>
              {searching ? 'Correlating…' : 'Analyze Signal'}
            </button>
          </form>

          {demoResult && (
            <div className="demo-result-card">
              <div className="demo-res-head">
                <div>
                  <span className="badge green">Match Found</span>
                  <h3>Actor Attribution: <b>{demoResult.actor}</b></h3>
                </div>
                <div className="demo-score">
                  <span>Confidence Score</span>
                  <b>{demoResult.confidence}%</b>
                </div>
              </div>

              <div className="demo-res-grid">
                <div className="demo-res-item">
                  <span>Primary Handle</span>
                  <code>{demoResult.attributes.primaryHandle}</code>
                </div>
                <div className="demo-res-item">
                  <span>Crypto Wallet</span>
                  <code>{demoResult.attributes.wallet}</code>
                </div>
                <div className="demo-res-item">
                  <span>PGP Fingerprint</span>
                  <code>{demoResult.attributes.pgpFingerprint}</code>
                </div>
                <div className="demo-res-item">
                  <span>Activity Pattern</span>
                  <span>{demoResult.attributes.activityHours}</span>
                </div>
              </div>

              <div className="demo-res-foot">
                <span>Sources Correlated: <b>{demoResult.sources.join(' · ')}</b></span>
                <button className="sm primary glow-btn" onClick={() => nav(user ? '/inv/search' : '/login')}>
                  Open Full Workspace →
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* FOOTER CTA */}
      <footer className="home-footer">
        <div className="footer-cta">
          <h2>Ready to de-anonymize threat actors?</h2>
          <p>Sign in to launch your workspace or access the investigator console.</p>
          <div className="row" style={{ justifyContent: 'center', marginTop: 20 }}>
            <button className="vibrant-sign-btn" style={{ padding: '12px 28px', fontSize: '15px' }} onClick={() => nav(user ? (user.role === 'admin' ? '/admin' : '/inv') : '/login')}>
              {user ? 'Enter Dashboard →' : 'Investigator Sign In →'}
            </button>
            <Link to="/admin/login" className="home-login-btn alt">
              Admin Portal →
            </Link>
          </div>
        </div>

        <div className="footer-bottom">
          <div>◈ <b>DarkTrace</b> · Threat Actor De-Anonymization & Intelligence</div>
          <small>Authorized Security & Law Enforcement Use Only. All Activity Audited.</small>
        </div>
      </footer>
    </div>
  );
}
