const jwt = require('jsonwebtoken');
const { User, INV_ROLES } = require('../models');

exports.auth = async (req, res, next) => {
  try {
    const token = (req.headers.authorization || '').slice(7);
    const p = jwt.verify(token, process.env.JWT_SECRET);
    const user = await User.findById(p.id);
    if (!user || user.status !== 'active') return res.status(401).json({ error: 'Session invalid' });
    req.user = user;
    next();
  } catch { res.status(401).json({ error: 'Unauthorized' }); }
};
exports.role = (...roles) => (req, res, next) =>
  roles.includes(req.user.role) ? next() : res.status(403).json({ error: 'Forbidden' });
exports.investigatorOnly = exports.role(...INV_ROLES);
exports.can = (perm) => (req, res, next) =>
  req.user.role === 'admin' || req.user.permissions.includes(perm) ? next() : res.status(403).json({ error: `Missing permission: ${perm}` });