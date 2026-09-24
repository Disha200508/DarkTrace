"""
Comprehensive Model Evaluation & False-Positive Testing Suite
SIH26151: Dark Web Threat Actor De-anonymization

Evaluates:
1. PAN Authorship Stylometry Model Performance (Acc, Prec, Rec, F1, ROC-AUC, Brier, Same vs Diff)
2. Behavioral Anomaly Detection
3. False-Positive & Edge Case Test Suite (8 distinct scenarios from Section 27):
   - Scenario 1: High stylometry + high behavior (Positive migration candidate)
   - Scenario 2: High stylometry + low behavior (Divergent cadence dampens confidence)
   - Scenario 3: Low stylometry + high TTP (Shared tooling alone != same actor)
   - Scenario 4: No wallet evidence (Missing data handled gracefully without negative penalty)
   - Scenario 5: PGP mismatch (Contradiction engine dampens confidence)
   - Scenario 6: Infrastructure mismatch (Contradiction engine discounts score)
   - Scenario 7: Insufficient data (Evidence coverage flags 'Insufficient Data')
   - Scenario 8: Completely unrelated personas (Correctly un-correlated)
"""

import os
import json
import numpy as np
from ai.correlation.scoring import CorrelationEngine
from ai.preprocessing.synthetic import SyntheticInvestigationAdapter
from ai.models.stylometry_model import StylometryModel
from ai.models.anomaly_model import ThreatAnomalyDetector


def run_comprehensive_evaluation():
    print("=" * 80)
    print("SIH26151: COMPREHENSIVE AI/ML MODEL EVALUATION & FALSE-POSITIVE BENCHMARK")
    print("=" * 80)

    # 1. Stylometry Model Summary
    summary_path = "ai/saved_models/training_summary.json"
    if os.path.exists(summary_path):
        with open(summary_path, "r") as f:
            summary = json.load(f)
        tm = summary.get("test_metrics", {})
        print("\n[PART 1: PAN AUTHORSHIP VERIFICATION TEST METRICS]")
        print(f"  Selected Model:              {summary.get('selected_model')}")
        print(f"  Test Accuracy:               {tm.get('accuracy', 'N/A')}")
        print(f"  Test Precision:              {tm.get('precision', 'N/A')}")
        print(f"  Test Recall:                 {tm.get('recall', 'N/A')}")
        print(f"  Test F1-Score:               {tm.get('f1', 'N/A')}")
        print(f"  Test ROC-AUC:                {tm.get('roc_auc', 'N/A')}")
        print(f"  Same-Author Accuracy:        {tm.get('same_author_accuracy', 'N/A')}")
        print(f"  Different-Author Accuracy:   {tm.get('different_author_accuracy', 'N/A')}")
        print(f"  Confusion Matrix:            {tm.get('confusion_matrix', 'N/A')}")
    else:
        print("\n[PART 1: PAN Stylometry metrics pending model training]")

    # 2. Multi-Signal Fusion & False-Positive Testing Suite (Section 27)
    print("\n" + "=" * 80)
    print("[PART 2: FALSE-POSITIVE & MULTI-SIGNAL CORRELATION TEST CASES]")
    print("=" * 80)

    adapter = SyntheticInvestigationAdapter()
    engine = CorrelationEngine()

    test_cases = [
        {
            "id": "TC-1",
            "name": "High Stylometry + High Behavior (Known Migration Pair)",
            "persona_a": adapter.get_persona("ShadowX"),
            "persona_b": adapter.get_persona("Shadow_X2026"),
            "expected_classification": "Migration Candidate",
            "check": lambda res: res["overall_confidence"] >= 0.70 and res["classification"] == "Migration Candidate"
        },
        {
            "id": "TC-2",
            "name": "High Stylometry + Low Behavior (Cadence Divergence)",
            "persona_a": adapter.get_persona("ShadowX"),
            "persona_b": {
                **adapter.get_persona("ShadowX"),
                "diurnal_hours": [12, 13, 14, 15],  # Noon UTC (opposite from night)
                "active_days": [5, 6],              # Weekend only
                "burst_score": 0.05
            },
            "expected_classification": "Potential Association / Lowered Confidence",
            "check": lambda res: res["overall_confidence"] < 0.85
        },
        {
            "id": "TC-3",
            "name": "Low Stylometry + High TTP (Shared Tooling Only)",
            "persona_a": adapter.get_persona("ShadowX"),
            "persona_b": {
                "name": "ScriptKiddie_TTPReuse",
                "threat_category": "Novice",
                "posts": ["Hey guys where can I download free SQL injection tools and bypass windows defender?"],
                "diurnal_hours": [18, 19, 20],
                "active_days": [5, 6],
                "ttps": ["T1059", "T1190", "T1071", "T1566"],  # Same TTPs
                "wallets": []
            },
            "expected_classification": "Weak Association / Uncorrelated",
            "check": lambda res: res["classification"] in ["Weak Association", "Uncorrelated Personas"]
        },
        {
            "id": "TC-4",
            "name": "No Wallet Evidence (Missing Data Handling)",
            "persona_a": adapter.get_persona("ShadowX"),
            "persona_b": adapter.get_persona("GhostOperator"),
            "expected_classification": "Distinguish No Data from Negative Match",
            "check": lambda res: res["signals"]["wallet"] is None and "Cryptocurrency Transaction Pattern data is unavailable" in str(res["missing_evidence"])
        },
        {
            "id": "TC-5",
            "name": "PGP Mismatch (Contradiction Activation)",
            "persona_a": adapter.get_persona("ShadowX"),
            "persona_b": adapter.get_persona("DarkVortex"),
            "expected_classification": "Contradiction Flagged & Confidence Penalized",
            "check": lambda res: len(res["contradictory_evidence"]) > 0 and res["signals"]["pgp"] == 0.0
        },
        {
            "id": "TC-6",
            "name": "Infrastructure Mismatch (Opposing Infrastructure)",
            "persona_a": adapter.get_persona("ShadowX"),
            "persona_b": adapter.get_persona("DarkVortex"),
            "expected_classification": "Infrastructure Mismatch Flagged",
            "check": lambda res: any("Infrastructure" in c or "TLS" in c for c in res["contradictory_evidence"])
        },
        {
            "id": "TC-7",
            "name": "Insufficient Data (Low Evidence Coverage)",
            "persona_a": {"name": "EmptyPersona_A", "posts": []},
            "persona_b": {"name": "EmptyPersona_B", "posts": []},
            "expected_classification": "Insufficient Data",
            "check": lambda res: res["classification"] == "Insufficient Data" and res["evidence_coverage"] < 0.40
        },
        {
            "id": "TC-8",
            "name": "Completely Unrelated Personas",
            "persona_a": adapter.get_persona("DarkVortex"),
            "persona_b": adapter.get_persona("GhostOperator"),
            "expected_classification": "Uncorrelated Personas",
            "check": lambda res: res["classification"] == "Uncorrelated Personas" and res["overall_confidence"] < 0.40
        }
    ]

    passed_count = 0
    for tc in test_cases:
        res = engine.correlate_personas(tc["persona_a"], tc["persona_b"])
        passed = tc["check"](res)
        if passed:
            passed_count += 1
            status_str = "PASS [OK]"
        else:
            status_str = "FAIL [X]"

        print(f"\n{tc['id']}: {tc['name']}")
        print(f"  Status:              {status_str}")
        print(f"  Confidence:          {res['overall_confidence']:.4f}")
        print(f"  Coverage:            {res['evidence_coverage']:.2f}")
        print(f"  Classification:      {res['classification']}")
        print(f"  Contradictions:      {len(res['contradictory_evidence'])}")
        if res["contradictory_evidence"]:
            for c in res["contradictory_evidence"]:
                print(f"    - {c}")

    print("\n" + "=" * 80)
    print(f"TEST SUITE SUMMARY: {passed_count}/{len(test_cases)} Test Cases Passed.")
    print("=" * 80)

    # 3. Anomaly Detection Test
    print("\n[PART 3: BEHAVIORAL ANOMALY DETECTION TEST]")
    anom_detector = ThreatAnomalyDetector()
    anom_detector.fit_on_corpus(np.empty((0, 8)))

    # Test anomalous persona with burst posting, off-hours, and high churn
    anom_persona = {
        "name": "AnomalousActor",
        "posts": ["post 1", "post 2", "post 3", "post 4", "post 5", "post 6", "post 7", "post 8"],
        "burst_score": 0.88,
        "diurnal_hours": [2, 3, 4],
        "wallets": [{"burst_rate": 0.90}],
        "infrastructure": {"churn_score": 0.85}
    }
    flagged = anom_detector.detect_anomalies(anom_persona)
    print(f"Flagged {len(flagged)} anomalies for high-activity test profile:")
    for a in flagged:
        print(f"  - [{a['severity']}] {a['anomaly_type']}: {a['description']}")

    print("\nEvaluation suite completed successfully.")
    return passed_count == len(test_cases)


if __name__ == "__main__":
    run_comprehensive_evaluation()
