"""
Timeline & Activity Rhythm Feature Extraction
SIH26151: Dark Web Threat Actor De-anonymization

Analyzes temporal migration dynamics, chronological succession, activity gap intervals,
and 24-hour diurnal rhythm continuity between persona profiles.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class TimelineExtractor:
    """Evaluates temporal migration consistency and timeline succession."""

    def __init__(self):
        pass

    def parse_date(self, date_val: Any) -> Optional[datetime]:
        """Safely parses ISO / standard date strings."""
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val
        date_str = str(date_val).strip()
        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y/%m/%d", "%d-%m-%Y"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def evaluate_timeline_migration(
        self,
        persona_a: Dict[str, Any],
        persona_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates temporal migration compatibility:
        - Succession (Persona A ceases -> Persona B emerges within reasonable window, e.g. 1-180 days)
        - Overlap (Partial operational handover vs permanent concurrent existence)
        - Chronological order
        """
        period_a = persona_a.get("active_period", {})
        period_b = persona_b.get("active_period", {})

        start_a = self.parse_date(period_a.get("start"))
        end_a = self.parse_date(period_a.get("end"))
        start_b = self.parse_date(period_b.get("start"))
        end_b = self.parse_date(period_b.get("end"))

        evidence = []
        contradictions = []

        if not (start_a and end_a and start_b and end_b):
            return {
                "timeline_score": 0.50,
                "is_available": False,
                "evidence": ["Incomplete temporal interval records for one or both personas."],
                "contradictions": []
            }

        # Calculate chronological delta
        # Scenario 1: Clean succession (A finishes, B starts shortly after)
        gap_days = (start_b - end_a).days

        if 0 <= gap_days <= 120:
            timeline_score = 0.90 - (gap_days / 120.0) * 0.15
            evidence.append(f"Plausible chronological migration: Persona B emerged {gap_days} days after Persona A ceased activity.")
        elif -60 <= gap_days < 0:
            # Overlap during transition phase (e.g. 1-2 months handover)
            timeline_score = 0.82
            evidence.append(f"Transition overlap: Persona B established {abs(gap_days)} days prior to retirement of Persona A.")
        elif gap_days > 120:
            # Dormant period
            timeline_score = max(0.40, 0.75 - (gap_days - 120) * 0.001)
            evidence.append(f"Extended dormancy interval ({gap_days} days) between persona operational lifespans.")
        else:
            # gap_days < -180: Heavy concurrent operation for years
            overlap_days = abs(gap_days)
            timeline_score = max(0.20, 0.50 - (overlap_days / 365.0) * 0.25)
            contradictions.append(f"Significant concurrent active lifespan ({overlap_days} days overlap), reducing migration probability.")

        return {
            "timeline_score": round(float(timeline_score), 4),
            "is_available": True,
            "gap_days": gap_days,
            "evidence": evidence,
            "contradictions": contradictions
        }
