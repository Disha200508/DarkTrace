const nameOf = (m, id) => m[String(id)]?.label || m[String(id)]?.value || String(id);

exports.buildReport = ({ investigation, ws, persona, user, reportId }) => {
  const m = Object.fromEntries(ws.entities.map((e) => [String(e._id), e]));
  const src = Object.fromEntries(ws.sources.map((s) => [String(s._id), s.name]));
  const srcNames = (ids) => (ids || []).map((i) => src[String(i)]).filter(Boolean);
  const c = ws.summary.counts;
  const actors = ws.summary.actors;

  return {
    meta: { reportId, generatedAt: new Date(), generatedBy: user.fullName, investigatorId: user.investigatorId,
      investigation: { invId: investigation.invId, name: investigation.name, priority: investigation.priority, status: investigation.status, tags: investigation.tags } },
    search: investigation.search,
    executiveSummary: `Search for ${investigation.search.type} "${investigation.search.query}" matched ${ws.entities.length} connected entities `
      + `(${Object.entries(c).map(([k, v]) => `${v} ${k.replace('_', ' ')}`).join(', ') || 'none'}) linked by ${ws.relationships.length} relationships `
      + `drawn from ${ws.sources.length} source(s). ${actors.length ? `Linked actor record(s): ${actors.map((a) => a.label || a.value).join(', ')}.` : 'No actor record is linked.'} `
      + 'All associations are analytical and are not proof of identity.',
    actors: actors.map((a) => ({ id: a.value, label: a.label, category: a.category, status: a.status, confidence: a.confidence, firstSeen: a.firstSeen, lastSeen: a.lastSeen })),
    identifiers: ws.entities.filter((e) => e.type !== 'actor').map((e) => ({ type: e.type, value: e.value, label: e.label, firstSeen: e.firstSeen, lastSeen: e.lastSeen, confidence: e.confidence, sources: srcNames(e.sourceIds) })),
    relationships: ws.relationships.map((r) => ({ from: nameOf(m, r.from), to: nameOf(m, r.to), type: r.type, confidence: r.confidence, method: r.method, status: r.status, sources: srcNames(r.sourceIds) })),
    timeline: ws.timeline.map((t) => ({ date: t.date, title: t.title, kind: t.kind, sources: srcNames(t.sourceIds) })),
    persona: persona || { available: false, reason: 'Persona analysis was not run or the AI service was unavailable.' },
    infrastructure: ws.entities.filter((e) => ['infrastructure', 'domain'].includes(e.type)).map((e) => ({ indicator: e.value, type: e.type, firstSeen: e.firstSeen, lastSeen: e.lastSeen, confidence: e.confidence, sources: srcNames(e.sourceIds),
      associated: ws.relationships.filter((r) => String(r.from) === String(e._id) || String(r.to) === String(e._id)).map((r) => nameOf(m, String(r.from) === String(e._id) ? r.to : r.from)) })),
    blockchain: ws.entities.filter((e) => e.type === 'wallet').map((e) => ({ wallet: e.value, label: e.label, attributes: e.attributes || {}, firstSeen: e.firstSeen, lastSeen: e.lastSeen, confidence: e.confidence, sources: srcNames(e.sourceIds) })),
    evidence: ws.evidence.map((x) => ({ title: x.title, type: x.type, date: x.observedAt, confidence: x.confidence, source: src[String(x.sourceId)], related: (x.entityIds || []).map((i) => nameOf(m, i)) })),
    confidenceAssessment: ws.summary.confidence,
    sources: ws.sources.map((s) => ({ name: s.name, type: s.type, reliability: s.reliability, lastImportAt: s.lastImportAt, recordsUsed: s.recordsUsed })),
    investigatorNotes: investigation.notes || '',
  };
};

const q = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
exports.toCSV = (snap) => {
  const rows = [['section', 'field_1', 'field_2', 'field_3', 'field_4', 'field_5']];
  const add = (s, ...v) => rows.push([s, ...v]);
  snap.identifiers.forEach((i) => add('identifier', i.type, i.value, i.firstSeen, i.confidence, i.sources.join('; ')));
  snap.relationships.forEach((r) => add('relationship', r.from, r.type, r.to, r.confidence, r.sources.join('; ')));
  snap.timeline.forEach((t) => add('timeline', t.date, t.kind, t.title, '', t.sources.join('; ')));
  snap.infrastructure.forEach((i) => add('infrastructure', i.type, i.indicator, i.associated.join('; '), i.confidence, i.sources.join('; ')));
  snap.blockchain.forEach((b) => add('blockchain', b.wallet, b.attributes.totalReceived, b.attributes.totalSent, b.confidence, b.sources.join('; ')));
  snap.evidence.forEach((e) => add('evidence', e.title, e.type, e.date, e.confidence, e.source));
  snap.sources.forEach((s) => add('source', s.name, s.type, s.reliability, s.recordsUsed, ''));
  return rows.map((r) => r.map(q).join(',')).join('\n');
};