const router = require('express').Router();
const bcrypt = require('bcryptjs');
const multer = require('multer');
const mongoose = require('mongoose');
const { auth, role } = require('../middleware/auth');
const M = require('../models');
const crud = require('./crud');
const audit = require('../services/audit');
const ai = require('../services/aiClient');
const jobs = require('../services/jobService');
const { csvToPayload, ingest } = require('../services/importService');
const { normalize } = require('../services/searchService');

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 25 * 1024 * 1024 } });
router.use(auth, role('admin'));

/* ---------- Investigators ---------- */
router.get('/investigators', async (req, res) => {
  const items = await M.User.find({ role: { $in: M.INV_ROLES } }).select('-passwordHash').sort({ createdAt: -1 }).lean();
  res.json({ items });
});
router.get('/login-activity', async (req, res) => {
  const items = await M.User.find().select('-passwordHash').sort({ lastLoginAt: -1, createdAt: -1 }).lean();
  res.json({ items });
});
router.post('/investigators', async (req, res) => {
  const { fullName, investigatorId, username, email, password, role: r, status, permissions } = req.body;
  if (!fullName || !investigatorId || !username || !email || !password) return res.status(400).json({ error: 'All fields are required' });
  if (password.length < 10) return res.status(400).json({ error: 'Temporary password must be at least 10 characters' });
  if (!M.INV_ROLES.includes(r || 'investigator')) return res.status(400).json({ error: 'Invalid role' });
  try {
    const u = await M.User.create({ fullName, investigatorId, username, email, role: r || 'investigator', status: status || 'active', permissions: permissions || undefined, passwordHash: await bcrypt.hash(password, 12), mustChangePassword: true });
    await audit({ user: req.user, req, action: 'Create Investigator', module: 'Investigators', detail: u.username });
    res.status(201).json({ id: u._id });
  } catch (e) { if (e.code === 11000) return res.status(409).json({ error: 'Investigator ID, username or email already exists' }); throw e; }
});
router.patch('/investigators/:id', async (req, res) => {
  const allow = ['fullName', 'email', 'role', 'status', 'permissions'];
  const upd = Object.fromEntries(Object.entries(req.body).filter(([k]) => allow.includes(k)));
  if (upd.role && !M.INV_ROLES.includes(upd.role)) return res.status(400).json({ error: 'Invalid role' });
  const u = await M.User.findOneAndUpdate({ _id: req.params.id, role: { $in: M.INV_ROLES } }, upd, { new: true }).select('-passwordHash');
  if (!u) return res.status(404).json({ error: 'Not found' });
  await audit({ user: req.user, req, action: 'Modify Investigator', module: 'Investigators', detail: `${u.username}: ${Object.keys(upd).join(', ')}` });
  res.json(u);
});
router.post('/investigators/:id/reset-password', async (req, res) => {
  if (!req.body.password || req.body.password.length < 10) return res.status(400).json({ error: 'Min 10 characters' });
  const u = await M.User.findOneAndUpdate({ _id: req.params.id, role: { $in: M.INV_ROLES } }, { passwordHash: await bcrypt.hash(req.body.password, 12), mustChangePassword: true });
  if (!u) return res.status(404).json({ error: 'Not found' });
  await audit({ user: req.user, req, action: 'Modify Investigator', module: 'Investigators', detail: `password reset: ${u.username}` });
  res.json({ ok: true });
});

/* ---------- Intelligence CRUD ---------- */
const prepEntity = async (b) => {
  const o = { ...b };
  if (o.type && o.value) { o.value = String(o.value).trim(); o.valueNorm = normalize(o.type, o.value); }
  ['confidence'].forEach((k) => { if (o[k] === '' || o[k] == null) delete o[k]; });
  ['firstSeen', 'lastSeen'].forEach((k) => { if (!o[k]) delete o[k]; });
  return o;
};
router.use('/entities', crud(M.Entity, { searchFields: ['value', 'label', 'category'], filters: ['type', 'status'], prepare: prepEntity, mod: 'Intelligence', nouns: 'Entity' }));
router.use('/sources', crud(M.Source, { searchFields: ['name'], mod: 'Data Sources', nouns: 'Source' }));
router.use('/relationships', crud(M.Relationship, {
  populate: [{ path: 'from', select: 'type value label' }, { path: 'to', select: 'type value label' }],
  filters: ['status', 'method', 'type'], mod: 'Intelligence', nouns: 'Relationship',
  prepare: async (b) => {
    const o = { ...b };
    for (const side of ['from', 'to']) {
      if (b[`${side}Type`] && b[`${side}Value`]) {
        const e = await M.Entity.findOne({ type: b[`${side}Type`], valueNorm: normalize(b[`${side}Type`], b[`${side}Value`]) });
        if (!e) throw Object.assign(new Error(`${side} entity not found — import or create it first`), { status: 400 });
        o[side] = e._id;
      }
    }
    return o;
  },
}));

/* ---------- Import / quality ---------- */
router.post('/import', upload.single('file'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'File required' });
  let payload;
  try {
    const name = req.file.originalname.toLowerCase();
    if (name.endsWith('.json')) payload = JSON.parse(req.file.buffer.toString('utf8'));
    else if (name.endsWith('.csv')) payload = csvToPayload(req.file.buffer, { name: req.body.sourceName, type: req.body.sourceType, reliability: req.body.reliability });
    else return res.status(400).json({ error: 'Only CSV or JSON supported' });
  } catch (e) { return res.status(400).json({ error: `Could not parse file: ${e.message}` }); }
  const result = await ingest(payload);
  await audit({ user: req.user, req, action: 'Import Data', module: 'Data Management', detail: `${req.file.originalname} → ${JSON.stringify({ n: result.entitiesNew, r: result.relationshipsNew })}` });
  res.json(result);
});

router.get('/data-quality', async (req, res) => {
  const incompleteQ = { $or: [{ firstSeen: { $exists: false } }, { confidence: { $exists: false } }, { sourceIds: { $size: 0 } }] };
  const [total, incomplete, incompleteList, dupes] = await Promise.all([
    M.Entity.countDocuments(), M.Entity.countDocuments(incompleteQ),
    M.Entity.find(incompleteQ).limit(100).select('type value firstSeen confidence sourceIds').lean(),
    M.Entity.aggregate([{ $group: { _id: '$valueNorm', n: { $sum: 1 }, types: { $addToSet: '$type' }, ids: { $push: '$_id' } } }, { $match: { n: { $gt: 1 } } }, { $limit: 100 }]),
  ]);
  const proposed = await M.Relationship.countDocuments({ status: 'proposed' });
  res.json({ total, incomplete, incompleteList, duplicates: dupes, proposedRelationships: proposed,
    completenessPct: total ? Math.round(((total - incomplete) / total) * 100) : null });
});

/* ---------- Analysis ---------- */
router.post('/jobs', async (req, res) => {
  const job = await jobs.run(req.body.type, req.user._id);
  await audit({ user: req.user, req, action: 'Run Analysis', module: 'Analysis Engine', detail: req.body.type });
  res.status(202).json(job);
});
router.get('/jobs', async (req, res) => res.json({ items: await M.Job.find().sort({ createdAt: -1 }).limit(50).populate('createdBy', 'fullName').lean() }));
router.patch('/relationships/:id/review', async (req, res) => {
  if (!['confirmed', 'rejected'].includes(req.body.status)) return res.status(400).json({ error: 'Invalid status' });
  const r = await M.Relationship.findByIdAndUpdate(req.params.id, { status: req.body.status }, { new: true });
  await audit({ user: req.user, req, action: 'Modify Relationship', module: 'Analysis Engine', detail: `${req.params.id} → ${req.body.status}` });
  res.json(r);
});

/* ---------- Oversight ---------- */
router.get('/investigations', async (req, res) => res.json({ items: await M.Investigation.find().sort({ updatedAt: -1 }).limit(200).populate('owner', 'fullName investigatorId').lean() }));
router.get('/reports', async (req, res) => res.json({ items: await M.Report.find().select('-snapshot').sort({ createdAt: -1 }).limit(200).populate('investigation', 'invId name').populate('generatedBy', 'fullName').lean() }));
router.get('/alerts', async (req, res) => res.json({ items: await M.Alert.find().sort({ createdAt: -1 }).limit(200).populate('owner', 'fullName').lean() }));
router.get('/audit', async (req, res) => {
  const f = {}; if (typeof req.query.action === 'string' && req.query.action) f.action = req.query.action;
  res.json({ items: await M.AuditLog.find(f).sort({ createdAt: -1 }).limit(300).populate('investigation', 'invId').lean() });
});

router.get('/stats', async (req, res) => {
  const since = new Date(Date.now() - 30 * 864e5);
  const [inv, activeInv, entities, actors, identifiers, rels, activeInvs, alerts, evidence, act, invBy, alBy, recent] = await Promise.all([
    M.User.countDocuments({ role: { $in: M.INV_ROLES } }), M.User.countDocuments({ role: { $in: M.INV_ROLES }, status: 'active' }),
    M.Entity.countDocuments(), M.Entity.countDocuments({ type: 'actor' }), M.Entity.countDocuments({ type: { $ne: 'actor' } }),
    M.Relationship.countDocuments(), M.Investigation.countDocuments({ status: { $in: ['New', 'Active', 'Under Review'] } }),
    M.Alert.countDocuments(), M.Evidence.countDocuments(),
    M.Entity.aggregate([{ $match: { createdAt: { $gte: since } } }, { $group: { _id: { $dateToString: { format: '%Y-%m-%d', date: '$createdAt' } }, n: { $sum: 1 } } }, { $sort: { _id: 1 } }]),
    M.Investigation.aggregate([{ $group: { _id: '$status', n: { $sum: 1 } } }]),
    M.Alert.aggregate([{ $group: { _id: '$severity', n: { $sum: 1 } } }]),
    M.AuditLog.find().sort({ createdAt: -1 }).limit(10).lean(),
  ]);
  res.json({ cards: { investigators: inv, activeInvestigators: activeInv, actors, identifiers, relationships: rels, activeInvestigations: activeInvs, alerts, intelligenceRecords: entities + rels + evidence },
    charts: { activity: act, investigations: invBy, alerts: alBy }, recent });
});

router.get('/health', async (req, res) => {
  res.json({ database: mongoose.connection.readyState === 1 ? 'connected' : 'down', ai: await ai.status(), uptimeSeconds: Math.round(process.uptime()), node: process.version });
});

router.get('/ai/info', async (req, res) => {
  const info = await ai.getModelsInfo();
  res.json(info);
});

router.get('/ai/health', async (req, res) => {
  const st = await ai.status();
  res.json(st);
});

module.exports = router;