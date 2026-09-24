require('dotenv').config();
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const { User } = require('../models');

(async () => {
  const [username, password, email] = process.argv.slice(2);
  if (!username || !password || !email || password.length < 12) { console.log('Usage: npm run create-admin -- <username> <password(12+ chars)> <email>'); process.exit(1); }
  await mongoose.connect(process.env.MONGO_URI);
  await User.create({ fullName: 'System Administrator', username, email, role: 'admin', passwordHash: await bcrypt.hash(password, 12) });
  console.log('Admin created'); process.exit(0);
})();