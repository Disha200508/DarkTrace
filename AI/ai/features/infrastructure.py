"""
PGP, Infrastructure & Certificate Feature Extraction
SIH26151: Dark Web Threat Actor De-anonymization

Computes analytical signals for:
- PGP key verification (exact fingerprint match, key ID match, mismatch, or missing)
- TLS/SSL certificate fingerprint and issuer compatibility
- Autonomous System Number (ASN) and hosting overlap
- Domain structure similarity and infrastructure churn rate

Safety Note:
Only processes authorized synthetic records; never conducts unauthorized active scans.
"""

import difflib
from typing import Dict, Any, List, Optional, Tuple


class InfrastructureExtractor:
    """Evaluates cryptographic PGP fingerprints and synthetic hosting/cert infrastructure."""

    def __init__(self):
        pass

    def evaluate_pgp(self, persona_a: Dict[str, Any], persona_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates PGP signature alignment:
        1.0 = exact fingerprint match
        0.5 = partial metadata / key ID match
        0.0 = explicit mismatch
        None = missing / unavailable
        """
        fp_a = persona_a.get("pgp_fingerprint")
        fp_b = persona_b.get("pgp_fingerprint")
        kid_a = persona_a.get("pgp_key_id")
        kid_b = persona_b.get("pgp_key_id")

        if not fp_a and not fp_b and not kid_a and not kid_b:
            return {
                "pgp_score": None,
                "is_available": False,
                "status": "missing",
                "evidence": ["No PGP key records available for either persona."],
                "is_mismatch": False
            }
        elif (fp_a and not fp_b) or (fp_b and not fp_a):
            return {
                "pgp_score": None,
                "is_available": False,
                "status": "partial_data",
                "evidence": ["PGP key present for only one persona; cannot evaluate parity."],
                "is_mismatch": False
            }

        clean_a = str(fp_a).replace(" ", "").upper()
        clean_b = str(fp_b).replace(" ", "").upper()

        if clean_a == clean_b and clean_a:
            return {
                "pgp_score": 1.0,
                "is_available": True,
                "status": "exact_match",
                "evidence": [f"Exact cryptographic PGP fingerprint match: {fp_a}"],
                "is_mismatch": False
            }
        elif kid_a and kid_b and str(kid_a).upper() == str(kid_b).upper():
            return {
                "pgp_score": 0.5,
                "is_available": True,
                "status": "partial_keyid_match",
                "evidence": [f"Matching PGP Key ID: {kid_a}"],
                "is_mismatch": False
            }
        else:
            return {
                "pgp_score": 0.0,
                "is_available": True,
                "status": "mismatch",
                "evidence": [f"Conflicting PGP fingerprints ({fp_a} vs {fp_b})"],
                "is_mismatch": True
            }

    def evaluate_infrastructure(
        self,
        persona_a: Dict[str, Any],
        persona_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates synthetic infrastructure: domain naming patterns, certificate fingerprints, ASNs, churn.
        """
        infra_a = persona_a.get("infrastructure", {})
        infra_b = persona_b.get("infrastructure", {})

        if not infra_a and not infra_b:
            return {
                "infrastructure_score": None,
                "certificate_similarity": None,
                "churn_score": 0.0,
                "is_available": False,
                "evidence": ["No infrastructure records available."]
            }

        evidence = []
        scores = []
        weights = []

        # 1. Certificate Fingerprint Match
        cert_a = infra_a.get("certificate_fingerprint")
        cert_b = infra_b.get("certificate_fingerprint")
        cert_sim = 0.0
        if cert_a and cert_b:
            if cert_a.upper() == cert_b.upper():
                cert_sim = 1.0
                evidence.append(f"Identical TLS/SSL Certificate SHA-256 fingerprint: {cert_a[:20]}...")
            else:
                cert_sim = 0.0
                evidence.append("Different TLS/SSL Certificate fingerprints.")
            scores.append(cert_sim)
            weights.append(0.40)

        # 2. ASN Overlap
        asns_a = set(infra_a.get("asns", []))
        asns_b = set(infra_b.get("asns", []))
        if asns_a and asns_b:
            asn_overlap = len(asns_a & asns_b) / max(len(asns_a | asns_b), 1)
            if asn_overlap > 0:
                evidence.append(f"Shared Autonomous System Numbers (ASNs): {', '.join(sorted(list(asns_a & asns_b)))}")
            scores.append(asn_overlap)
            weights.append(0.30)

        # 3. Domain Pattern Similarity
        doms_a = infra_a.get("domains", [])
        doms_b = infra_b.get("domains", [])
        if doms_a and doms_b:
            dom_sims = []
            for da in doms_a:
                for db in doms_b:
                    sim = difflib.SequenceMatcher(None, da.lower(), db.lower()).ratio()
                    dom_sims.append(sim)
            max_dom_sim = max(dom_sims) if dom_sims else 0.0
            if max_dom_sim > 0.60:
                evidence.append(f"High domain lexical pattern similarity ({max_dom_sim:.2f}) across infrastructure assets")
            scores.append(max_dom_sim)
            weights.append(0.30)

        # 4. Churn score
        churn_a = infra_a.get("churn_score", 0.3)
        churn_b = infra_b.get("churn_score", 0.3)
        avg_churn = (churn_a + churn_b) / 2.0

        if scores and weights:
            total_w = sum(weights)
            final_infra_score = sum(s * w for s, w in zip(scores, weights)) / total_w
        else:
            final_infra_score = 0.50

        return {
            "infrastructure_score": round(float(final_infra_score), 4),
            "certificate_similarity": round(float(cert_sim), 4) if (cert_a and cert_b) else None,
            "churn_score": round(float(avg_churn), 4),
            "is_available": bool(scores),
            "evidence": evidence
        }
