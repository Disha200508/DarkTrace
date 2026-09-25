import { useState, useEffect, useRef } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth } from '../auth';
import { useTheme } from '../theme';
import { errMsg } from '../api';
import LogoIcon from '../components/LogoIcon';

export default function Login({ portal = 'investigator' }) {
  const { user, login } = useAuth();
  const nav = useNavigate();
  const { theme, toggleTheme } = useTheme();

  // Sign in state
  const [loginId, setLoginId] = useState('');
  const [loginPw, setLoginPw] = useState('');
  const [showLoginPw, setShowLoginPw] = useState(false);
  const [busy, setBusy] = useState(false);

  const canvasRef = useRef(null);
  const admin = portal === 'admin';

  // Redirect if already authenticated
  if (user) {
    return <Navigate to={user.role === 'admin' ? '/admin' : '/inv'} replace />;
  }

  // Interactive Background Canvas (Cyber Node Graph Animation)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    let width = (canvas.width = canvas.parentElement.offsetWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement.offsetHeight || window.innerHeight);

    const handleResize = () => {
      if (!canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.offsetWidth || window.innerWidth;
      height = canvas.height = canvas.parentElement.offsetHeight || window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Particle nodes
    const nodeCount = Math.floor((width * height) / 18000);
    const nodes = Array.from({ length: Math.max(25, nodeCount) }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      radius: Math.random() * 2 + 1.5,
      pulse: Math.random() * Math.PI,
    }));

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
      const nodeColor = isDark ? 'rgba(59, 130, 246, ' : 'rgba(37, 99, 235, ';
      const lineColor = isDark ? 'rgba(59, 130, 246, ' : 'rgba(37, 99, 235, ';

      // Draw connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 130) {
            const alpha = (1 - dist / 130) * (isDark ? 0.25 : 0.15);
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = lineColor + alpha + ')';
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }

      // Draw nodes
      nodes.forEach((node) => {
        node.x += node.vx;
        node.y += node.vy;
        node.pulse += 0.03;

        if (node.x < 0 || node.x > width) node.vx *= -1;
        if (node.y < 0 || node.y > height) node.vy *= -1;

        const pulseRadius = node.radius + Math.sin(node.pulse) * 0.8;
        const alpha = 0.5 + Math.sin(node.pulse) * 0.3;

        ctx.beginPath();
        ctx.arc(node.x, node.y, Math.max(0.5, pulseRadius), 0, Math.PI * 2);
        ctx.fillStyle = nodeColor + alpha + ')';
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [theme]);

  // Submit Sign In
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    if (!loginId || !loginPw) {
      toast.error('Please enter your identifier and password');
      return;
    }
    setBusy(true);
    try {
      const u = await login(portal, loginId, loginPw);
      toast.success(`Welcome back, ${u.fullName || u.username}`);
      nav(u.role === 'admin' ? '/admin' : '/inv');
    } catch (err) {
      toast.error(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-container">
      {/* BACKGROUND CANVAS & GRID OVERLAY */}
      <div className="auth-bg-wrapper">
        <canvas ref={canvasRef} className="auth-canvas" />
        <div className="auth-grid-overlay" />
      </div>

      {/* TOPBAR */}
      <header className="auth-topbar">
        <div className="auth-brand-logo">
          <LogoIcon size={38} />
          <div className="brand-text-stack">
            <span className="brand-title">DarkTrace</span>
            <span className="brand-badge">CYBER INTELLIGENCE</span>
          </div>
        </div>

        <div className="auth-topbar-right">
          <div className="clearance-badge">
            <span className="live-dot green" />
            <span className="badge-text">256-BIT ZERO-TRUST SESSION</span>
          </div>

          <button className="theme-toggle" onClick={toggleTheme} type="button">
            {theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
          </button>
        </div>
      </header>

      {/* MAIN LAYOUT SPLIT */}
      <div className="auth-content-split">
        {/* LEFT COLUMN: VISUAL SHOWCASE */}
        <div className="auth-showcase-panel">
          <div className="showcase-content">
            <div className="cyber-tag">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              <span>CLASSIFIED THREAT DE-ANONYMIZATION</span>
            </div>

            <h1 className="showcase-title">
              Intelligence Platform for <span className="text-gradient">Threat Actor</span> Attribution
            </h1>

            <p className="showcase-desc">
              Correlate darkweb handles, crypto wallets, PGP keys, and breach records across millions of entities with automated AI graph analysis.
            </p>

            {/* LIVE METRICS CARDS */}
            <div className="showcase-stats-grid">
              <div className="showcase-stat-card">
                <div className="stat-icon blue">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10z" />
                  </svg>
                </div>
                <div>
                  <span className="stat-val">14.2M+</span>
                  <span className="stat-lbl">Entity Correlations</span>
                </div>
              </div>

              <div className="showcase-stat-card">
                <div className="stat-icon purple">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                    <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                    <line x1="12" y1="22.08" x2="12" y2="12" />
                  </svg>
                </div>
                <div>
                  <span className="stat-val">&lt; 45ms</span>
                  <span className="stat-lbl">Graph Query Speed</span>
                </div>
              </div>
            </div>

            {/* AUDIT NOTICE */}
            <div className="showcase-notice">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>Restricted Access. Every search, export, and clearance change is immutably logged for audit compliance.</span>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: AUTH CARD (SIGN IN ONLY) */}
        <div className="auth-form-panel">
          <div className="auth-card-glass">
            {/* PORTAL INDICATOR */}
            <div className="auth-card-header">
              <div className="portal-pill-badge">
                {admin ? (
                  <span className="portal-tag admin-tag">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    ADMIN GATEKEEPER
                  </span>
                ) : (
                  <span className="portal-tag inv-tag">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>
                    INVESTIGATOR PORTAL
                  </span>
                )}
              </div>
            </div>

            {/* FORM TITLE */}
            <div className="auth-title-block">
              <h2>
                {admin ? 'Administrator Sign-In' : 'Investigator Sign-In'}
              </h2>
              <p>
                {admin
                  ? 'Enter your system administrator credentials to access the console'
                  : 'Enter your accredited credentials or investigator ID to proceed'}
              </p>
            </div>

            {/* SIGN IN FORM */}
            <form className="auth-form" onSubmit={handleLoginSubmit}>
              <div className="form-group">
                <label htmlFor="login-id">
                  {admin ? 'Admin Username' : 'Investigator ID / Username'}
                </label>
                <div className="input-icon-wrap">
                  <svg className="field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                  <input
                    id="login-id"
                    type="text"
                    placeholder={admin ? 'Username' : 'Investigator ID / Username'}
                    value={loginId}
                    onChange={(e) => setLoginId(e.target.value)}
                    autoFocus
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <div className="label-with-action">
                  <label htmlFor="login-pw">Password</label>
                </div>
                <div className="input-icon-wrap">
                  <svg className="field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                  <input
                    id="login-pw"
                    type={showLoginPw ? 'text' : 'password'}
                    placeholder="••••••••••••"
                    value={loginPw}
                    onChange={(e) => setLoginPw(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    className="eye-toggle-btn"
                    onClick={() => setShowLoginPw(!showLoginPw)}
                    title={showLoginPw ? 'Hide Password' : 'Show Password'}
                  >
                    {showLoginPw ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                        <line x1="1" y1="1" x2="23" y2="23" />
                      </svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              <button type="submit" className="auth-submit-btn primary" disabled={busy}>
                {busy ? (
                  <span className="btn-loading">
                    <span className="spinner-icon" /> Authenticating...
                  </span>
                ) : (
                  <>
                    <span>Sign In</span>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </svg>
                  </>
                )}
              </button>
            </form>

            {/* SWITCH PORTAL FOOTER LINK */}
            <div className="auth-card-footer">
              <Link
                className="alt-portal-link"
                to={admin ? '/login' : '/admin/login'}
              >
                {admin ? 'Switch to Investigator Portal →' : 'Switch to Admin Portal →'}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}