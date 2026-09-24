"""
Confidence Calibration & Uncertainty Engine
SIH26151: Dark Web Threat Actor De-anonymization

Calibrates raw multi-signal affinity into reliable, uncertainty-aware analytical confidence.
Incorporates evidence coverage discounting, contradiction penalties, and logistic scaling.
"""

import math
from typing import Dict, Any, List, Optional
import numpy as np


class ConfidenceCalibrator:
    """Calibrates multi-signal correlation scores into uncertainty-aware analytical confidence."""

    def __init__(self, platt_a: float = 8.5, platt_b: float = -4.5):
        # Default Platt scaling sigmoid parameters: 1 / (1 + exp(-(a*x + b)))
        self.platt_a = platt_a
        self.platt_b = platt_b

    def sigmoid_calibrate(self, raw_score: float) -> float:
        """Applies calibrated sigmoid transfer function to raw multi-signal score."""
        x = np.clip(raw_score, 0.0, 1.0)
        logit = self.platt_a * (x - 0.5)
        calibrated = 1.0 / (1.0 + math.exp(-logit))
        return float(np.clip(calibrated, 0.0, 1.0))

    def compute_analytical_confidence(
        self,
        raw_weighted_score: float,
        evidence_coverage: float,
        contradiction_penalty: float,
        min_coverage_threshold: float = 0.40
    ) -> Dict[str, float]:
        """
        Computes final analytical confidence accounting for:
        1. Raw weighted multi-signal fusion
        2. Sigmoid probability calibration
        3. Evidence coverage discount factor (if coverage is low, confidence is dampened)
        4. Contradiction penalty subtraction
        """
        # 1. Base Calibrated Probability
        calibrated_prob = self.sigmoid_calibrate(raw_weighted_score)

        # 2. Coverage adjustment factor:
        # If coverage >= 0.70 -> full weight; if coverage < 0.40 -> significant dampening
        if evidence_coverage >= 0.70:
            coverage_factor = 1.0
        elif evidence_coverage >= min_coverage_threshold:
            coverage_factor = 0.70 + 0.30 * ((evidence_coverage - min_coverage_threshold) / (0.70 - min_coverage_threshold))
        else:
            coverage_factor = max(0.20, evidence_coverage / min_coverage_threshold * 0.70)

        # 3. Apply coverage factor & subtract contradiction penalty
        adjusted_confidence = (calibrated_prob * coverage_factor) - contradiction_penalty
        analytical_confidence = float(np.clip(adjusted_confidence, 0.0, 1.0))

        return {
            "raw_probability": round(float(raw_weighted_score), 4),
            "calibrated_probability": round(float(calibrated_prob), 4),
            "analytical_confidence": round(float(analytical_confidence), 4),
            "coverage_factor": round(float(coverage_factor), 3)
        }
