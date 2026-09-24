import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

const TYPE_COLORS = {
  wallet: '#fbbf24',
  handle: '#38bdf8',
  email: '#34d399',
  ip: '#ff5d5d',
  domain: '#a855f7',
  phone: '#f97316',
  org: '#ec4899',
  person: '#2dd4bf',
};

export default function Graph({ entities = [], relationships = [], onSelect, onExpand }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const elements = [
      ...entities.map((e) => ({
        data: {
          id: e._id,
          label: e.label || e.value || e._id,
          type: e.type,
          color: TYPE_COLORS[e.type] || '#2dd4bf',
        },
      })),
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
            'color': '#e6edf3',
            'font-size': '11px',
            'font-family': 'Inter, system-ui, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'width': 28,
            'height': 28,
            'border-width': 2,
            'border-color': '#10151c',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#ffffff',
            'shadow-blur': 10,
            'shadow-color': '#2dd4bf',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#232c3a',
            'target-arrow-color': '#232c3a',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'color': '#7d8ba1',
            'font-size': '9px',
            'text-rotation': 'autorotate',
            'text-margin-y': -8,
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
            'line-color': '#2dd4bf',
            'target-arrow-color': '#2dd4bf',
            'width': 3,
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        padding: 40,
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
        <button className="sm" onClick={handleZoomIn}>+</button>
        <button className="sm" onClick={handleZoomOut}>-</button>
        <button className="sm" onClick={handleFit}>Fit</button>
        <button className="sm" onClick={handleReset}>Reset</button>
      </div>
      <div ref={containerRef} className="graph" />
      <div className="legend">
        <span><i style={{ background: '#fbbf24' }} /> Wallet</span>
        <span><i style={{ background: '#38bdf8' }} /> Handle</span>
        <span><i style={{ background: '#34d399' }} /> Email</span>
        <span><i style={{ background: '#ff5d5d' }} /> IP</span>
        <span><i style={{ background: '#a855f7' }} /> Domain</span>
        <span><i style={{ background: '#2dd4bf' }} /> Person</span>
        <span><i className="dash" /> Proposed edge</span>
      </div>
    </div>
  );
}
