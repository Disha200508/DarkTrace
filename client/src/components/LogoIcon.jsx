export default function LogoIcon({ size = 28, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 36 36"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`darktrace-logo-svg ${className}`}
      style={{ display: 'inline-block', verticalAlign: 'middle', flexShrink: 0 }}
    >
      <defs>
        <linearGradient id="dtLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" />
          <stop offset="50%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#a855f7" />
        </linearGradient>
        <linearGradient id="dtShieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#6366f1" stopOpacity="0.08" />
        </linearGradient>
      </defs>
      
      {/* Cyber Shield Outer Frame */}
      <polygon
        points="18,2.5 32,8.5 32,23.5 18,33.5 4,23.5 4,8.5"
        fill="url(#dtShieldGrad)"
        stroke="url(#dtLogoGrad)"
        strokeWidth="2.2"
        strokeLinejoin="round"
      />
      
      {/* Radar Ring */}
      <circle cx="18" cy="18" r="6" stroke="url(#dtLogoGrad)" strokeWidth="1.5" strokeDasharray="3 2" opacity="0.85" />
      <circle cx="18" cy="18" r="2.5" fill="url(#dtLogoGrad)" />
      
      {/* Network Edges */}
      <line x1="18" y1="12" x2="18" y2="6.5" stroke="url(#dtLogoGrad)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="18" y1="24" x2="18" y2="29.5" stroke="url(#dtLogoGrad)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="13" y1="15" x2="8.5" y2="12.5" stroke="url(#dtLogoGrad)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="23" y1="21" x2="27.5" y2="23.5" stroke="url(#dtLogoGrad)" strokeWidth="1.5" strokeLinecap="round" />

      {/* Vertex Nodes */}
      <circle cx="18" cy="6.5" r="1.8" fill="#38bdf8" />
      <circle cx="18" cy="29.5" r="1.8" fill="#a855f7" />
      <circle cx="8.5" cy="12.5" r="1.8" fill="#38bdf8" />
      <circle cx="27.5" cy="23.5" r="1.8" fill="#a855f7" />
    </svg>
  );
}
