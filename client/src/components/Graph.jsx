import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

const TYPE_COLORS = {
  actor: '#3b82f6',
  username: '#38bdf8',
  forum_account: '#a855f7',
  marketplace_account: '#9333ea',
  pgp: '#ec4899',
  wallet: '#fbbf24',
  domain: '#10b981',
  infrastructure: '#059669',
  ip: '#ef4444',
  email: '#34d399',
  handle: '#38bdf8',
  phone: '#f97316',
  org: '#ec4899',
  person: '#3b82f6',
};

const LEGEND_ITEMS = [
  { label: 'Threat Actor', color: '#3b82f6' },
  { label: 'Username / Handle', color: '#38bdf8' },
  { label: 'Forum / Marketplace', color: '#a855f7' },
  { label: 'PGP Fingerprint', color: '#ec4899' },
  { label: 'Crypto Wallet', color: '#fbbf24' },
  { label: 'Domain / Infrastructure', color: '#10b981' },
  { label: 'IP Address', color: '#ef4444' },
  { label: 'Proposed Link', dash: true },
];

export default function Graph({ entities = [], relationships = [], onSelect, onExpand }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const elements = [
      ...entities.map((e) => {
        const isActor = e.type === 'actor';
        return {
          data: {
            id: e._id,
            label: e.label || e.value || e._id,
            type: e.type,
            color: TYPE_COLORS[e.type] || '#3b82f6',
            size: isActor ? 42 : 28,
            borderWidth: isActor ? 3 : 2,
            borderColor: isActor ? '#60a5fa' : '#1e293b',
          },
        };
      }),
      ...relationships.map((r) => ({
        data: {
          id: r._id,
          source: typeof r.from === 'object' ? r.from._id : r.from,
          target: typeof r.to === 'object' ? r.to._id : r.to,
          label: r.type || '',
          status: r.status,
        },
      })),
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'color': '#f8fafc',
            'font-size': '11px',
            'font-weight': '600',
            'font-family': 'Inter, system-ui, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 7,
            'text-outline-color': '#0f172a',
            'text-outline-width': 2,
            'width': 'data(size)',
            'height': 'data(size)',
            'border-width': 'data(borderWidth)',
            'border-color': 'data(borderColor)',
            'transition-property': 'background-color, border-color, width, height',
            'transition-duration': '0.2s',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#ffffff',
            'shadow-blur': 12,
            'shadow-color': '#3b82f6',
            'shadow-opacity': 0.8,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#334155',
            'target-arrow-color': '#334155',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'color': '#94a3b8',
            'font-size': '10px',
            'font-weight': '500',
            'text-rotation': 'autorotate',
            'text-margin-y': -8,
            'text-outline-color': '#0f172a',
            'text-outline-width': 1.5,
          },
        },
        {
          selector: 'edge[status = "proposed"]',
          style: {
            'line-style': 'dashed',
            'line-color': '#fbbf24',
            'target-arrow-color': '#fbbf24',
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#3b82f6',
            'target-arrow-color': '#3b82f6',
            'width': 3,
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        padding: 60,
        nodeRepulsion: 450000,
        idealEdgeLength: 130,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
      },
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      if (onSelect) onSelect({ kind: 'node', id: node.id() });
    });

    cy.on('dbltap', 'node', (evt) => {
      const node = evt.target;
      if (onExpand) onExpand(node.id());
    });

    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      if (onSelect) onSelect({ kind: 'edge', id: edge.id() });
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy && onSelect) {
        onSelect(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [entities, relationships]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.2);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() / 1.2);
  const handleFit = () => cyRef.current?.fit();
  const handleReset = () => cyRef.current?.reset();

  return (
    <div className="graph-box">
      <div className="graph-tools">
        <button className="sm" onClick={handleZoomIn} title="Zoom In">+</button>
        <button className="sm" onClick={handleZoomOut} title="Zoom Out">-</button>
        <button className="sm" onClick={handleFit} title="Fit to Screen">Fit</button>
        <button className="sm" onClick={handleReset} title="Reset View">Reset</button>
      </div>

      <div ref={containerRef} className="graph" />

      {/* Clean Legend Box */}
      <div className="graph-legend-bar">
        <div className="legend-title">Graph Entity Legend:</div>
        <div className="legend-items">
          {LEGEND_ITEMS.map((item, idx) => (
            <span key={idx} className="legend-chip">
              {item.dash ? (
                <i className="dash" />
              ) : (
                <i className="dot-pill" style={{ background: item.color }} />
              )}
              {item.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
