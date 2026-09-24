const { Schema, model } = require('mongoose');
const { ObjectId, Mixed } = Schema.Types;

const ENTITY_TYPES = ['actor', 'username', 'pgp', 'wallet', 'forum_account', 'marketplace_account', 'domain', 'infrastructure'];
const INV_ROLES = ['investigator', 'senior_investigator', 'analyst'];

const userS = new Schema({
  fullName: { type: String, required: true },
  investigatorId: { type: String, unique: true, sparse: true },
  username: { type: String, required: true, unique: true, lowercase: true, trim: true },
  email: { type: String, required: true, unique: true, lowercase: true },
  passwordHash: String,
  role: { type: String, enum: ['admin', ...INV_ROLES], default: 'investigator' },
  permissions: { type: [String], default: ['search', 'report', 'export'] },
  status: { type: String, enum: ['active', 'disabled'], default: 'active' },
  mustChangePassword: { type: Boolean, default: false },
  lastLoginAt: Date,
}, { timestamps: true });

const sourceS = new Schema({
  name: { type: String, required: true, unique: true },
  type: { type: String, default: 'dataset' },
  reliability: { type: String, enum: ['A - Reliable', 'B - Usually reliable', 'C - Fairly reliable', 'D - Not usually reliable', 'unrated'], default: 'unrated' },
  description: String,
  lastImportAt: Date,
}, { timestamps: true });

const entityS = new Schema({
  type: { type: String, enum: ENTITY_TYPES, required: true },
  value: { type: String, required: true },
  valueNorm: { type: String, required: true },
  label: String,
  category: String,
  status: { type: String, default: 'active' },
  confidence: { type: Number, min: 0, max: 100 },
  firstSeen: Date,
  lastSeen: Date,
  sourceIds: [{ type: ObjectId, ref: 'Source' }],
  attributes: Mixed, // e.g. wallets: { chain, balance, totalReceived, totalSent, txCount, transactions:[{hash,time,amount,counterparty,direction}] }
  profile: Mixed,    // textual/behavioural data for persona analysis: { textSamples, activityHours, topics }
}, { timestamps: true });
entityS.index({ type: 1, valueNorm: 1 }, { unique: true });
entityS.index({ valueNorm: 1 });

const relS = new Schema({
  from: { type: ObjectId, ref: 'Entity', required: true },
  to: { type: ObjectId, ref: 'Entity', required: true },
  type: { type: String, required: true }, // uses, controls, posted_on, hosted_on, transacted_with ...
  confidence: { type: Number, min: 0, max: 100 },
  method: { type: String, enum: ['imported', 'manual', 'correlation', 'ai'], default: 'imported' },
  status: { type: String, enum: ['confirmed', 'proposed', 'rejected'], default: 'confirmed' },
  reason: String,
  firstSeen: Date,
  lastSeen: Date,
  sourceIds: [{ type: ObjectId, ref: 'Source' }],
}, { timestamps: true });
relS.index({ from: 1, to: 1, type: 1 }, { unique: true });
relS.index({ to: 1 });

const evidenceS = new Schema({
  title: { type: String, required: true },
  type: { type: String, default: 'observation' },
  content: String,
  entityIds: [{ type: ObjectId, ref: 'Entity', index: true }],
  sourceId: { type: ObjectId, ref: 'Source' },
  observedAt: Date,
  confidence: { type: Number, min: 0, max: 100 },
}, { timestamps: true });

const investigationS = new Schema({
  invId: { type: String, unique: true },
  name: { type: String, required: true },
  priority: { type: String, enum: ['low', 'medium', 'high', 'critical'], default: 'medium' },
  status: { type: String, enum: ['New', 'Active', 'Under Review', 'Closed', 'Archived'], default: 'Active' },
  tags: [String],
  notes: String,
  saved: { type: Boolean, default: false },
  owner: { type: ObjectId, ref: 'User', required: true },
  search: { type: { type: String }, query: String },
  rootEntityIds: [ObjectId],
  entityIds: [{ type: ObjectId, index: true }],
}, { timestamps: true });

const searchLogS = new Schema({
  user: { type: ObjectId, ref: 'User', index: true },
  type: String, query: String, resultCount: Number,
  investigation: { type: ObjectId, ref: 'Investigation' },
}, { timestamps: true });

const alertS = new Schema({
  kind: { type: String, enum: ['new_identifier', 'new_relationship', 'new_related_entity', 'persona_similarity', 'infrastructure_indicator', 'data_issue'] },
  severity: { type: String, enum: ['High', 'Medium', 'Low'], default: 'Low' },
  message: String,
  owner: { type: ObjectId, ref: 'User' },          // null = system/admin alert
  investigation: { type: ObjectId, ref: 'Investigation' },
  read: { type: Boolean, default: false },
}, { timestamps: true });

const auditS = new Schema({
  user: { type: ObjectId, ref: 'User' }, username: String,
  action: String, module: String,
  investigation: { type: ObjectId, ref: 'Investigation' },
  detail: String, ip: String,
}, { timestamps: true });
auditS.index({ createdAt: -1 });

const jobS = new Schema({
  type: { type: String, enum: ['correlation', 'persona'] },
  status: { type: String, enum: ['queued', 'running', 'completed', 'failed'], default: 'queued' },
  createdBy: { type: ObjectId, ref: 'User' },
  result: Mixed, error: String, startedAt: Date, finishedAt: Date,
}, { timestamps: true });

const reportS = new Schema({
  reportId: { type: String, unique: true },
  investigation: { type: ObjectId, ref: 'Investigation' },
  generatedBy: { type: ObjectId, ref: 'User' },
  status: { type: String, default: 'Generated' },
  formats: [String], // formats actually exported
  snapshot: Mixed,
}, { timestamps: true });

module.exports = {
  ENTITY_TYPES, INV_ROLES,
  User: model('User', userS), Source: model('Source', sourceS), Entity: model('Entity', entityS),
  Relationship: model('Relationship', relS), Evidence: model('Evidence', evidenceS),
  Investigation: model('Investigation', investigationS), SearchLog: model('SearchLog', searchLogS),
  Alert: model('Alert', alertS), AuditLog: model('AuditLog', auditS), Job: model('Job', jobS), Report: model('Report', reportS),
};