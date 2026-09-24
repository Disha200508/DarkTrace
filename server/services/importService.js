const { parse } = require('csv-parse/sync');
const { Entity, Relationship, Evidence, Source, Investigation, Alert, ENTITY_TYPES } = require('../models');
const { normalize } = require('./searchService');

const toDate = (v) => { if (!v) return null; const d = new Date(v); return isNaN(d) ? null : d; };
const toConf = (v) => { const n = Number(v); return v === '' || v == null || !Number.isFinite(n) ? undefined : Math.max(0, Math.min(100, n)); };

exports.csvToPayload = (buffer, meta) => {
  const rows = parse(buffer, { columns: true, skip_empty_lines: true, trim: true });
  const p = { source: meta, entities: [], relationships: [], evidence: [] };
  for (const r of rows) {
    if ((r.kind || 'entity') === 'relationship')
      p.relationships.push({ fromType: r.fromType, fromValue: r.fromValue, toType: r.toType, toValue: r.toValue, type: r.relType, confidence: r.confidence, firstSeen: r.firstSeen, lastSeen: r.lastSeen });
    else p.entities.push({ type: r.type, value: r.value, label: r.label, category: r.category, confidence: r.confidence, firstSeen: r.firstSeen, lastSeen: r.lastSeen });
  }
  return p;
};

exports.ingest = async (payload) => {
  const s = payload.source;
  if (!s?.name) throw Object.assign(new Error('Payload must include source.name'), { status: 400 });
  const source = await Source.findOneAndUpdate(
    { name: s.name },
    { $setOnInsert: { type: s.type || 'dataset', reliability: s.reliability || 'unrated' }, $set: { lastImportAt: new Date() } },
    { upsert: true, new: true });

  const stats = { entitiesNew: 0, entitiesUpdated: 0, relationshipsNew: 0, evidence: 0, rejected: [] };
  const cache = new Map();

  const upsertEntity = async (e, ref) => {
    if (!e || !ENTITY_TYPES.includes(e.type) || !e.value) { stats.rejected.push(`${ref}: invalid type/value`); return null; }
    const valueNorm = normalize(e.type, e.value);
    const key = `${e.type}|${valueNorm}`;
    if (cache.has(key)) return cache.get(key);
    let doc = await Entity.findOne({ type: e.type, valueNorm });
    if (!doc) { doc = new Entity({ type: e.type, value: String(e.value).trim(), valueNorm, sourceIds: [] }); stats.entitiesNew++; }
    else stats.entitiesUpdated++;
    for (const k of ['label', 'category', 'status']) if (e[k]) doc[k] = e[k];
    const c = toConf(e.confidence); if (c !== undefined) doc.confidence = c;
    const fs = toDate(e.firstSeen), ls = toDate(e.lastSeen);
    if (fs && (!doc.firstSeen || fs < doc.firstSeen)) doc.firstSeen = fs;
    if (ls && (!doc.lastSeen || ls > doc.lastSeen)) doc.lastSeen = ls;
    if (e.attributes) { doc.attributes = { ...(doc.attributes || {}), ...e.attributes }; doc.markModified('attributes'); }
    if (e.profile) { doc.profile = { ...(doc.profile || {}), ...e.profile }; doc.markModified('profile'); }
    if (!doc.sourceIds.some((x) => x.equals(source._id))) doc.sourceIds.push(source._id);
    await doc.save();
    cache.set(key, doc);
    return doc;
  };

  (payload.entities || []).forEach(() => {});
  for (const [i, e] of (payload.entities || []).entries()) await upsertEntity(e, `entity[${i}]`);

  const newRels = [];
  for (const [i, r] of (payload.relationships || []).entries()) {
    const a = await upsertEntity({ type: r.fromType, value: r.fromValue }, `rel[${i}].from`);
    const b = await upsertEntity({ type: r.toType, value: r.toValue }, `rel[${i}].to`);
    if (!a || !b || !r.type) { if (a && b) stats.rejected.push(`rel[${i}]: missing type`); continue; }
    const existing = await Relationship.findOne({ from: a._id, to: b._id, type: r.type });
    const doc = await Relationship.findOneAndUpdate(
      { from: a._id, to: b._id, type: r.type },
      { $set: { ...(toConf(r.confidence) !== undefined && { confidence: toConf(r.confidence) }), ...(toDate(r.firstSeen) && { firstSeen: toDate(r.firstSeen) }), ...(toDate(r.lastSeen) && { lastSeen: toDate(r.lastSeen) }) },
        $addToSet: { sourceIds: source._id }, $setOnInsert: { method: 'imported', status: 'confirmed' } },
      { upsert: true, new: true });
    if (!existing) { stats.relationshipsNew++; newRels.push(doc); }
  }

  for (const [i, x] of (payload.evidence || []).entries()) {
    if (!x.title) { stats.rejected.push(`evidence[${i}]: missing title`); continue; }
    const ids = [];
    for (const ref of x.entities || []) { const d = await upsertEntity(ref, `evidence[${i}]`); if (d) ids.push(d._id); }
    await Evidence.create({ title: x.title, type: x.type, content: x.content, entityIds: ids, sourceId: source._id, observedAt: toDate(x.observedAt), confidence: toConf(x.confidence) });
    stats.evidence++;
  }

  // Real alerts: only for investigations that already contain an endpoint of a newly created relationship
  for (const r of newRels) {
    const invs = await Investigation.find({ status: { $nin: ['Closed', 'Archived'] }, entityIds: { $in: [r.from, r.to] } }).select('_id owner name').lean();
    for (const inv of invs)
      await Alert.create({ kind: 'new_relationship', severity: r.confidence >= 75 ? 'High' : r.confidence >= 50 ? 'Medium' : 'Low', message: `New "${r.type}" relationship imported that touches investigation "${inv.name}".`, owner: inv.owner, investigation: inv._id });
  }
  if (stats.rejected.length)
    await Alert.create({ kind: 'data_issue', severity: 'Medium', message: `Import from "${source.name}" rejected ${stats.rejected.length} record(s).` });

  return { source: source.name, ...stats, rejected: stats.rejected.slice(0, 50) };
};