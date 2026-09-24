const { AuditLog } = require('../models');
module.exports = async ({ user, req, action, module, investigation, detail }) => {
  try {
    await AuditLog.create({
      user: user?._id, username: user?.username, action, module, investigation, detail,
      ip: req?.ip,
    });
  } catch (e) { console.error('audit failed', e.message); }
};