"""
Evidence Aggregator & Coverage Engine
SIH26151: Dark Web Threat Actor De-anonymization

Generates transparent, source-attributed evidence records for every evaluated analytical signal.
Strictly distinguishes between 'No Match' (negative evidence) and 'No Data' (missing evidence).
Computes analytical evidence coverage.
"""

from typing import Dict, Any, List, Optional, Tuple


SIGNAL_METADATA = {
    "stylometry": {
        "name": "Stylometric Authorship Verification",
        "source": "PAN Authorship Verification Dataset",
        "method": "Character & Word N-Gram TF-IDF + Statistical Stylometry + Calibrated Classifier",
        "limitations": "Linguistic style can be obfuscated or mimicked; requires sufficient text length (>50 chars)."
    },
    "behavior": {
        "name": "Behavioral & Cadence Analysis",
        "source": "Dark Web Forum Telemetry & Activity Logs",
        "method": "36-Dimensional Cadence, Burstiness, and Forum Distribution Vector Cosine",
        "limitations": "Cadence may shift across operational phases or automated bot activity."
    },
    "activity_rhythm": {
        "name": "Diurnal Activity Rhythm",
        "source": "Forum Timestamp Records",
        "method": "24-Hour Diurnal Probability Curve Cosine Alignment",
        "limitations": "Timezone shifts, VPNs, or sleep schedules can alter diurnal rhythm."
    },
    "topic": {
        "name": "Thematic & Topic Affinity",
        "source": "safe_corpus.json & Dark Web Forum Lexicon",
        "method": "Domain-specific Cyber Threat Thematic Extraction & Vector Cosine",
        "limitations": "Threat actors frequently change operational focus or purchase access in new domains."
    },
    "timeline": {
        "name": "Timeline & Migration Succession",
        "source": "Operational Lifespan Telemetry",
        "method": "Chronological Gap & Succession Horizon Analysis",
        "limitations": "Assumes chronological handover; dormant intervals vary widely."
    },
    "ttp": {
        "name": "MITRE ATT&CK TTP Fingerprint",
        "source": "MITRE ATT&CK Enterprise STIX Knowledge Base",
        "method": "Technique Extraction & Tactic-Weighted Jaccard / Multi-Hot Cosine",
        "limitations": "TTPs depend on available threat intelligence reports and post content."
    },
    "wallet": {
        "name": "Cryptocurrency Transaction Pattern",
        "source": "Elliptic Bitcoin Transaction Dataset Framework",
        "method": "8-Dimensional Graph & Transaction Flow Representation Similarity",
        "limitations": "Behavioral similarity only; does not attribute private individual wallets."
    },
    "pgp": {
        "name": "PGP Cryptographic Signature",
        "source": "Synthetic PGP Key Ring Records",
        "method": "SHA-1 / Full Fingerprint and Key-ID Parity Match",
        "limitations": "Actors may generate new keys; public keys can be spoofed without signature verification."
    },
    "infrastructure": {
        "name": "Infrastructure & Certificate Reuse",
        "source": "Synthetic Hosting, ASN & TLS Certificate Data",
        "method": "Certificate SHA-256 Fingerprint, ASN Overlap, Domain Edit Similarity",
        "limitations": "Shared hosting and CDNs may cause coincidental ASN overlap."
    }
}


class EvidenceEngine:
    """Aggregates supporting, contradictory, and missing evidence across all modalities."""

    def __init__(self):
        self.signal_metadata = SIGNAL_METADATA

    def build_evidence_bundle(
        self,
        signals: Dict[str, Optional[float]],
        signal_details: Dict[str, Any],
        contradictions: List[str]
    ) -> Dict[str, Any]:
        """
        Builds the complete evidence report:
        - supporting_evidence (structured objects with source, method, limitations)
        - contradictory_evidence
        - missing_evidence
        - evidence_coverage (float 0..1)
        """
        supporting_evidence: List[Dict[str, Any]] = []
        missing_evidence: List[str] = []

        total_signals = len(self.signal_metadata)
        available_signals = 0

        for sig_key, meta in self.signal_metadata.items():
            score = signals.get(sig_key)
            det = signal_details.get(sig_key, {})
            ev_list = det.get("evidence", []) if isinstance(det, dict) else []

            if score is None:
                # No Data
                missing_evidence.append(f"{meta['name']} data is unavailable in current dossiers.")
            else:
                # Available signal
                available_signals += 1
                if score >= 0.50 or (sig_key == "pgp" and score > 0.0):
                    supporting_evidence.append({
                        "type": sig_key,
                        "name": meta["name"],
                        "score": round(score, 4),
                        "source": meta["source"],
                        "method": meta["method"],
                        "evidence": ev_list if ev_list else [f"Positive correlation score: {score:.2f}"],
                        "limitations": meta["limitations"]
                    })
                elif score < 0.35:
                    # Low score (weak evidence)
                    supporting_evidence.append({
                        "type": sig_key,
                        "name": meta["name"],
                        "score": round(score, 4),
                        "source": meta["source"],
                        "method": meta["method"],
                        "evidence": ev_list if ev_list else [f"Weak / uncorrelated score: {score:.2f}"],
                        "limitations": meta["limitations"]
                    })

        coverage = available_signals / max(total_signals, 1)

        return {
            "supporting_evidence": supporting_evidence,
            "contradictory_evidence": contradictions,
            "missing_evidence": missing_evidence,
            "evidence_coverage": round(coverage, 3),
            "available_signal_count": available_signals,
            "total_signal_count": total_signals
        }
