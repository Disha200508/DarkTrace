const router = require('express').Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const { User, INV_ROLES } = require('../models');
const { auth } = require('../middleware/auth');
const audit = require('../services/audit');

router.post('/login', rateLimit({ windowMs: 15 * 60 * 1000, max: 30 }), async (req, res) => {
  const { identifier = '', password = '', portal } = req.body;
  const id = String(identifier).trim();
  const user = await User.findOne({ $or: [{ username: id.toLowerCase() }, { investigatorId: id }] });
  const portalOk = user && (portal === 'admin' ? user.role === 'admin' : INV_ROLES.includes(user.role));
  const ok = portalOk && user.status === 'active' && (await bcrypt.compare(password, user.passwordHash));
  if (!ok) {
    await audit({ user, req, action: 'Login Failed', module: 'Auth', detail: id });
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  user.lastLoginAt = new Date(); await user.save();
  await audit({ user, req, action: 'Login', module: 'Auth' });
  const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET, { expiresIn: '8h' });
  res.json({ token, user: { id: user._id, fullName: user.fullName, username: user.username, role: user.role, permissions: user.permissions, mustChangePassword: user.mustChangePassword } });
});

router.post('/register', rateLimit({ windowMs: 15 * 60 * 1000, max: 20 }), async (req, res) => {
  try {
    const { fullName, username, email, password, investigatorId, role = 'investigator' } = req.body;
    
    if (!fullName || !username || !email || !password) {
      return res.status(400).json({ error: 'All fields (Full Name, Username, Email, Password) are required' });
    }
    if (password.length < 8) {
      return res.status(400).json({ error: 'Password must be at least 8 characters long' });
    }

    const cleanUsername = username.trim().toLowerCase();
    const cleanEmail = email.trim().toLowerCase();

    // Check if user or email already exists
    const existing = await User.findOne({ $or: [{ username: cleanUsername }, { email: cleanEmail }] });
    if (existing) {
      if (existing.username === cleanUsername) {
        return res.status(400).json({ error: 'Username is already taken' });
      }
      return res.status(400).json({ error: 'Email address is already registered' });
    }

    // Generate investigator ID if not provided
    const finalInvId = (investigatorId && investigatorId.trim()) 
      ? investigatorId.trim().toUpperCase() 
      : `INV-${Math.floor(1000 + Math.random() * 9000)}`;

    const passwordHash = await bcrypt.hash(password, 12);
    const validRole = INV_ROLES.includes(role) ? role : 'investigator';

    const newUser = await User.create({
      fullName: fullName.trim(),
      username: cleanUsername,
      email: cleanEmail,
      investigatorId: finalInvId,
      passwordHash,
      role: validRole,
      permissions: ['search', 'report', 'export'],
      status: 'active',
      mustChangePassword: false,
    });

    await audit({ user: newUser, req, action: 'User Sign Up', module: 'Auth', detail: `Registered ${cleanUsername} (${finalInvId})` });

    const token = jwt.sign({ id: newUser._id }, process.env.JWT_SECRET, { expiresIn: '8h' });
    res.status(201).json({
      token,
      user: {
        id: newUser._id,
        fullName: newUser.fullName,
        username: newUser.username,
        email: newUser.email,
        investigatorId: newUser.investigatorId,
        role: newUser.role,
        permissions: newUser.permissions,
        mustChangePassword: newUser.mustChangePassword
      }
    });
  } catch (err) {
    console.error('Registration error:', err);
    res.status(500).json({ error: 'Failed to create account. Please try again.' });
  }
});

router.get('/me', auth, (req, res) => {
  const u = req.user;
  res.json({ id: u._id, fullName: u.fullName, username: u.username, email: u.email, investigatorId: u.investigatorId, role: u.role, permissions: u.permissions, mustChangePassword: u.mustChangePassword });
});

router.post('/logout', auth, async (req, res) => { await audit({ user: req.user, req, action: 'Logout', module: 'Auth' }); res.json({ ok: true }); });

router.post('/change-password', auth, async (req, res) => {
  const { current, next } = req.body;
  if (!next || next.length < 10) return res.status(400).json({ error: 'Password must be at least 10 characters' });
  if (!(await bcrypt.compare(current || '', req.user.passwordHash))) return res.status(400).json({ error: 'Current password incorrect' });
  req.user.passwordHash = await bcrypt.hash(next, 12); req.user.mustChangePassword = false; await req.user.save();
  res.json({ ok: true });
});
module.exports = router;