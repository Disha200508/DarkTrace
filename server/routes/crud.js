const router = require('express').Router;
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

module.exports = (Model, { populate, searchFields = [], filters = [], prepare = async (b) => b, mod = 'Data', nouns = 'Record' } = {}) => {
  const r = router();
  r.get('/', async (req, res) => {
    const { q, page = 1, limit = 25 } = req.query;
    const f = {};
    filters.forEach((k) => { if (typeof req.query[k] === 'string' && req.query[k]) f[k] = req.query[k]; }); // whitelisted, string-only (no operator injection)
    if (q && searchFields.length) f.$or = searchFields.map((k) => ({ [k]: new RegExp(esc(String(q)), 'i') }));
    let query = Model.find(f).sort({ createdAt: -1 }).skip((Math.max(+page, 1) - 1) * Math.min(+limit, 100)).limit(Math.min(+limit, 100)).lean();
    if (populate) query = query.populate(populate);
    const [items, total] = await Promise.all([query, Model.countDocuments(f)]);
    res.json({ items, total });
  });
  r.post('/', async (req, res) => {
    const doc = await Model.create(await prepare(req.body));
    require('../services/audit')({ user: req.user, req, action: `Create ${nouns}`, module: mod, detail: String(doc._id) });
    res.status(201).json(doc);
  });
  r.put('/:id', async (req, res) => {
    const doc = await Model.findByIdAndUpdate(req.params.id, await prepare(req.body, true), { new: true, runValidators: true });
    if (!doc) return res.status(404).json({ error: 'Not found' });
    require('../services/audit')({ user: req.user, req, action: `Modify ${nouns}`, module: mod, detail: String(doc._id) });
    res.json(doc);
  });
  r.delete('/:id', async (req, res) => {
    await Model.findByIdAndDelete(req.params.id);
    require('../services/audit')({ user: req.user, req, action: `Delete ${nouns}`, module: mod, detail: req.params.id });
    res.json({ ok: true });
  });
  return r;
};