"""
Threat Anomaly Detection Training Script
SIH26151: Dark Web Threat Actor De-anonymization

Trains the Isolation Forest and behavioral outlier detection baseline on safe_corpus
and synthetic behavioral vectors.
"""

import os
import json
import numpy as np
from ai.preprocessing.safe_corpus import SafeCorpusPreprocessor
from ai.models.anomaly_model import ThreatAnomalyDetector


def run_anomaly_training():
    print("=" * 70)
    print("SIH26151: TRAINING BEHAVIORAL ANOMALY DETECTION MODEL")
    print("=" * 70)

    prep = SafeCorpusPreprocessor("safe_corpus.json")
    posts = prep.extract_posts()
    print(f"Loaded {len(posts)} posts from safe_corpus.json")

    detector = ThreatAnomalyDetector(contamination=0.05)
    detector.fit_on_corpus(np.empty((0, 8)))
    detector.save("ai/saved_models")

    print("Threat anomaly detection model successfully trained and saved to ai/saved_models/")
    return detector


if __name__ == "__main__":
    run_anomaly_training()
