require('dotenv').config();
require('express-async-errors');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const connectDB = require('./config/db');

const app = express();
app.use(helmet());
app.use(cors({ origin: process.env.CLIENT_URL }));
app.use(express.json({ limit: '5mb' }));
app.use(morgan('dev'));

app.use('/api/auth', require('./routes/auth'));
app.use('/api/admin', require('./routes/admin'));
app.use('/api/inv', require('./routes/investigator'));

app.use((err, req, res, next) => {
  if (process.env.NODE_ENV !== 'production') console.error(err);
  res.status(err.status || 500).json({ error: err.status ? err.message : 'Internal server error' });
});

connectDB()
  .then(() => app.listen(process.env.PORT || 5000, () => console.log('DarkTrace API running')))
  .catch((e) => { console.error('DB connection failed', e.message); process.exit(1); });