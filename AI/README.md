# SIH26151: Dark Web Threat Actor De-anonymization — AI/ML Backend Pipeline

> **Research & Demonstration Notice**:  
> This system is built strictly for cybersecurity research and demonstration purposes using anonymized, synthetic, and publicly available benchmark datasets. All analytical outputs express **Similarity**, **Potential Association**, **Migration Candidate**, and **Analytical Confidence**, never confirmed real-world identity.

---

## 1. Overview & Architecture

The SIH26151 AI/ML backend pipeline is a multi-modal threat intelligence engine designed to correlate threat actor personas across dark web forums, PGP cryptographic keys, MITRE ATT&CK techniques, and Bitcoin transaction graph flows.

```
+-----------------------------------------------------------------------------------+
|                                RAW DATASETS                                       |
|  * safe_corpus.json (Anonymized Dark Web Forum Posts & Timestamps)                |
|  * PAN Authorship Verification Dataset (2022 dataset0 / dataset1)                 |
|  * MITRE ATT&CK Enterprise STIX Knowledge Base                                    |
|  * Elliptic Bitcoin Transaction & Edge Graph Dataset                              |
|  * Synthetic Threat Actor Investigation Records                                   |
|  * Live Public Bitcoin Blockchain API (Blockstream / Esplora / Mempool / Demo)    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        NORMALIZATION & ADAPTER LAYER                              |
|  * safe_corpus.py  |  pan.py  |  mitre.py  |  elliptic.py  |  synthetic.py        |
|  * blockchain/provider: EsploraProvider, BlockchairProvider, DemoBlockchainProvider|
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                         FEATURE EXTRACTION ENGINES                                |
|  * stylometry.py: Character/Word N-Grams, Lexical Richness (TTR, Yule K), Punct.  |
|  * behavior.py: 36-D Cadence, Forum Distribution Entropy, Burstiness Index        |
|  * timeline.py: 24-Hour Diurnal Rhythm Curve & Chronological Succession          |
|  * topics.py: Cyber Thematic Taxonomy & Cosine Affinity Distribution              |
|  * ttp.py: Multi-Hot MITRE ATT&CK Vector & Tactic-Weighted Jaccard                |
|  * wallet.py: 8-D Financial Flow (Volume, Frequency, In/Out Ratio, Graph Degree)  |
|  * infrastructure.py: PGP Fingerprints, TLS Cert Hashes, ASN Overlap, Churn Rate  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           TRAINED AI / ML MODELS                                  |
|  * Stylometry Verifier: Calibrated Gradient Boosting (F1: 88.64%, ROC-AUC: 93.17%)|
|  * Platt Scaling Sigmoid Calibrator (Brier Loss: 0.1006)                          |
|  * Threat Anomaly Detector: Multivariate Isolation Forest & LOF                  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     CORRELATION & UNCERTAINTY ENGINES                             |
|  * Weighted Correlation: Dynamic normalization over available signals             |
|  * Contradiction Engine: Detects hard/soft conflicts (PGP mismatch, timezone deltas)|
|  * Evidence Engine: Distinguishes 'No Match' from 'No Data' & computes coverage  |
|  * Confidence Engine: Sigmoid calibration with evidence coverage discounting      |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                       FASTAPI REST API & GRAPH TOPOLOGY                           |
|  * JSON API Endpoints for Persona Correlation, Stylometry, Hypothesis & Anomalies |
|  * Cytoscape.js Compatible Correlation Graph Generator (Actor -> Wallets -> Alias)|
+-----------------------------------------------------------------------------------+
```

---

## 2. Threat Actor & Wallet Correlation Graph

The AI pipeline includes a dedicated **Cytoscape.js Graph Generator** (`ai/inference/graph_generator.py`) matching the frontend visualization:

### Graph Topology & Visual Hierarchy:
```
                                +-----------------------------+
                                |  Threat Actor (ShadowX)     | [Hexagon, #e05656]
                                +--------------+--------------+
                                               |
                   +---------------------------+---------------------------+
                   | (Primary Alias)                                       | (Potential Association)
                   v                                                       v
     +---------------------------+                          +-------------------------------------+
     | Darknet Handle            |                          | Wallet A (Primary Extortion Inflow) | [Circle, #e67e22]
     | (@x_shadow_99)            | [Badge, #1abc9c]         +------------------+------------------+
     +-------------+-------------+                                             |
                   | (Signed Post)                                             | (Potential Association)
                   v                                                           +--------------------+--------------------+
     +---------------------------+                                             |                    |                    |
     | PGP Cryptographic Key     |                                             v                    v                    v
     | (PGP: 0x89ABCDEF)         | [Diamond, #9b59b6]                   +---------------+    +---------------+    +---------------+
     +---------------------------+                                      | Wallet B      |    | Wallet C      |    | Wallet D      |
                                                                        | (Mixer Hub)   |    | (Infra/Proxy) |    | (Off-Ramp)    |
                                                                        | [#3498db]     |    | [#3498db]     |    | [#3498db]     |
                                                                        +---------------+    +---------------+    +---------------+
```

### Hierarchy Model:
$$\text{SHADOWX} \longrightarrow \text{Wallet A} \longrightarrow [\text{Wallet B (Mixer)}, \text{Wallet C (Infra)}, \text{Wallet D (Off-Ramp)}]$$

---

## 3. Directory Structure

```text
ai/
├── api/
│   └── ai_routes.py               # FastAPI application & REST endpoints
├── config/
│   └── scoring.yaml               # Configurable signal weights, thresholds & penalties
├── correlation/
│   ├── confidence.py              # Sigmoid calibration & uncertainty estimation
│   ├── contradictions.py          # Contradiction detection & discount penalty engine
│   ├── evidence.py                # Source-attributed evidence bundle & coverage engine
│   └── scoring.py                 # Multi-signal weighted fusion engine
├── features/
│   ├── behavior.py                # 36-D Cadence, burstiness & forum entropy
│   ├── infrastructure.py          # PGP parity, certificate fingerprints & ASN churn
│   ├── stylometry.py              # N-grams, vocabulary richness, punctuation & syntax
│   ├── timeline.py                # 24-hr diurnal curve & migration succession
│   ├── topics.py                  # Domain thematic taxonomy & cosine similarity
│   ├── ttp.py                     # MITRE ATT&CK vectorization & Jaccard similarity
│   └── wallet.py                  # Elliptic-aligned 8-D financial flow comparator
├── inference/
│   ├── actor_similarity.py        # Persona dossier comparison
│   ├── graph_generator.py         # Cytoscape.js correlation graph topology generator
│   ├── migration_detection.py     # Migration detector & hypothesis testing
│   └── stylometry_inference.py    # Probabilistic text comparison API
├── models/
│   ├── anomaly_model.py           # Isolation Forest threat anomaly detector
│   └── stylometry_model.py        # Calibrated Gradient Boosting authorship verifier
├── preprocessing/
│   ├── elliptic.py                # Elliptic Bitcoin dataset loader & adapter
│   ├── mitre.py                   # MITRE ATT&CK STIX knowledge base parser
│   ├── pan.py                     # PAN 2022 Authorship Verification dataset loader
│   ├── safe_corpus.py             # Safe corpus dark web post cleaner & extractor
│   └── synthetic.py               # Synthetic threat persona investigation dossiers
├── saved_models/                  # Serialized artifacts (model.pkl, scaler.pkl, etc.)
├── tests/
│   └── test_pipeline.py           # Comprehensive 18-test unit & integration suite
└── training/
    ├── evaluate_models.py         # Model evaluation & 8-scenario false-positive benchmark
    ├── train_anomaly.py           # Behavioral anomaly detector training
    └── train_stylometry.py        # PAN authorship verification training & benchmarking
```

---

## 4. Setup & Installation

### Prerequisites:
- Python 3.10+
- `pip`

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 5. How to Run Training & Evaluation

### Step 2: Train the PAN Authorship Verification Model
Trains and benchmarks Logistic Regression, Random Forest, Gradient Boosting, and Linear SVM on the PAN 2022 dataset:
```bash
python -m ai.training.train_stylometry
```
**Output Summary:**
- Optimal Model Selected: **Gradient Boosting**
- Test Accuracy: `84.76%`
- Test F1-Score: `88.64%`
- Test ROC-AUC: `93.17%`
- Serializes artifacts to `ai/saved_models/`.

### Step 3: Train Behavioral Anomaly Detector
Fits the Isolation Forest baseline on dark web forum cadence and operational telemetry:
```bash
python -m ai.training.train_anomaly
```

### Step 4: Run the False-Positive & Edge-Case Benchmark Suite
Evaluates the model against 8 distinct edge cases (contradictory PGP keys, commodity TTP mimicry, timezone divergence, missing wallet data):
```bash
python -m ai.training.evaluate_models
```

### Step 5: Run Full Unit & Integration Test Suite
Executes all 18 automated tests covering preprocessing, feature extractors, calibration, and REST endpoints:
```bash
python -m unittest ai/tests/test_pipeline.py
```

---

## 6. How to Start the AI Backend Server

Launch the FastAPI backend service on port `8000`:
```bash
uvicorn ai.api.ai_routes:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation will be available at:  
👉 **`http://localhost:8000/docs`**

---

## 7. Sample API Requests & JSON Responses

### 1. Threat Actor & Wallet Correlation Graph (Cytoscape.js Format)
**Endpoint**: `GET /api/ai/graph/actor-correlation?target=ShadowX`

```bash
curl -X GET "http://localhost:8000/api/ai/graph/actor-correlation?target=ShadowX"
```

**Sample Response:**
```json
{
  "case_id": "CASE-SIH26151-SHADOWX",
  "title": "Threat Actor & Wallet Correlation Graph",
  "target": "ShadowX",
  "hierarchy_model": "SHADOWX -> Wallet A -> [Wallet B, Wallet C, Wallet D]",
  "engine": "Cytoscape.js Engine v3.x Compatible",
  "elements": {
    "nodes": [
      {
        "data": {
          "id": "actor_shadowx",
          "label": "ShadowX",
          "type": "threat_actor",
          "category": "Threat Actor",
          "shape": "hexagon",
          "color": "#e05656",
          "bg_color": "#8b1e1e"
        },
        "classes": "threat-actor-node"
      },
      {
        "data": {
          "id": "handle_shadowx",
          "label": "@x_shadow_99",
          "type": "darknet_handle",
          "category": "Darknet Handle",
          "shape": "round-rectangle",
          "color": "#1abc9c"
        },
        "classes": "handle-node"
      },
      {
        "data": {
          "id": "pgp_shadowx",
          "label": "PGP: 0x89ABCDEF",
          "type": "pgp_key",
          "category": "PGP Cryptographic Key",
          "shape": "diamond",
          "color": "#9b59b6"
        },
        "classes": "pgp-node"
      },
      {
        "data": {
          "id": "wallet_a_shadowx",
          "label": "Wallet A (Primary Extortion Inflow)",
          "type": "primary_wallet",
          "shape": "ellipse",
          "color": "#e67e22"
        },
        "classes": "primary-wallet-node"
      },
      {
        "data": {
          "id": "wallet_mixer_shadowx",
          "label": "Wallet B (Mixer / Tumbler Hub)",
          "type": "connected_wallet",
          "shape": "ellipse",
          "color": "#3498db"
        },
        "classes": "connected-wallet-node"
      }
    ],
    "edges": [
      {
        "data": {
          "id": "edge_actor_shadowx_handle_shadowx",
          "source": "actor_shadowx",
          "target": "handle_shadowx",
          "label": "Primary Alias",
          "relationship": "Primary Alias",
          "style": "solid",
          "color": "#1abc9c"
        }
      },
      {
        "data": {
          "id": "edge_actor_shadowx_wallet_a_shadowx",
          "source": "actor_shadowx",
          "target": "wallet_a_shadowx",
          "label": "Potential Association",
          "relationship": "Potential Association",
          "style": "dashed",
          "color": "#e67e22",
          "confidence": 0.85
        }
      },
      {
        "data": {
          "id": "edge_migration_shadowx_shadowx2026",
          "source": "actor_shadowx",
          "target": "actor_shadow_x2026",
          "label": "Migration Candidate (97%)",
          "relationship": "Migration Candidate",
          "style": "dashed",
          "color": "#f39c12",
          "confidence": 0.971
        }
      }
    ]
  },
  "safety_notice": "SYNTHETIC DEMO: Blockchain data shown is synthetic demonstration data. Relationships between actors and wallets represent 'Potential Association' heuristics."
}
```

---

### 2. Multi-Signal Persona Correlation
**Endpoint**: `POST /api/ai/actor/compare`

```bash
curl -X POST "http://localhost:8000/api/ai/actor/compare" \
     -H "Content-Type: application/json" \
     -d '{
       "persona_a": {"name": "ShadowX"},
       "persona_b": {"name": "Shadow_X2026"}
     }'
```

**Sample Response:**
```json
{
  "case_id": "CASE-SIH26151-SHADOWX",
  "target": "ShadowX",
  "comparison_target": "Shadow_X2026",
  "signals": {
    "stylometry": 0.9971,
    "behavior": 0.9856,
    "activity_rhythm": 0.9912,
    "topic": 0.9245,
    "timeline": 0.8845,
    "wallet": 0.9984,
    "pgp": 1.0,
    "infrastructure": 0.8750,
    "ttp": 0.7500,
    "campaign_score": 0.9526
  },
  "overall_confidence": 0.9710,
  "raw_probability": 0.9526,
  "calibrated_probability": 0.9710,
  "classification": "Migration Candidate",
  "supporting_evidence": [
    {
      "type": "stylometry",
      "name": "Stylometric Authorship Verification",
      "score": 0.9971,
      "source": "PAN Authorship Verification Dataset",
      "method": "Character & Word N-Gram TF-IDF + Statistical Stylometry + Calibrated Classifier",
      "evidence": [
        "Character n-gram similarity: 0.94",
        "Word n-gram similarity: 0.88",
        "Vocabulary profile similarity: 0.91",
        "Punctuation distribution similarity: 0.95"
      ]
    },
    {
      "type": "pgp",
      "name": "PGP Cryptographic Signature",
      "score": 1.0,
      "source": "Synthetic PGP Key Ring Records",
      "evidence": [
        "Exact cryptographic PGP fingerprint match: 4A8F 90B2 12C3 D4E5 F6A7 B8C9 0123 4567 89AB CDEF"
      ]
    }
  ],
  "contradictory_evidence": [],
  "missing_evidence": [],
  "evidence_coverage": 1.0,
  "safety_notice": "Analytical similarity does not establish real-world identity."
}
```

---

### 3. Binary Stylometric Comparison
**Endpoint**: `POST /api/ai/stylometry/compare`

```bash
curl -X POST "http://localhost:8000/api/ai/stylometry/compare" \
     -H "Content-Type: application/json" \
     -d '{
       "text_a": "WTS fresh enterprise SQL dump and internal DB schema. Payment strictly via escrow. No lowball offers.",
       "text_b": "WTS updated corporate DB dump with verified schema. Payment strictly in BTC via trusted escrow."
     }'
```

**Sample Response:**
```json
{
  "character_similarity": 0.8834,
  "word_similarity": 0.7812,
  "vocabulary_similarity": 0.8920,
  "punctuation_similarity": 0.9540,
  "syntax_similarity": 0.9102,
  "stylometric_score": 0.9854,
  "same_author_probability": 0.9854,
  "classification": "Potential Same-Author Pattern",
  "model_name": "stylometry_verifier",
  "model_version": "1.0.0",
  "methodology": "Character + Word N-Gram + Statistical Stylometry"
}
```

---

### 4. Hypothesis Testing
**Endpoint**: `POST /api/ai/hypothesis/test`

```bash
curl -X POST "http://localhost:8000/api/ai/hypothesis/test" \
     -H "Content-Type: application/json" \
     -d '{
       "persona_a": {"name": "ShadowX"},
       "persona_b": {"name": "Shadow_X2026"}
     }'
```

**Sample Response:**
```json
{
  "hypothesis": "Persona 'Shadow_X2026' may represent an operational migration or associated cluster of Persona 'ShadowX'.",
  "target_a": "ShadowX",
  "target_b": "Shadow_X2026",
  "classification": "Migration Candidate",
  "confidence": 0.9710,
  "supporting_signals": [
    "Stylometry (Score: 0.9971)",
    "Behavior (Score: 0.9856)",
    "Activity Rhythm (Score: 0.9912)",
    "Topic (Score: 0.9245)",
    "Timeline (Score: 0.8845)",
    "Wallet (Score: 0.9984)",
    "Pgp (Score: 1.0)",
    "Infrastructure (Score: 0.875)",
    "Ttp (Score: 0.75)"
  ],
  "contradictory_signals": [],
  "missing_signals": [],
  "evidence_coverage": 1.0,
  "safety_notice": "Analytical similarity does not establish real-world identity."
}
```

---

### 5. Behavioral Anomaly Detection
**Endpoint**: `POST /api/ai/anomaly/detect`

```bash
curl -X POST "http://localhost:8000/api/ai/anomaly/detect" \
     -H "Content-Type: application/json" \
     -d '{
       "persona": {
         "name": "BurstyActor",
         "posts": ["post 1", "post 2", "post 3", "post 4", "post 5", "post 6"],
         "burst_score": 0.92,
         "diurnal_hours": [2, 3],
         "wallets": [{"burst_rate": 0.88}],
         "infrastructure": {"churn_score": 0.85}
       }
     }'
```

**Sample Response:**
```json
{
  "target": "BurstyActor",
  "anomalies_detected": 4,
  "anomalies": [
    {
      "anomaly_type": "High Burst Posting Rate",
      "severity": "Critical",
      "anomaly_score": 0.92,
      "description": "Unusual burst frequency index (0.92) detected exceeding baseline.",
      "supporting_features": ["burst_rate", "posting_cadence"]
    },
    {
      "anomaly_type": "Off-Hour Operational Deviation",
      "severity": "Medium",
      "anomaly_score": 1.0,
      "description": "High concentration of active operations during anomalous nocturnal/early UTC hours.",
      "supporting_features": ["diurnal_hours", "off_hour_ratio"]
    },
    {
      "anomaly_type": "Cryptocurrency Transaction Volume Spike",
      "severity": "Critical",
      "anomaly_score": 0.88,
      "description": "Sudden sharp increase in Bitcoin outbound volume and connected transaction nodes.",
      "supporting_features": ["wallet_vol_spike", "outbound_volume"]
    },
    {
      "anomaly_type": "Accelerated Infrastructure Churn",
      "severity": "High",
      "anomaly_score": 0.85,
      "description": "Rapid DNS and hosting provider migration observed (churn: 0.85).",
      "supporting_features": ["infra_churn_rate", "domain_rotation"]
    }
  ],
  "safety_notice": "Analytical anomaly detection flags operational pattern shifts."
}
```

---

---

## 8. Read-Only Blockchain Intelligence Module

The blockchain intelligence module provides **strictly read-only public Bitcoin lookups**, calculating transaction metrics, flow ratios, Cytoscape graph structures, and AI wallet behavior scores aligned with the Elliptic dataset representation without modifying any existing features.

### Security Guarantees:
- **Strictly GET / Read-Only**: No transaction signing, private key handling, credential collection, or network broadcasting.
- **Input Validation**: Rejects invalid inputs before network calls (Legacy `1...`, P2SH `3...`, Bech32 `bc1q...`, Taproot `bc1p...`, and 64-char hex hashes).
- **Data Provenance**: Every response clearly indicates `[ LIVE PUBLIC BLOCKCHAIN ]` or `[ SYNTHETIC DEMO ]`.
- **Offline Demo Mode**: Toggleable offline mode for SIH presentations without internet dependency.

---

## 9. Blockchain API Endpoints & Sample Responses

### 1. Address Analysis
**Endpoint**: `GET /api/blockchain/address/{address}`

```bash
curl -X GET "http://localhost:8000/api/blockchain/address/1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa?demo=false"
```

**Sample Response:**
```json
{
  "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
  "address_type": "Legacy (P2PKH / Base58)",
  "network": "bitcoin-mainnet",
  "source_type": "LIVE PUBLIC BLOCKCHAIN",
  "provider": "Blockstream / Esplora (https://blockstream.info/api)",
  "demo_mode": false,
  "summary": {
    "transaction_count": 5218,
    "total_received_btc": 99.84521045,
    "total_spent_btc": 0.0,
    "unspent_btc": 99.84521045,
    "observable_utxos": 5218,
    "first_seen": "2009-01-03 18:15:05Z",
    "last_seen": "2024-09-24 12:40:12Z",
    "average_transaction_value": 0.019134
  },
  "behavior": {
    "transaction_frequency": 0.35,
    "average_value": 0.019,
    "inbound_ratio": 1.0,
    "outbound_ratio": 0.0,
    "counterparty_count": 4820,
    "burst_activity": 0.42
  },
  "ai_integration": {
    "wallet_behavior_score": 0.7245,
    "compared_target": "ShadowX",
    "interpretation": "Potential Behavioral Association based on 8-D transaction flow vector cosine",
    "methodology": "Elliptic Bitcoin Representation Alignment"
  },
  "flow_analysis": {
    "inbound_btc": 99.84521045,
    "outbound_btc": 0.0,
    "net_observable_flow_btc": 99.84521045,
    "flow_status": "NET_ACCUMULATION"
  },
  "forensic_risk": {
    "forensic_risk_score": 38.5,
    "risk_level": "MODERATE",
    "components": {
      "transaction_velocity": 5.0,
      "flow_asymmetry": 15.0,
      "graph_connectivity": 18.5,
      "behavioral_anomalies": 0.0
    }
  },
  "graph": {
    "nodes": [
      {
        "data": {
          "id": "addr_1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
          "label": "1A1zP1eP...vfNa",
          "type": "target_address",
          "color": "#e05656"
        },
        "classes": "target-address-node"
      }
    ],
    "edges": [],
    "clustering": {
      "method": "connected_components",
      "label": "Transaction-connected cluster"
    }
  },
  "investigation_dossier_entry": {
    "section": "BLOCKCHAIN OBSERVATION",
    "network": "bitcoin-mainnet",
    "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "first_seen": "2009-01-03 18:15:05Z",
    "last_seen": "2024-09-24 12:40:12Z",
    "total_received": "99.84521045 BTC",
    "total_spent": "0.0 BTC",
    "observable_utxo": "99.84521045 BTC",
    "forensic_risk_score": 38.5,
    "risk_level": "MODERATE",
    "provenance": {
      "source": "Public Bitcoin Blockchain",
      "provider": "Blockstream / Esplora"
    }
  },
  "limitations": [
    "Observable blockchain behavior does not establish real-world ownership or identity.",
    "Connections between addresses represent observable transaction flow heuristics only."
  ]
}
```

---

### 2. Transaction Lookup
**Endpoint**: `GET /api/blockchain/transaction/{txid}`

```bash
curl -X GET "http://localhost:8000/api/blockchain/transaction/a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d"
```

---

### 3. Unified Analyzer
**Endpoint**: `POST /api/blockchain/analyze`

```bash
curl -X POST "http://localhost:8000/api/blockchain/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "1ShadowX9947bc1qxy2kgdygjrsqtzq2n0yrf249",
       "demo_mode": true
     }'
```

---

### 4. Mode Toggle (Live vs Demo)
**Endpoint**: `POST /api/blockchain/mode`

```bash
curl -X POST "http://localhost:8000/api/blockchain/mode" \
     -H "Content-Type: application/json" \
     -d '{"demo_mode": true}'
```

---

## 10. Summary of All REST Endpoints

### AI Core Endpoints:
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/ai/graph/actor-correlation` | Generates Cytoscape.js correlation graph topology |
| `GET` | `/api/ai/graph/actor/{id}` | Generates single actor subgraph elements |
| `POST` | `/api/ai/stylometry/compare` | Binary text authorship verification |
| `POST` | `/api/ai/actor/compare` | Full 9-signal multi-modal persona correlation |
| `POST` | `/api/ai/migration/detect` | Persona migration candidate detector |
| `POST` | `/api/ai/hypothesis/test` | Structured analytical hypothesis tester |
| `POST` | `/api/ai/anomaly/detect` | Isolation Forest behavioral & financial anomaly detector |
| `GET` | `/api/ai/actor/{id}/profile` | Retrieves synthetic persona dossier |
| `GET` | `/api/ai/actor/{id}/evidence` | Retrieves source-attributed evidence bundle |
| `GET` | `/api/ai/health` | Service health status |
| `GET` | `/api/ai/models/info` | Trained model metadata, versions, and metrics |

### Blockchain Intelligence Endpoints:
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/blockchain/address/{address}` | Public blockchain metrics, flow, graph, and AI behavior score |
| `GET` | `/api/blockchain/transaction/{txid}` | Raw transaction inputs, outputs, fee, and confirmations |
| `POST` | `/api/blockchain/analyze` | Unified address & transaction hash analyzer |
| `POST` | `/api/blockchain/mode` | Toggles between Live Public API and Offline Demo Mode |
| `GET` | `/api/blockchain/status` | Provider status, cache statistics, and supported address types |
