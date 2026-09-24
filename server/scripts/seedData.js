const mongoose = require('mongoose');
require('dotenv').config();
if (!process.env.MONGO_URI || process.env.MONGO_URI.includes('127.0.0.1')) {
  require('dotenv').config({ path: require('path').join(__dirname, '../.env') });
}
const { ingest } = require('../services/importService');

const samplePayload = {
  source: {
    name: 'SIH26151 Anonymized DarkWeb Intelligence Corpus',
    type: 'threat_intel_feed',
    reliability: 'A - Reliable'
  },
  entities: [
    // 1. ShadowX Cluster
    { type: 'actor', value: 'ShadowX', label: 'ShadowX (Data Broker)', category: 'Initial Access Broker', confidence: 95, firstSeen: '2023-01-10T00:00:00Z', lastSeen: '2023-11-15T00:00:00Z', profile: { posts: ['WTS fresh enterprise SQL dump and internal DB schema.', 'Releasing new python stealer source with custom obf.'], diurnal_hours: [0, 1, 2, 3, 21, 22] } },
    { type: 'username', value: 'ShadowX', label: 'ShadowX @ Dread', confidence: 90, firstSeen: '2023-01-10T00:00:00Z' },
    { type: 'forum_account', value: 'ShadowX_Dread', label: 'Dread Forum Account', confidence: 92, firstSeen: '2023-01-12T00:00:00Z' },
    { type: 'pgp', value: '4A8F 90B2 12C3 D4E5 F6A7 B8C9 0123 4567 89AB CDEF', label: 'PGP Fingerprint (ShadowX)', confidence: 100, firstSeen: '2022-12-01T00:00:00Z' },
    { type: 'wallet', value: 'bc1qShadowX9947xy2kgdygjrsqtzq2n0yrf249', label: 'BTC Wallet (ShadowX Primary)', confidence: 90, firstSeen: '2023-02-01T00:00:00Z', attributes: { chain: 'Bitcoin', balance: '2.45 BTC', totalReceived: '35.2 BTC', txCount: 14 } },
    { type: 'domain', value: 'shadow-drop.is', label: 'Payload Staging Domain', confidence: 85, firstSeen: '2023-03-01T00:00:00Z' },

    // 2. Shadow_X2026 Migrated Persona
    { type: 'actor', value: 'Shadow_X2026', label: 'Shadow_X2026 (Migrated Identity)', category: 'Initial Access Broker', confidence: 88, firstSeen: '2024-01-05T00:00:00Z', lastSeen: '2024-09-20T00:00:00Z', profile: { posts: ['WTS updated corporate DB dump with verified schema.', 'Updated python loader with advanced memory injection.'], diurnal_hours: [0, 1, 2, 3, 22] } },
    { type: 'username', value: 'Shadow_X2026', label: 'Shadow_X2026 @ Exploit', confidence: 88, firstSeen: '2024-01-05T00:00:00Z' },

    // 3. DarkVortex Group
    { type: 'actor', value: 'DarkVortex', label: 'DarkVortex (Ransomware Lead)', category: 'Ransomware Operator', confidence: 98, firstSeen: '2023-06-01T00:00:00Z', lastSeen: '2024-04-10T00:00:00Z', profile: { posts: ['All files encrypted using military grade AES-256 and RSA-4096.', 'Company network compromised via active directory persistence.'], diurnal_hours: [8, 9, 10, 11, 12, 13, 14] } },
    { type: 'username', value: 'DarkVortex', label: 'DarkVortex @ RansomHub', confidence: 95, firstSeen: '2023-06-01T00:00:00Z' },
    { type: 'wallet', value: 'bc1qDarkVortexRansomPool9993820129381023', label: 'BTC Wallet (DarkVortex Escrow)', confidence: 95, firstSeen: '2023-06-05T00:00:00Z', attributes: { chain: 'Bitcoin', balance: '18.5 BTC', totalReceived: '180.0 BTC', txCount: 42 } },
    { type: 'infrastructure', value: 'vortex-leak-portal.onion', label: 'Tor Leak Site', confidence: 95, firstSeen: '2023-06-10T00:00:00Z' },

    // 4. BurstyActor Anomaly Target
    { type: 'actor', value: 'BurstyActor', label: 'BurstyActor (High Churn Operator)', category: 'Cyber Crime Group', confidence: 85, firstSeen: '2024-02-01T00:00:00Z', lastSeen: '2024-09-01T00:00:00Z', profile: { posts: ['High-frequency post sample 1', 'High-frequency post sample 2'], burst_score: 0.92, diurnal_hours: [2, 3] } },
    { type: 'username', value: 'BurstyActor', label: 'BurstyActor Handle', confidence: 85, firstSeen: '2024-02-01T00:00:00Z' }
  ],
  relationships: [
    // ShadowX links
    { fromType: 'actor', fromValue: 'ShadowX', toType: 'username', toValue: 'ShadowX', type: 'uses_handle', confidence: 95, firstSeen: '2023-01-10T00:00:00Z' },
    { fromType: 'actor', fromValue: 'ShadowX', toType: 'pgp', toValue: '4A8F 90B2 12C3 D4E5 F6A7 B8C9 0123 4567 89AB CDEF', type: 'owns_pgp_key', confidence: 100, firstSeen: '2022-12-01T00:00:00Z' },
    { fromType: 'actor', fromValue: 'ShadowX', toType: 'wallet', toValue: 'bc1qShadowX9947xy2kgdygjrsqtzq2n0yrf249', type: 'controls_wallet', confidence: 90, firstSeen: '2023-02-01T00:00:00Z' },
    { fromType: 'actor', fromValue: 'ShadowX', toType: 'domain', toValue: 'shadow-drop.is', type: 'hosts_infrastructure', confidence: 85, firstSeen: '2023-03-01T00:00:00Z' },

    // Migration link between ShadowX and Shadow_X2026
    { fromType: 'actor', fromValue: 'ShadowX', toType: 'actor', toValue: 'Shadow_X2026', type: 'migrated_to', confidence: 88, firstSeen: '2024-01-05T00:00:00Z' },
    { fromType: 'actor', fromValue: 'Shadow_X2026', toType: 'pgp', toValue: '4A8F 90B2 12C3 D4E5 F6A7 B8C9 0123 4567 89AB CDEF', type: 'reused_pgp_key', confidence: 100, firstSeen: '2024-01-05T00:00:00Z' },

    // DarkVortex links
    { fromType: 'actor', fromValue: 'DarkVortex', toType: 'username', toValue: 'DarkVortex', type: 'uses_handle', confidence: 95, firstSeen: '2023-06-01T00:00:00Z' },
    { fromType: 'actor', fromValue: 'DarkVortex', toType: 'wallet', toValue: 'bc1qDarkVortexRansomPool9993820129381023', type: 'controls_wallet', confidence: 95, firstSeen: '2023-06-05T00:00:00Z' },
    { fromType: 'actor', fromValue: 'DarkVortex', toType: 'infrastructure', toValue: 'vortex-leak-portal.onion', type: 'operates_leak_site', confidence: 95, firstSeen: '2023-06-10T00:00:00Z' }
  ],
  evidence: [
    {
      title: 'Darknet Forum Sales Post - Enterprise DB Hash Verification',
      type: 'forum_post',
      content: 'WTS fresh enterprise SQL dump and internal DB schema. Payment strictly via escrow. PGP key attached.',
      observedAt: '2023-01-15T14:30:00Z',
      confidence: 90,
      entities: [{ type: 'actor', value: 'ShadowX' }, { type: 'pgp', value: '4A8F 90B2 12C3 D4E5 F6A7 B8C9 0123 4567 89AB CDEF' }]
    },
    {
      title: 'Ransomware Extortion Notice & Decryption Portal Link',
      type: 'ransom_note',
      content: 'All files encrypted using military grade AES-256. Contact negotiation desk via Tor leak portal.',
      observedAt: '2023-06-12T09:15:00Z',
      confidence: 95,
      entities: [{ type: 'actor', value: 'DarkVortex' }, { type: 'wallet', value: 'bc1qDarkVortexRansomPool9993820129381023' }]
    }
  ]
};

async function seed() {
  const uri = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/darktrace';
  console.log('Connecting to MongoDB at:', uri);
  await mongoose.connect(uri);
  console.log('Ingesting seed payload...');
  const res = await ingest(samplePayload);
  console.log('Seed completed successfully:', JSON.stringify(res, null, 2));
  await mongoose.disconnect();
}

seed().catch((err) => {
  console.error('Seed error:', err);
  process.exit(1);
});
