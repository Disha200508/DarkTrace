"""
End-to-End Pipeline & API Unit Tests
SIH26151: Dark Web Threat Actor De-anonymization

Tests all preprocessing, feature extraction, correlation, anomaly detection,
and FastAPI endpoint components.
"""

import unittest
import json
import numpy as np
from fastapi.testclient import TestClient

from ai.preprocessing.safe_corpus import SafeCorpusPreprocessor
from ai.preprocessing.pan import PANPreprocessor
from ai.preprocessing.mitre import MitreAttackKB
from ai.preprocessing.elliptic import EllipticPreprocessor
from ai.preprocessing.synthetic import SyntheticInvestigationAdapter
from ai.features.stylometry import StylometryExtractor
from ai.features.behavior import BehaviorExtractor
from ai.features.timeline import TimelineExtractor
from ai.features.topics import TopicExtractor
from ai.features.ttp import TTPExtractor
from ai.features.wallet import WalletExtractor
from ai.features.infrastructure import InfrastructureExtractor
from ai.correlation.contradictions import ContradictionEngine
from ai.correlation.evidence import EvidenceEngine
from ai.correlation.confidence import ConfidenceCalibrator
from ai.correlation.scoring import CorrelationEngine
from ai.models.stylometry_model import StylometryModel
from ai.models.anomaly_model import ThreatAnomalyDetector
from ai.api.ai_routes import app


class TestSIH26151Pipeline(unittest.TestCase):
    """Unit test suite for SIH26151 backend pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.adapter = SyntheticInvestigationAdapter()
        cls.engine = CorrelationEngine()

    def test_01_safe_corpus_preprocessor(self):
        prep = SafeCorpusPreprocessor("safe_corpus.json")
        posts = prep.extract_posts()
        self.assertGreater(len(posts), 0)
        self.assertIn("content", posts[0])
        self.assertIn("author", posts[0])

    def test_02_mitre_knowledge_base(self):
        kb = MitreAttackKB()
        self.assertGreater(len(kb.techniques), 500)
        t1059 = kb.get_technique("T1059")
        self.assertIsNotNone(t1059)
        extracted = kb.extract_ttps_from_text("Adversary used powershell and mimikatz to dump credentials")
        self.assertIn("T1059", extracted["ttp_ids"])
        self.assertIn("T1003", extracted["ttp_ids"])

    def test_03_elliptic_adapter(self):
        prep = EllipticPreprocessor()
        vec = prep.extract_wallet_features({
            "tx_frequency": 12.0,
            "avg_tx_value": 3.5,
            "inbound_volume": 40.0,
            "outbound_volume": 38.0
        })
        self.assertEqual(len(vec), 8)
        self.assertFalse(np.isnan(vec).any())

    def test_04_stylometry_extractor(self):
        extractor = StylometryExtractor()
        text_a = "This is a sample technical post explaining memory injection mechanisms."
        text_b = "This is another sample post discussing exploit payload delivery and stubs."
        feats_a = extractor.extract_statistical_features(text_a)
        self.assertIn("avg_word_length", feats_a)
        self.assertIn("ttr", feats_a)

    def test_05_multi_signal_correlation(self):
        p_a = self.adapter.get_persona("ShadowX")
        p_b = self.adapter.get_persona("Shadow_X2026")
        res = self.engine.correlate_personas(p_a, p_b)

        self.assertEqual(res["target"], "ShadowX")
        self.assertEqual(res["comparison_target"], "Shadow_X2026")
        self.assertIn("stylometry", res["signals"])
        self.assertIn("behavior", res["signals"])
        self.assertIn("ttp", res["signals"])
        self.assertIn("overall_confidence", res)
        self.assertGreater(res["overall_confidence"], 0.70)
        self.assertEqual(res["classification"], "Migration Candidate")
        self.assertGreater(res["evidence_coverage"], 0.60)
        self.assertIn("safety_notice", res)

    def test_06_contradiction_engine(self):
        p_a = self.adapter.get_persona("ShadowX")
        p_b = self.adapter.get_persona("DarkVortex")
        res = self.engine.correlate_personas(p_a, p_b)

        self.assertGreater(len(res["contradictory_evidence"]), 0)
        self.assertEqual(res["signals"]["pgp"], 0.0)  # PGP mismatch

    def test_07_anomaly_detector(self):
        detector = ThreatAnomalyDetector()
        detector.fit_on_corpus(np.empty((0, 8)))
        flagged = detector.detect_anomalies({
            "burst_score": 0.95,
            "diurnal_hours": [2, 3],
            "wallets": [{"burst_rate": 0.85}],
            "infrastructure": {"churn_score": 0.90}
        })
        self.assertGreater(len(flagged), 0)

    # FastAPI Endpoints Testing
    def test_08_api_health(self):
        resp = self.client.get("/api/ai/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "healthy")

    def test_09_api_models_info(self):
        resp = self.client.get("/api/ai/models/info")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("models", resp.json())

    def test_10_api_stylometry_compare(self):
        resp = self.client.post("/api/ai/stylometry/compare", json={
            "text_a": "WTS database breach dumps with 500k credentials. Payment strictly BTC.",
            "text_b": "Fresh corporate database dump available. Contact via Session. BTC payment."
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("character_similarity", data)
        self.assertIn("stylometric_score", data)

    def test_11_api_actor_compare(self):
        resp = self.client.post("/api/ai/actor/compare", json={
            "persona_a": {"name": "ShadowX"},
            "persona_b": {"name": "Shadow_X2026"}
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("overall_confidence", data)
        self.assertIn("classification", data)

    def test_12_api_migration_detect(self):
        resp = self.client.post("/api/ai/migration/detect", json={
            "persona_a": {"name": "ShadowX"},
            "persona_b": {"name": "Shadow_X2026"}
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["classification"], "Migration Candidate")

    def test_13_api_hypothesis_test(self):
        resp = self.client.post("/api/ai/hypothesis/test", json={
            "persona_a": {"name": "ShadowX"},
            "persona_b": {"name": "Shadow_X2026"}
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("hypothesis", data)
        self.assertIn("supporting_signals", data)

    def test_14_api_anomaly_detect(self):
        resp = self.client.post("/api/ai/anomaly/detect", json={
            "persona": {
                "name": "BurstyActor",
                "burst_score": 0.90,
                "diurnal_hours": [3]
            }
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("anomalies_detected", data)

    def test_15_api_get_profile(self):
        resp = self.client.get("/api/ai/actor/ShadowX/profile")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["name"], "ShadowX")

    def test_16_api_get_evidence(self):
        resp = self.client.get("/api/ai/actor/ShadowX/evidence?comparison_target=Shadow_X2026")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("supporting_evidence", data)
        self.assertIn("evidence_coverage", data)

    def test_17_api_graph_generation(self):
        resp = self.client.get("/api/ai/graph/actor-correlation?target=ShadowX")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("elements", data)
        self.assertIn("nodes", data["elements"])
        self.assertIn("edges", data["elements"])
        self.assertGreater(len(data["elements"]["nodes"]), 5)
        self.assertGreater(len(data["elements"]["edges"]), 5)

    def test_18_api_single_actor_graph(self):
        resp = self.client.get("/api/ai/graph/actor/ShadowX")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("elements", data)
        self.assertEqual(data["target"], "ShadowX")


if __name__ == "__main__":
    unittest.main()
