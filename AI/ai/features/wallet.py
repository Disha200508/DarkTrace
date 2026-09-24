"""
Wallet & Transaction Behavioral Similarity Extractor
SIH26151: Dark Web Threat Actor De-anonymization

Compares cryptocurrency transaction behaviors, volume flow ratios, graph degree,
and burst metrics using the Elliptic transaction representation framework.

Ethical / Safety Note:
Calculates behavioral and transactional similarity only. Does not attribute real-world private wallets.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from ai.preprocessing.elliptic import EllipticPreprocessor


class WalletExtractor:
    """Computes wallet behavioral vectors and pairwise behavioral similarity."""

    def __init__(self, elliptic_prep: Optional[EllipticPreprocessor] = None):
        self.elliptic_prep = elliptic_prep or EllipticPreprocessor()

    def compute_wallet_similarity(
        self,
        persona_a: Dict[str, Any],
        persona_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Computes wallet behavioral score comparing synthetic wallet transaction profiles.
        """
        wallets_a = persona_a.get("wallets", [])
        wallets_b = persona_b.get("wallets", [])

        if not wallets_a or not wallets_b:
            return {
                "wallet_score": None,  # Distinguish No Data from No Match
                "is_available": False,
                "evidence": ["Wallet transaction history unavailable for one or both personas."],
                "behavioral_distance": None
            }

        # Average wallet vectors if multiple wallets exist
        vecs_a = [self.elliptic_prep.extract_wallet_features(w) for w in wallets_a]
        vecs_b = [self.elliptic_prep.extract_wallet_features(w) for w in wallets_b]

        mean_a = np.mean(vecs_a, axis=0)
        mean_b = np.mean(vecs_b, axis=0)

        norm_a = np.linalg.norm(mean_a)
        norm_b = np.linalg.norm(mean_b)

        if norm_a > 0 and norm_b > 0:
            sim = float(np.dot(mean_a, mean_b) / (norm_a * norm_b))
        else:
            sim = 0.0

        sim = float(np.clip(sim, 0.0, 1.0))
        evidence = []

        if sim > 0.75:
            evidence.append(f"Highly compatible financial behavior profile (similarity: {sim:.2f})")
            w_a0 = wallets_a[0]
            w_b0 = wallets_b[0]
            evidence.append(f"Similar transaction frequency ({w_a0.get('tx_frequency')} vs {w_b0.get('tx_frequency')} tx/wk) and avg value ({w_a0.get('avg_tx_value')} vs {w_b0.get('avg_tx_value')} BTC)")
        elif sim < 0.40:
            evidence.append(f"Divergent transaction volume scale and graph degree (similarity: {sim:.2f})")

        return {
            "wallet_score": round(sim, 4),
            "is_available": True,
            "evidence": evidence,
            "wallet_count_a": len(wallets_a),
            "wallet_count_b": len(wallets_b)
        }
