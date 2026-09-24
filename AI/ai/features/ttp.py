"""
MITRE ATT&CK TTP Feature Vectorizer & Comparator
SIH26151: Dark Web Threat Actor De-anonymization

Vectorizes Tactics, Techniques, and Procedures (TTPs) based on enterprise ATT&CK STIX
and calculates structural similarity between threat actors.
"""

from typing import Dict, Any, List, Set, Optional
import numpy as np
from ai.preprocessing.mitre import MitreAttackKB


class TTPExtractor:
    """Computes TTP fingerprints and structural alignment scores."""

    def __init__(self, kb: Optional[MitreAttackKB] = None):
        self.kb = kb or MitreAttackKB()

    def extract_ttp_vector(self, ttp_ids: List[str]) -> np.ndarray:
        """Converts list of technique IDs into multi-hot vector over all known techniques."""
        all_ids = self.kb.all_technique_ids()
        vec = np.zeros(len(all_ids), dtype=float)
        id_to_idx = {tid: i for i, tid in enumerate(all_ids)}

        for tid in ttp_ids:
            clean_id = tid.strip().upper()
            if clean_id in id_to_idx:
                vec[id_to_idx[clean_id]] = 1.0
            # Also credit parent technique if sub-technique
            if "." in clean_id:
                parent = clean_id.split(".")[0]
                if parent in id_to_idx:
                    vec[id_to_idx[parent]] = 0.5
        return vec

    def compute_ttp_similarity(
        self,
        persona_a: Dict[str, Any],
        persona_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Computes TTP similarity between two personas using Jaccard and multi-hot cosine similarity.
        """
        ttps_a = set(persona_a.get("ttps", []))
        ttps_b = set(persona_b.get("ttps", []))

        # Check if text extraction needed
        if not ttps_a and persona_a.get("posts"):
            extracted = self.kb.extract_ttps_from_text(" ".join(persona_a["posts"]))
            ttps_a = set(extracted["ttp_ids"])
        if not ttps_b and persona_b.get("posts"):
            extracted = self.kb.extract_ttps_from_text(" ".join(persona_b["posts"]))
            ttps_b = set(extracted["ttp_ids"])

        if not ttps_a and not ttps_b:
            return {
                "ttp_score": 0.0,
                "is_available": False,
                "shared_ttps": [],
                "diff_ttps": [],
                "ttp_confidence": 0.0,
                "evidence": ["No MITRE ATT&CK TTP records or indicators available for either persona."]
            }

        shared = sorted(list(ttps_a & ttps_b))
        diff = sorted(list((ttps_a - ttps_b) | (ttps_b - ttps_a)))
        total_union = len(ttps_a | ttps_b)

        jaccard = len(shared) / max(total_union, 1)

        # Build technique names for shared TTPs
        shared_details = []
        for tid in shared:
            t_obj = self.kb.get_technique(tid)
            name = t_obj.name if t_obj else "Unknown"
            shared_details.append(f"{tid} ({name})")

        evidence = []
        if shared:
            evidence.append(f"Shared ATT&CK Techniques: {', '.join(shared_details)}")
        if diff:
            evidence.append(f"Unmatched individual techniques: {', '.join(diff[:4])}")

        return {
            "ttp_score": round(float(jaccard), 4),
            "is_available": True,
            "shared_ttps": shared,
            "diff_ttps": diff,
            "shared_details": shared_details,
            "ttp_confidence": round(min(0.95, 0.40 + 0.15 * len(shared)), 3),
            "evidence": evidence
        }
