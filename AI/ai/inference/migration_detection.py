"""
Multi-Signal Migration Detection & Hypothesis Testing Interface
SIH26151: Dark Web Threat Actor De-anonymization

Provides high-level APIs for:
1. Migration candidate detection (Section 18)
2. Hypothesis testing (Section 26)
3. Threat actor temporal evolution & drift analysis (Section 25)
"""

from typing import Dict, Any, List, Optional
from ai.correlation.scoring import CorrelationEngine
from ai.preprocessing.synthetic import SyntheticInvestigationAdapter


def detect_migration(
    persona_a: Dict[str, Any],
    persona_b: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates whether Persona B represents a plausible migration / operational transition of Persona A.
    Returns master correlation signals, calibrated overall confidence, and classification.
    """
    engine = CorrelationEngine()
    return engine.correlate_personas(persona_a, persona_b)


def test_hypothesis(
    persona_a: Dict[str, Any],
    persona_b: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Formal analytical hypothesis test:
    Hypothesis: 'Persona B may represent a migration or linked operational identity of Persona A.'

    Returns:
    - hypothesis statement
    - supporting_signals
    - contradictory_signals
    - missing_signals
    - evidence_coverage
    - confidence
    - classification
    - safety_notice
    """
    name_a = persona_a.get("name", "Target A")
    name_b = persona_b.get("name", "Target B")

    engine = CorrelationEngine()
    result = engine.correlate_personas(persona_a, persona_b)

    supporting_signals = []
    for k, v in result["signals"].items():
        if v is not None and v >= 0.50:
            supporting_signals.append(f"{k.replace('_', ' ').title()} (Score: {v})")

    missing_signals = [k.replace("_", " ").title() for k, v in result["signals"].items() if v is None]

    return {
        "hypothesis": f"Persona '{name_b}' may represent an operational migration or associated cluster of Persona '{name_a}'.",
        "target_a": name_a,
        "target_b": name_b,
        "classification": result["classification"],
        "confidence": result["overall_confidence"],
        "calibrated_probability": result["calibrated_probability"],
        "supporting_signals": supporting_signals,
        "contradictory_signals": result["contradictory_evidence"],
        "missing_signals": missing_signals,
        "evidence_coverage": result["evidence_coverage"],
        "safety_notice": "Analytical similarity does not establish real-world identity."
    }


def analyze_actor_evolution(snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tracks temporal drift across chronological persona activity snapshots:
    stylometric stability, topic changes, TTP expansions, and infrastructure rotations.
    """
    if not snapshots or len(snapshots) < 2:
        return {
            "actor_evolution_score": 1.0,
            "drift_detected": False,
            "observations": ["Insufficient historical snapshots to calculate temporal drift."]
        }

    engine = CorrelationEngine()
    drift_scores = []
    observations = []

    for i in range(len(snapshots) - 1):
        s1 = snapshots[i]
        s2 = snapshots[i + 1]
        res = engine.correlate_personas(s1, s2)
        drift_scores.append(res["overall_confidence"])

        if res["overall_confidence"] < 0.60:
            observations.append(f"Significant behavioral/stylistic divergence observed between snapshot {i} and {i+1}.")

    avg_stability = float(sum(drift_scores) / len(drift_scores))
    evolution_score = round(avg_stability, 4)

    return {
        "actor_evolution_score": evolution_score,
        "stability_index": evolution_score,
        "drift_detected": avg_stability < 0.65,
        "snapshot_count": len(snapshots),
        "observations": observations if observations else ["Consistent operational fingerprint maintained across snapshots."]
    }
