"""
Contradiction Detection Engine
SIH26151: Dark Web Threat Actor De-anonymization

Identifies contradictory signals, operational impossibilities, and conflicting evidence
between two threat actor personas to prevent confirmation bias and false-positive attribution.
"""

from typing import Dict, Any, List, Tuple, Optional


class ContradictionEngine:
    """Detects opposing signals and computes calibrated confidence penalty factors."""

    def __init__(self, penalty_config: Optional[Dict[str, float]] = None):
        self.penalties = penalty_config or {
            "pgp_mismatch": 0.18,
            "temporal_impossibility": 0.25,
            "severe_diurnal_mismatch": 0.12,
            "opposing_threat_focus": 0.08,
            "conflicting_infrastructure": 0.10
        }

    def evaluate_contradictions(
        self,
        signals: Dict[str, Optional[float]],
        persona_a: Dict[str, Any],
        persona_b: Dict[str, Any],
        sub_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates signals and raw dossiers for substantive contradictions.
        Returns list of contradiction statements and composite penalty factor.
        """
        contradictions: List[str] = []
        penalty_accum = 0.0

        # 1. PGP Cryptographic Mismatch
        # If both personas explicitly provide PGP keys and they mismatch, it is strong counter-evidence
        pgp_score = signals.get("pgp")
        if pgp_score is not None and pgp_score == 0.0:
            fp_a = persona_a.get("pgp_fingerprint", "Unknown")
            fp_b = persona_b.get("pgp_fingerprint", "Unknown")
            contradictions.append(f"Cryptographic Mismatch: Explicitly conflicting PGP keys ({fp_a[:15]}... vs {fp_b[:15]}...).")
            penalty_accum += self.penalties.get("pgp_mismatch", 0.18)

        # 2. Severe Diurnal Rhythm / Timezone Conflict
        diurnal_sim = sub_details.get("diurnal_similarity") if sub_details else None
        if diurnal_sim is not None and diurnal_sim < 0.20:
            contradictions.append(f"Temporal/Diurnal Contradiction: Disjoint 24-hour activity curves (similarity: {diurnal_sim:.2f}) indicating different operational timezones.")
            penalty_accum += self.penalties.get("severe_diurnal_mismatch", 0.12)

        # 3. Timeline Conflict / Long-term concurrent operation
        timeline_details = sub_details.get("timeline") if sub_details else {}
        timeline_contradictions = timeline_details.get("contradictions", [])
        for tc in timeline_contradictions:
            contradictions.append(tc)
            penalty_accum += self.penalties.get("temporal_impossibility", 0.25)

        # 4. Infrastructure Conflict
        infra_score = signals.get("infrastructure")
        cert_sim = sub_details.get("certificate_similarity") if sub_details else None
        if cert_sim is not None and cert_sim == 0.0 and infra_score is not None and infra_score < 0.25:
            contradictions.append("Infrastructure Mismatch: Completely disjoint hosting ASNs and conflicting TLS certificate fingerprints.")
            penalty_accum += self.penalties.get("conflicting_infrastructure", 0.10)

        # 5. Stylometry vs Behavioral Conflict
        sty_score = signals.get("stylometry")
        beh_score = signals.get("behavior")
        ttp_score = signals.get("ttp")

        if sty_score is not None and beh_score is not None:
            if sty_score > 0.85 and beh_score < 0.25:
                contradictions.append("Signal Divergence: High stylometric resemblance but sharply conflicting behavioral and cadence patterns.")
            elif sty_score < 0.25 and beh_score > 0.85:
                contradictions.append("Signal Divergence: High behavioral cadence similarity but contrasting linguistic/stylometric profiles.")

        # 6. Low Stylometry + High TTP (Commodity Tooling / Script Kiddie Mimicry)
        if sty_score is not None and sty_score < 0.35 and ttp_score is not None and ttp_score > 0.70:
            contradictions.append("Commodity Tooling Pattern: Shared attack techniques without linguistic/stylometric affinity indicates commodity tool usage rather than same threat actor.")
            penalty_accum += self.penalties.get("opposing_threat_focus", 0.15)

        # Cap penalty at 0.50 max reduction
        total_penalty = min(0.50, penalty_accum)

        return {
            "contradictions": contradictions,
            "penalty_factor": round(total_penalty, 3),
            "has_contradictions": len(contradictions) > 0
        }
