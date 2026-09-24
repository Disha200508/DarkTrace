"""
Actor Similarity Inference Module
SIH26151: Dark Web Threat Actor De-anonymization

Exposes persona profile extraction and pairwise behavioral & forensic comparison.
"""

from typing import Dict, Any, Optional
from ai.correlation.scoring import CorrelationEngine
from ai.preprocessing.synthetic import SyntheticInvestigationAdapter

_CORRELATION_ENGINE: Optional[CorrelationEngine] = None
_ADAPTER: Optional[SyntheticInvestigationAdapter] = None


def get_correlation_engine() -> CorrelationEngine:
    global _CORRELATION_ENGINE
    if _CORRELATION_ENGINE is None:
        _CORRELATION_ENGINE = CorrelationEngine()
    return _CORRELATION_ENGINE


def get_adapter() -> SyntheticInvestigationAdapter:
    global _ADAPTER
    if _ADAPTER is None:
        _ADAPTER = SyntheticInvestigationAdapter()
    return _ADAPTER


def compare_actors(persona_a_dict: Dict[str, Any], persona_b_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Compares two persona profiles across all 9 analytical dimensions."""
    engine = get_correlation_engine()
    return engine.correlate_personas(persona_a_dict, persona_b_dict)


def get_actor_profile(actor_id_or_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves full profile dossier for a given synthetic actor ID or name."""
    adapter = get_adapter()
    return adapter.get_persona(actor_id_or_name)
