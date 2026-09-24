"""
Topic Similarity & Lexical Distribution Model
SIH26151: Dark Web Threat Actor De-anonymization

Extracts topic distributions, thematic clusters, and key dark-web operational vocabularies
from persona post histories. Computes cosine topic similarity, shared topics, and divergent topics.
"""

import re
from typing import Dict, Any, List, Set, Tuple
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


# Known dark web cyber domain topic taxonomies
THEMATIC_DOMAINS = {
    "data_breach": ["leak", "database", "dump", "schema", "records", "sql", "breach", "credentials", "emails"],
    "malware_dev": ["loader", "stealer", "rat", "obfuscation", "memory", "injection", "crypter", "stub", "payload", "c2"],
    "ransomware": ["ransom", "encrypt", "decryptor", "aes", "rsa", "negotiation", "extortion", "payment", "lock"],
    "initial_access": ["rdp", "vpn", "access", "corporate", "domain", "admin", "privilege", "active directory", "citrix"],
    "cryptocurrency": ["escrow", "btc", "bitcoin", "xmr", "monero", "wallet", "points", "transaction", "payment"],
    "espionage_ics": ["scada", "ics", "telemetry", "dns", "tunneling", "edr", "evasion", "apt", "spearphishing"]
}


class TopicExtractor:
    """Extracts topic vectors and explains topical overlap and divergence."""

    def __init__(self, max_features: int = 200):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=max_features,
            ngram_range=(1, 2)
        )
        self.is_fitted = False

    def fit(self, all_texts: List[str]) -> "TopicExtractor":
        """Fits TF-IDF vectorizer on background corpus."""
        valid = [t for t in all_texts if t and len(t.strip()) > 5]
        if not valid:
            valid = ["cyber security exploit database leak malware sample placeholder"]
        self.vectorizer.fit(valid)
        self.is_fitted = True
        return self

    def extract_thematic_profile(self, texts: List[str]) -> Dict[str, float]:
        """Maps text collection to predefined cyber threat thematic domains."""
        combined = " ".join(texts).lower()
        profile: Dict[str, float] = {}
        for domain, kws in THEMATIC_DOMAINS.items():
            matches = sum(1 for kw in kws if re.search(r"\b" + re.escape(kw) + r"\b", combined))
            score = matches / len(kws)
            profile[domain] = score
        return profile

    def compute_topic_similarity(self, persona_a: Dict[str, Any], persona_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates topic similarity between two personas, returning:
        - topic_score
        - shared_topics
        - different_topics
        - evidence
        """
        texts_a = persona_a.get("posts", [])
        texts_b = persona_b.get("posts", [])

        if not texts_a or not texts_b:
            return {
                "topic_score": 0.0,
                "shared_topics": [],
                "different_topics": [],
                "is_available": False,
                "evidence": ["No post texts available to extract topic distributions."]
            }

        prof_a = self.extract_thematic_profile(texts_a)
        prof_b = self.extract_thematic_profile(texts_b)

        # Vector cosine similarity over thematic domains
        v_a = np.array([prof_a[k] for k in sorted(prof_a.keys())], dtype=float)
        v_b = np.array([prof_b[k] for k in sorted(prof_b.keys())], dtype=float)

        norm_a = np.linalg.norm(v_a)
        norm_b = np.linalg.norm(v_b)

        if norm_a > 0 and norm_b > 0:
            cos_sim = float(np.dot(v_a, v_b) / (norm_a * norm_b))
        else:
            cos_sim = 0.0

        shared_topics = []
        different_topics = []

        for k in sorted(prof_a.keys()):
            sa, sb = prof_a[k], prof_b[k]
            if sa > 0.15 and sb > 0.15:
                shared_topics.append(k.replace("_", " ").title())
            elif (sa > 0.20 and sb == 0) or (sb > 0.20 and sa == 0):
                different_topics.append(k.replace("_", " ").title())

        evidence = []
        if shared_topics:
            evidence.append(f"Strong thematic convergence in operational domains: {', '.join(shared_topics)}")
        if different_topics:
            evidence.append(f"Divergent focus noted in domains: {', '.join(different_topics)}")

        return {
            "topic_score": round(float(np.clip(cos_sim, 0.0, 1.0)), 4),
            "shared_topics": shared_topics,
            "different_topics": different_topics,
            "is_available": True,
            "evidence": evidence
        }
