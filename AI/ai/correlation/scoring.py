"""
Weighted Correlation & Master Signal Fusion Engine
SIH26151: Dark Web Threat Actor De-anonymization

Integrates all 9 analytical modalities into explainable multi-signal correlation scores:
Stylometry, Behavior, Activity Rhythm, Topic, Timeline, Wallet, PGP, Infrastructure, TTP.

Dynamically weights available signals without penalizing missing data, checks for contradictions,
aggregates evidence bundles, calibrates confidence, and formats the Master AI JSON output.
"""

import os
import yaml
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from ai.correlation.evidence import EvidenceEngine
from ai.correlation.contradictions import ContradictionEngine
from ai.correlation.confidence import ConfidenceCalibrator
from ai.features.stylometry import StylometryExtractor
from ai.features.behavior import BehaviorExtractor
from ai.features.timeline import TimelineExtractor
from ai.features.topics import TopicExtractor
from ai.features.ttp import TTPExtractor
from ai.features.wallet import WalletExtractor
from ai.features.infrastructure import InfrastructureExtractor
from ai.models.stylometry_model import StylometryModel


class CorrelationEngine:
    """Master multi-signal fusion and hypothesis evaluation engine."""

    def __init__(self, config_path: str = "ai/config/scoring.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.weights = self.config.get("weights", {
            "stylometry": 0.25,
            "behavior": 0.15,
            "activity_rhythm": 0.10,
            "topic": 0.10,
            "timeline": 0.10,
            "ttp": 0.15,
            "wallet": 0.08,
            "pgp": 0.04,
            "infrastructure": 0.03
        })
        self.thresholds = self.config.get("thresholds", {
            "migration_candidate": 0.75,
            "potential_association": 0.55,
            "weak_association": 0.35,
            "min_evidence_coverage": 0.40
        })

        # Sub-engines
        self.evidence_engine = EvidenceEngine()
        self.contradiction_engine = ContradictionEngine(self.config.get("contradiction_penalties"))
        self.confidence_calibrator = ConfidenceCalibrator()

        # Feature extractors
        self.behavior_ext = BehaviorExtractor()
        self.timeline_ext = TimelineExtractor()
        self.topic_ext = TopicExtractor()
        self.ttp_ext = TTPExtractor()
        self.wallet_ext = WalletExtractor()
        self.infra_ext = InfrastructureExtractor()

        # Stylometry model
        self.stylometry_model = StylometryModel()
        # Attempt to load trained weights if saved
        if os.path.exists("ai/saved_models/model.pkl"):
            self.stylometry_model.load("ai/saved_models")

    def _load_config(self) -> Dict[str, Any]:
        """Loads configuration YAML."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {}

    def correlate_personas(
        self,
        persona_a: Dict[str, Any],
        persona_b: Dict[str, Any],
        target_name_a: Optional[str] = None,
        target_name_b: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes full 9-signal analytical correlation between two threat actor personas.
        Produces complete Master AI JSON output.
        """
        name_a = target_name_a or persona_a.get("name", "Target_A")
        name_b = target_name_b or persona_b.get("name", "Target_B")

        signal_details: Dict[str, Any] = {}
        signals: Dict[str, Optional[float]] = {}

        # 1. STYLOMETRY SIGNAL
        posts_a = persona_a.get("posts", [])
        posts_b = persona_b.get("posts", [])
        text_a = " \n".join(posts_a)
        text_b = " \n".join(posts_b)

        if text_a and text_b:
            sty_res = self.stylometry_model.compare_texts(text_a, text_b)
            signals["stylometry"] = sty_res["stylometric_score"]
            signal_details["stylometry"] = {
                "score": sty_res["stylometric_score"],
                "evidence": [
                    f"Character n-gram similarity: {sty_res['character_similarity']:.2f}",
                    f"Word n-gram similarity: {sty_res['word_similarity']:.2f}",
                    f"Vocabulary profile similarity: {sty_res['vocabulary_similarity']:.2f}",
                    f"Punctuation distribution similarity: {sty_res['punctuation_similarity']:.2f}",
                    f"Syntactic rhythm similarity: {sty_res['syntax_similarity']:.2f}"
                ]
            }
        else:
            signals["stylometry"] = None
            signal_details["stylometry"] = {"evidence": ["No post texts available."]}

        # 2. BEHAVIOR SIGNAL
        beh_res = self.behavior_ext.compute_behavior_similarity(persona_a, persona_b)
        signals["behavior"] = beh_res["behavior_similarity"]
        signal_details["behavior"] = {"evidence": beh_res["evidence"]}

        # 3. ACTIVITY RHYTHM (DIURNAL) SIGNAL
        signals["activity_rhythm"] = beh_res["diurnal_similarity"]
        signal_details["activity_rhythm"] = {
            "evidence": [f"Diurnal 24-hour activity curve alignment: {beh_res['diurnal_similarity']:.2f}"]
        }

        # 4. TOPIC SIGNAL
        top_res = self.topic_ext.compute_topic_similarity(persona_a, persona_b)
        signals["topic"] = top_res["topic_score"] if top_res["is_available"] else None
        signal_details["topic"] = {"evidence": top_res["evidence"]}

        # 5. TIMELINE SIGNAL
        tl_res = self.timeline_ext.evaluate_timeline_migration(persona_a, persona_b)
        signals["timeline"] = tl_res["timeline_score"] if tl_res["is_available"] else None
        signal_details["timeline"] = tl_res

        # 6. TTP / MITRE ATT&CK SIGNAL
        ttp_res = self.ttp_ext.compute_ttp_similarity(persona_a, persona_b)
        signals["ttp"] = ttp_res["ttp_score"] if ttp_res["is_available"] else None
        signal_details["ttp"] = {"evidence": ttp_res["evidence"]}

        # 7. WALLET SIGNAL
        w_res = self.wallet_ext.compute_wallet_similarity(persona_a, persona_b)
        signals["wallet"] = w_res["wallet_score"]  # may be None
        signal_details["wallet"] = {"evidence": w_res["evidence"]}

        # 8. PGP SIGNAL
        pgp_res = self.infra_ext.evaluate_pgp(persona_a, persona_b)
        signals["pgp"] = pgp_res["pgp_score"]  # may be None, 0.0, 0.5, or 1.0
        signal_details["pgp"] = {"evidence": pgp_res["evidence"]}

        # 9. INFRASTRUCTURE SIGNAL
        infra_res = self.infra_ext.evaluate_infrastructure(persona_a, persona_b)
        signals["infrastructure"] = infra_res["infrastructure_score"] if infra_res["is_available"] else None
        signal_details["infrastructure"] = {"evidence": infra_res["evidence"]}
        signal_details["certificate_similarity"] = infra_res.get("certificate_similarity")

        # ----------------------------------------------------------------------
        # DYNAMIC WEIGHTED FUSION (Normalizing over available signals only)
        # ----------------------------------------------------------------------
        available_weights = []
        available_scores = []

        for k, weight in self.weights.items():
            score = signals.get(k)
            if score is not None:
                available_weights.append(weight)
                available_scores.append(score)

        if available_weights:
            total_w = sum(available_weights)
            raw_fusion_score = sum(s * w for s, w in zip(available_scores, available_weights)) / total_w
        else:
            raw_fusion_score = 0.0

        # ----------------------------------------------------------------------
        # CONTRADICTION DETECTION & PENALTIES
        # ----------------------------------------------------------------------
        contra_res = self.contradiction_engine.evaluate_contradictions(
            signals=signals,
            persona_a=persona_a,
            persona_b=persona_b,
            sub_details={
                "diurnal_similarity": beh_res["diurnal_similarity"],
                "timeline": tl_res,
                "certificate_similarity": infra_res.get("certificate_similarity")
            }
        )

        # ----------------------------------------------------------------------
        # EVIDENCE BUNDLE & COVERAGE
        # ----------------------------------------------------------------------
        ev_bundle = self.evidence_engine.build_evidence_bundle(
            signals=signals,
            signal_details=signal_details,
            contradictions=contra_res["contradictions"]
        )

        # ----------------------------------------------------------------------
        # CONFIDENCE CALIBRATION
        # ----------------------------------------------------------------------
        calib_res = self.confidence_calibrator.compute_analytical_confidence(
            raw_weighted_score=raw_fusion_score,
            evidence_coverage=ev_bundle["evidence_coverage"],
            contradiction_penalty=contra_res["penalty_factor"],
            min_coverage_threshold=self.thresholds.get("min_evidence_coverage", 0.40)
        )

        confidence = calib_res["analytical_confidence"]

        # Classification decision
        if ev_bundle["evidence_coverage"] < self.thresholds.get("min_evidence_coverage", 0.40):
            classification = "Insufficient Data"
        elif confidence >= self.thresholds.get("migration_candidate", 0.75):
            classification = "Migration Candidate"
        elif confidence >= self.thresholds.get("potential_association", 0.55):
            classification = "Potential Association"
        elif confidence >= self.thresholds.get("weak_association", 0.35):
            classification = "Weak Association"
        else:
            classification = "Uncorrelated Personas"

        # Construct final output JSON
        return {
            "case_id": f"CASE-SIH26151-{name_a.upper()}",
            "target": name_a,
            "comparison_target": name_b,
            "signals": {
                "stylometry": signals.get("stylometry"),
                "behavior": signals.get("behavior"),
                "activity_rhythm": signals.get("activity_rhythm"),
                "topic": signals.get("topic"),
                "timeline": signals.get("timeline"),
                "wallet": signals.get("wallet"),
                "pgp": signals.get("pgp"),
                "infrastructure": signals.get("infrastructure"),
                "ttp": signals.get("ttp"),
                "campaign_score": round(float(raw_fusion_score), 4)
            },
            "overall_confidence": confidence,
            "raw_probability": calib_res["raw_probability"],
            "calibrated_probability": calib_res["calibrated_probability"],
            "classification": classification,
            "supporting_evidence": ev_bundle["supporting_evidence"],
            "contradictory_evidence": ev_bundle["contradictory_evidence"],
            "missing_evidence": ev_bundle["missing_evidence"],
            "evidence_coverage": ev_bundle["evidence_coverage"],
            "methodology": [
                "PAN Authorship Stylometry Verification",
                "Diurnal & Weekly Behavioral Profiling",
                "MITRE ATT&CK STIX TTP Alignment",
                "Elliptic Bitcoin Behavioral Flow Adapter",
                "Temporal Succession Analysis",
                "Contradiction Engine & Sigmoid Confidence Calibration"
            ],
            "data_sources": [
                "safe_corpus.json",
                "PAN Authorship Verification (2022)",
                "MITRE ATT&CK Enterprise STIX",
                "Elliptic Bitcoin Dataset",
                "Synthetic Investigation Dossiers"
            ],
            "safety_notice": "Analytical similarity does not establish real-world identity."
        }
