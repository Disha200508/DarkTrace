"""
Behavioral Fingerprint & Activity Feature Extraction
SIH26151: Dark Web Threat Actor De-anonymization

Extracts multidimensional behavioral patterns from synthetic persona activity:
- Posting frequency and cadence
- Inactivity intervals and variance
- Burstiness and session clustering
- Forum distribution entropy
- Category affinity
- 24-hour diurnal profile and 7-day weekly cadence
"""

import math
from typing import Dict, Any, List, Optional
import numpy as np


class BehaviorExtractor:
    """Extracts behavioral vectors and computes behavioral similarity between personas."""

    def __init__(self):
        pass

    def extract_behavior_vector(self, persona: Dict[str, Any]) -> np.ndarray:
        """
        Extracts standardized 36-dimensional behavioral vector:
        - [0..23]: 24-hour normalized diurnal distribution
        - [24..30]: 7-day normalized day-of-week distribution
        - [31]: Posting volume (log scaled)
        - [32]: Burstiness score
        - [33]: Forum distribution entropy
        - [34]: Threat category code
        - [35]: Average cadence rate
        """
        # 1. 24-hour diurnal profile
        diurnal = np.zeros(24, dtype=float)
        active_hours = persona.get("diurnal_hours", [])
        if active_hours:
            for h in active_hours:
                if 0 <= h < 24:
                    diurnal[h] += 1.0
            total_h = np.sum(diurnal)
            if total_h > 0:
                diurnal = diurnal / total_h
        else:
            diurnal = np.full(24, 1.0 / 24.0)

        # 2. 7-day weekly profile
        weekly = np.zeros(7, dtype=float)
        active_days = persona.get("active_days", [])
        if active_days:
            for d in active_days:
                if 0 <= d < 7:
                    weekly[d] += 1.0
            total_d = np.sum(weekly)
            if total_d > 0:
                weekly = weekly / total_d
        else:
            weekly = np.full(7, 1.0 / 7.0)

        # 3. Volume and post stats
        posts = persona.get("posts", [])
        post_count = len(posts)
        log_vol = np.log1p(float(post_count))

        # 4. Burstiness index (variance / mean ratio or synthetic metric)
        burstiness = float(persona.get("burst_score", 0.35 if post_count > 2 else 0.1))

        # 5. Forum diversity entropy
        forums = persona.get("forums", ["General"])
        f_counts = Counter_forums = {}
        for f in forums:
            f_counts[f] = f_counts.get(f, 0) + 1
        probs = [c / len(forums) for c in f_counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs) if probs else 0.0

        # 6. Threat category hash/encoding
        cat_str = str(persona.get("threat_category", "Unknown"))
        cat_code = (sum(ord(c) for c in cat_str) % 100) / 100.0

        # 7. Cadence rate
        cadence = float(persona.get("avg_posts_per_week", max(1.0, float(post_count) * 1.5)))
        norm_cadence = np.log1p(cadence)

        vec = np.concatenate([
            diurnal,              # 24 dims
            weekly,               # 7 dims
            [log_vol, burstiness, entropy, cat_code, norm_cadence]  # 5 dims
        ])
        return vec

    def compute_behavior_similarity(self, persona_a: Dict[str, Any], persona_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates cosine similarity and modular behavioral affinities between two personas.
        """
        vec_a = self.extract_behavior_vector(persona_a)
        vec_b = self.extract_behavior_vector(persona_b)

        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)

        if norm_a == 0 or norm_b == 0:
            overall_sim = 0.0
        else:
            overall_sim = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

        # Diurnal sub-similarity (first 24 dimensions)
        d_a, d_b = vec_a[:24], vec_b[:24]
        nd_a, nd_b = np.linalg.norm(d_a), np.linalg.norm(d_b)
        diurnal_sim = float(np.dot(d_a, d_b) / (nd_a * nd_b)) if (nd_a > 0 and nd_b > 0) else 0.0

        # Weekly sub-similarity (next 7 dimensions)
        w_a, w_b = vec_a[24:31], vec_b[24:31]
        nw_a, nw_b = np.linalg.norm(w_a), np.linalg.norm(w_b)
        weekly_sim = float(np.dot(w_a, w_b) / (nw_a * nw_b)) if (nw_a > 0 and nw_b > 0) else 0.0

        # Forum overlap
        forums_a = set(persona_a.get("forums", []))
        forums_b = set(persona_b.get("forums", []))
        forum_overlap = len(forums_a & forums_b) / max(len(forums_a | forums_b), 1)

        evidence = []
        if diurnal_sim > 0.75:
            evidence.append(f"Highly correlated 24-hour diurnal activity curve (similarity: {diurnal_sim:.2f})")
        elif diurnal_sim < 0.30:
            evidence.append(f"Disparate active hours (similarity: {diurnal_sim:.2f})")

        if weekly_sim > 0.80:
            evidence.append(f"Matching weekly activity pattern (similarity: {weekly_sim:.2f})")

        if forum_overlap > 0.50:
            evidence.append(f"Shared forum presence across: {', '.join(sorted(list(forums_a & forums_b)))}")

        return {
            "behavior_similarity": round(float(np.clip(overall_sim, 0.0, 1.0)), 4),
            "diurnal_similarity": round(float(np.clip(diurnal_sim, 0.0, 1.0)), 4),
            "weekly_similarity": round(float(np.clip(weekly_sim, 0.0, 1.0)), 4),
            "forum_overlap": round(float(forum_overlap), 4),
            "evidence": evidence
        }
