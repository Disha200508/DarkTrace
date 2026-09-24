const router = require('express').Router();
const crypto = require('crypto');
const M = require('../models');
const { auth, investigatorOnly, can } = require('../middleware/auth');
const audit = require('../services/audit');
const S = require('../services/searchService');
const ai = require('../services/aiClient');
const { buildReport, toCSV } = require('../services/reportService');

router.use(auth, investigatorOnly);
const newId = (p) => `${p}-${new Date().getFullYear()}-${crypto.randomBytes(3).toString('hex').toUpperCase()}`;

async function runPersona(ws) {
  const accts = ws.entities.filter((e) => ['username', 'forum_account', 'marketplace_account'].includes(e.type) && e.profile);
  if (accts.length < 2) return { available: false, reason: 'Fewer than two connected accounts have textual/behavioural profile data.' };
  try {
    const out = await ai.personaCompare(accts.map((a) => ({ id: String(a._id), type: a.type, value: a.value, profile: a.profile })));
    return { available: true, pairs: out.pairs || [], note: 'Analytical similarity only — not confirmation of shared identity.' };
  } catch (e) { return { available: false, reason: e.message }; }
}

/* ---- Search ---- */
router.post('/search', can('search'), async (req, res) => {
  const { type, query } = req.body;
  if (!S.TYPE_MAP[type] || typeof query !== 'string' || !query.trim() || query.length > 256) return res.status(400).json({ error: 'Valid search type and value required' });
  const ws = await S.search(type, query.trim());
  const log = await M.SearchLog.create({ user: req.user._id, type, query: query.trim(), resultCount: ws.entities.length });
  await audit({ user: req.user, req, action: 'Search', module: 'Search', detail: `${type}: ${query.trim()}` });
  res.json({ searchId: log._id, workspace: ws });
});

router.get('/entities/:id/neighbors', async (req, res) => res.json(await S.neighbors(req.params.id)));
router.get('/entities', async (req, res) => {
  const f = {}; if (typeof req.query.type === 'string' && req.query.type) f.type = req.query.type;
  if (typeof req.query.q === 'string' && req.query.q) f.$or = [{ value: new RegExp(req.query.q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i') }, { label: new RegExp(req.query.q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i') }];
  const items = await M.Entity.find(f).sort({ updatedAt: -1 }).limit(100).lean();
  await audit({ user: req.user, req, action: 'View Actor', module: 'Intelligence', detail: f.type || 'all' });
  res.json({ items });
});
router.post('/evidence/:id/view', async (req, res) => { await audit({ user: req.user, req, action: 'View Evidence', module: 'Evidence', detail: req.params.id }); res.json({ ok: true }); });
router.post('/persona', async (req, res) => {
  const ids = Array.isArray(req.body.entityIds) ? req.body.entityIds : [];
  const entities = await M.Entity.find({ _id: { $in: ids } }).lean();
  res.json(await runPersona({ entities }));
});

/* ---- AI Model Pipeline Endpoints ---- */
router.post('/ai/stylometry', async (req, res) => {
  const { text_a, text_b } = req.body;
  if (!text_a || !text_b) return res.status(400).json({ error: 'Both text_a and text_b are required for stylometric comparison' });
  const result = await ai.stylometryCompare(text_a, text_b);
  await audit({ user: req.user, req, action: 'Stylometry Compare', module: 'AI Engine', detail: `Text len A:${text_a.length} B:${text_b.length}` });
  res.json(result);
});

router.post('/ai/actor-compare', async (req, res) => {
  const { persona_a, persona_b } = req.body;
  if (!persona_a || !persona_b) return res.status(400).json({ error: 'Both persona_a and persona_b are required' });
  const result = await ai.actorCompare(persona_a, persona_b);
  await audit({ user: req.user, req, action: 'Actor Correlation', module: 'AI Engine', detail: `Comparing ${persona_a.name || persona_a} vs ${persona_b.name || persona_b}` });
  res.json(result);
});

router.post('/ai/migration', async (req, res) => {
  const { persona_a, persona_b } = req.body;
  const result = await ai.migrationDetect(persona_a, persona_b);
  res.json(result);
});

router.post('/ai/hypothesis', async (req, res) => {
  const { persona_a, persona_b } = req.body;
  const result = await ai.hypothesisTest(persona_a, persona_b);
  await audit({ user: req.user, req, action: 'Test Hypothesis', module: 'AI Engine', detail: `${persona_a} -> ${persona_b}` });
  res.json(result);
});

router.post('/ai/anomaly', async (req, res) => {
  const { persona } = req.body;
  const result = await ai.anomalyDetect(persona);
  res.json(result);
});

router.get('/ai/graph', async (req, res) => {
  const target = req.query.target || 'ShadowX';
  const graph = await ai.getCorrelationGraph(target);
  res.json(graph);
});

router.get('/ai/blockchain/address/:addr', async (req, res) => {
  const info = await ai.getBlockchainAddress(req.params.addr, req.query.target, req.query.demo);
  res.json(info);
});

router.get('/ai/blockchain/tx/:txid', async (req, res) => {
  const info = await ai.getBlockchainTransaction(req.params.txid);
  res.json(info);
});

router.post('/ai/blockchain/analyze', async (req, res) => {
  const info = await ai.analyzeBlockchain(req.body.query, req.body.comparison_target);
  res.json(info);
});

router.get('/ai/blockchain/status', async (req, res) => {
  const info = await ai.getBlockchainStatus();
  res.json(info);
});

/* ---- Investigations ---- */
router.post('/investigations', async (req, res) => {
  const { name, priority, status, tags, notes, search, searchId } = req.body;
  if (!name || !search?.type || !search?.query) return res.status(400).json({ error: 'Name and search required' });
  const ws = await S.search(search.type, search.query);
  const inv = await M.Investigation.create({
    invId: newId('INV'), name, priority, status, tags: (tags || []).slice(0, 20), notes, saved: true, owner: req.user._id, search,
    rootEntityIds: ws.roots.map((r) => r._id), entityIds: ws.entities.map((e) => e._id),
  });
  if (searchId) await M.SearchLog.updateOne({ _id: searchId, user: req.user._id }, { investigation: inv._id });
  await audit({ user: req.user, req, action: 'Create Investigation', module: 'Investigations', investigation: inv._id, detail: inv.invId });
  res.status(201).json(inv);
});

router.get('/investigations', async (req, res) => {
  const f = { owner: req.user._id };
  const b = req.query.bucket;
  if (b === 'active') f.status = { $in: ['New', 'Active', 'Under Review'] };
  if (b === 'saved') f.saved = true;
  if (b === 'closed') f.status = { $in: ['Closed', 'Archived'] };
  res.json({ items: await M.Investigation.find(f).sort({ updatedAt: -1 }).lean() });
});

const own = async (req) => {
  const inv = await M.Investigation.findOne({ _id: req.params.id, owner: req.user._id });
  if (!inv) throw Object.assign(new Error('Investigation not found'), { status: 404 });
  return inv;
};
router.get('/investigations/:id', async (req, res) => {
  const inv = await own(req);
  const ws = await S.search(inv.search.type, inv.search.query); // always live data
  inv.entityIds = ws.entities.map((e) => e._id); inv.rootEntityIds = ws.roots.map((r) => r._id); await inv.save();
  res.json({ investigation: inv, workspace: ws });
});
router.patch('/investigations/:id', async (req, res) => {
  const inv = await own(req);
  for (const k of ['name', 'priority', 'status', 'tags', 'notes', 'saved']) if (k in req.body) inv[k] = req.body[k];
  await inv.save();
  await audit({ user: req.user, req, action: 'Modify Investigation', module: 'Investigations', investigation: inv._id });
  res.json(inv);
});

/* ---- Reports ---- */
router.post('/investigations/:id/report', can('report'), async (req, res) => {
  const inv = await own(req);
  const ws = await S.search(inv.search.type, inv.search.query);
  const persona = await runPersona(ws);
  const reportId = newId('RPT');
  const snapshot = buildReport({ investigation: inv, ws, persona, user: req.user, reportId });
  const rep = await M.Report.create({ reportId, investigation: inv._id, generatedBy: req.user._id, snapshot });
  await audit({ user: req.user, req, action: 'Generate Report', module: 'Reports', investigation: inv._id, detail: reportId });
  res.status(201).json({ reportId });
});
router.get('/reports', async (req, res) => res.json({ items: await M.Report.find({ generatedBy: req.user._id }).select('-snapshot').sort({ createdAt: -1 }).populate('investigation', 'invId name').lean() }));
const ownReport = async (req) => {
  const r = await M.Report.findOne({ reportId: req.params.rid, generatedBy: req.user._id });
  if (!r) throw Object.assign(new Error('Report not found'), { status: 404 });
  return r;
};
router.get('/reports/:rid', async (req, res) => res.json((await ownReport(req)).snapshot));
router.get('/reports/:rid/export', can('export'), async (req, res) => {
  const rep = await ownReport(req); const fmt = req.query.format;
  if (!['json', 'csv', 'pdf'].includes(fmt)) return res.status(400).json({ error: 'format must be json, csv or pdf' });
  await M.Report.updateOne({ _id: rep._id }, { $addToSet: { formats: fmt } });
  await audit({ user: req.user, req, action: 'Export Data', module: 'Reports', investigation: rep.investigation, detail: `${rep.reportId} ${fmt}` });
  if (fmt === 'pdf') return res.json({ ok: true }); // PDF is produced client-side via print stylesheet; this records the export
  res.setHeader('Content-Disposition', `attachment; filename="${rep.reportId}.${fmt}"`);
  if (fmt === 'json') return res.json(rep.snapshot);
  res.type('text/csv').send(toCSV(rep.snapshot));
});

/* ---- History / alerts / dashboard ---- */
router.get('/history', async (req, res) => res.json({ items: await M.SearchLog.find({ user: req.user._id }).sort({ createdAt: -1 }).limit(200).populate('investigation', 'invId name').lean() }));
router.get('/alerts', async (req, res) => res.json({ items: await M.Alert.find({ owner: req.user._id }).sort({ createdAt: -1 }).limit(200).populate('investigation', 'invId name').lean() }));
router.patch('/alerts/:id/read', async (req, res) => { await M.Alert.updateOne({ _id: req.params.id, owner: req.user._id }, { read: true }); res.json({ ok: true }); });
router.get('/dashboard', async (req, res) => {
  const o = req.user._id;
  const [active, saved, alerts, reports, recent] = await Promise.all([
    M.Investigation.countDocuments({ owner: o, status: { $in: ['New', 'Active', 'Under Review'] } }),
    M.Investigation.countDocuments({ owner: o, saved: true }),
    M.Alert.countDocuments({ owner: o, read: false }), M.Report.countDocuments({ generatedBy: o }),
    M.SearchLog.find({ user: o }).sort({ createdAt: -1 }).limit(8).lean(),
  ]);
  res.json({ active, saved, alerts, reports, recent });
});

module.exports = router;