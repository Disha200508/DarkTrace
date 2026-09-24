"""
Stylometry Inference Interface
SIH26151: Dark Web Threat Actor De-anonymization

Exposes clean, probabilistic stylometric comparison for arbitrary text pairs:
compare_texts(text_a, text_b)
"""

import os
from typing import Dict, Any, Optional
from ai.models.stylometry_model import StylometryModel

# Singleton inference model instance
_STYLOMETRY_MODEL: Optional[StylometryModel] = None


def get_stylometry_model() -> StylometryModel:
    """Lazy-loads and returns the singleton stylometry model."""
    global _STYLOMETRY_MODEL
    if _STYLOMETRY_MODEL is None:
        model = StylometryModel()
        if os.path.exists("ai/saved_models/model.pkl"):
            model.load("ai/saved_models")
        _STYLOMETRY_MODEL = model
    return _STYLOMETRY_MODEL


def compare_texts(text_a: str, text_b: str) -> Dict[str, Any]:
    """
    Compares two raw texts and produces granular linguistic similarities,
    overall stylometric score, calibrated same-author probability, and classification.

    Output format:
    {
      "character_similarity": 0,
      "word_similarity": 0,
      "vocabulary_similarity": 0,
      "punctuation_similarity": 0,
      "syntax_similarity": 0,
      "stylometric_score": 0,
      "same_author_probability": 0,
      "classification": "Potential Same-Author Pattern",
      "model_name": "stylometry_verifier",
      "model_version": "1.0.0",
      "feature_version": "1.0.0",
      "methodology": "Character + Word N-Gram + Statistical Stylometry"
    }
    """
    model = get_stylometry_model()
    return model.compare_texts(text_a, text_b)
