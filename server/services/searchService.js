const { Entity, Relationship, Evidence, Source } = require('../models');

const TYPE_MAP = {
  username: 'username', pgp: 'pgp', wallet: 'wallet', forum: 'forum_account',
  marketplace: 'marketplace_account', domain: 'domain', infrastructure: 'infrastructure', actor: 'actor',
};
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const normalize = (type, v) => {
  v = String(v).trim();
  if (type === 'pgp') return v.replace(/\s+/g, '').replace(/^0x/i, '').toLowerCase();
  if (type === 'wallet') return v.startsWith('0x') ? v.toLowerCase() : v; // BTC-style addresses are case-sensitive
  return v.toLowerCase();
};

async function findRoots(type, query) {
  const et = TYPE_MAP[type];
  if (!et) throw Object.assign(new Error('Unsupported search type'), { status: 400 });
  const norm = normalize(et, query);
  let f;
  if (et === 'pgp' && norm.length >= 8) f = { type: et, valueNorm: new RegExp(esc(norm) + '$') }; // full fingerprint or key ID
  else if (et === 'actor') f = { type: et, $or: [{ valueNorm: norm }, { label: new RegExp('^' + esc(query.trim()) + '$', 'i') }] };
  else f = { type: et, valueNorm: norm };
  return Entity.find(f).limit(20).lean();
}

async function expand(rootIds, maxDepth = 3, cap = 400) {
  const seen = new Set(rootIds.map(String));
  const edges = new Map();
  let frontier = [...rootIds];
  for (let d = 0; d < maxDepth && frontier.length && seen.size < cap; d++) {
    const rels = await Relationship.find({ status: { $ne: 'rejected' }, $or: [{ from: { $in: frontier } }, { to: { $in: frontier } }] }).lean();
    const next = [];
    for (const r of rels) {
      edges.set(String(r._id), r);
      for (const id of [r.from, r.to]) if (!seen.has(String(id)) && seen.size < cap) { seen.add(String(id)); next.push(id); }
    }
    frontier = next;
  }
  return { ids: [...seen], rels: [...edges.values()] };
}

function assess(rels, sources) {
  const c = rels.map((r) => r.confidence).filter(Number.isFinite);
  const avg = c.length ? Math.round(c.reduce((a, b) => a + b, 0) / c.length) : null;
  const level = avg == null ? 'unassessed' : avg >= 75 && sources.length >= 2 ? 'high' : avg >= 50 ? 'moderate' : 'low';
  return {
    averageRelationshipConfidence: avg, relationshipCount: rels.length, independentSources: sources.length, level,
    method: 'Mean of stored relationship confidences. "High" additionally requires at least 2 independent sources.',
  };
}

function buildTimeline(entities, rels, evidence, nameOf) {
  const ev = [];
  for (const e of entities) {
    if (e.firstSeen) ev.push({ date: e.firstSeen, kind: 'observed', title: `${e.type.replace('_', ' ')} observed: ${e.label || e.value}`, entityId: e._id, sourceIds: e.sourceIds, confidence: e.confidence });
    for (const t of e.attributes?.transactions || [])
      if (t.time) ev.push({ date: t.time, kind: 'transaction', title: `Transaction on ${e.label || e.value}${t.amount != null ? ` (${t.amount})` : ''}`, entityId: e._id, sourceIds: e.sourceIds, detail: t });
  }
  for (const r of rels) if (r.firstSeen) ev.push({ date: r.firstSeen, kind: 'relationship', title: `${r.type}: ${nameOf(r.from)} → ${nameOf(r.to)}`, relationshipId: r._id, sourceIds: r.sourceIds, confidence: r.confidence });
  for (const x of evidence) if (x.observedAt) ev.push({ date: x.observedAt, kind: 'evidence', title: x.title, evidenceId: x._id, sourceIds: x.sourceId ? [x.sourceId] : [], confidence: x.confidence });
  return ev.sort((a, b) => new Date(a.date) - new Date(b.date));
}

async function loadWorkspace(rootIds, ids, rels) {
  const [entities, evidence] = await Promise.all([
    Entity.find({ _id: { $in: ids } }).lean(),
    Evidence.find({ entityIds: { $in: ids } }).lean(),
  ]);
  const usage = new Map();
  const bump = (arr) => (arr || []).forEach((s) => usage.set(String(s), (usage.get(String(s)) || 0) + 1));
  entities.forEach((e) => bump(e.sourceIds)); rels.forEach((r) => bump(r.sourceIds)); evidence.forEach((x) => x.sourceId && bump([x.sourceId]));
  const sourceDocs = await Source.find({ _id: { $in: [...usage.keys()] } }).lean();
  const sources = sourceDocs.map((s) => ({ ...s, recordsUsed: usage.get(String(s._id)) }));

  const byId = Object.fromEntries(entities.map((e) => [String(e._id), e]));
  const nameOf = (id) => byId[String(id)]?.label || byId[String(id)]?.value || String(id);
  const validRels = rels.filter((r) => byId[String(r.from)] && byId[String(r.to)]);
  const actors = entities.filter((e) => e.type === 'actor');
  const dates = entities.flatMap((e) => [e.firstSeen, e.lastSeen]).filter(Boolean).map((d) => new Date(d));
  const counts = {}; entities.forEach((e) => (counts[e.type] = (counts[e.type] || 0) + 1));

  return {
    entities, relationships: validRels, evidence, sources,
    timeline: buildTimeline(entities, validRels, evidence, nameOf),
    summary: {
      counts, actors,
      category: actors[0]?.category, status: actors[0]?.status,
      firstSeen: dates.length ? new Date(Math.min(...dates)) : null,
      lastSeen: dates.length ? new Date(Math.max(...dates)) : null,
      confidence: assess(validRels, sources),
    },
  };
}

async function search(type, query) {
  const roots = await findRoots(type, query);
  if (!roots.length) return { query: { type, query }, roots: [], entities: [], relationships: [], evidence: [], sources: [], timeline: [], summary: { counts: {}, actors: [], confidence: assess([], []) } };
  const rootIds = roots.map((r) => r._id);
  const { ids, rels } = await expand(rootIds);
  const ws = await loadWorkspace(rootIds, ids, rels);
  return { query: { type, query }, roots, ...ws };
}

async function neighbors(entityId) {
  const { ids, rels } = await expand([entityId], 1, 100);
  const ws = await loadWorkspace([entityId], ids, rels);
  return { entities: ws.entities, relationships: ws.relationships, sources: ws.sources };
}

module.exports = { search, neighbors, normalize, TYPE_MAP, assess };