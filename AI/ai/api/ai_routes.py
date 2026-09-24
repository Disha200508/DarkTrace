"""
FastAPI Backend Routes for SIH26151 AI/ML Pipeline
SIH26151: Dark Web Threat Actor De-anonymization

Exposes clean JSON REST endpoints for integration with the frontend application:
- POST /api/ai/stylometry/compare
- POST /api/ai/actor/compare
- POST /api/ai/migration/detect
- POST /api/ai/hypothesis/test
- POST /api/ai/anomaly/detect
- GET /api/ai/actor/{id}/profile
- GET /api/ai/actor/{id}/evidence
- GET /api/ai/health
- GET /api/ai/models/info
"""

from typing import Dict, Any, List, Optional
from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ai.inference.stylometry_inference import compare_texts, get_stylometry_model
from ai.inference.actor_similarity import compare_actors, get_actor_profile, get_adapter
from ai.inference.migration_detection import detect_migration, test_hypothesis, analyze_actor_evolution
from ai.models.anomaly_model import ThreatAnomalyDetector
from ai.correlation.scoring import CorrelationEngine


# Pydantic Request Models
class StylometryCompareRequest(BaseModel):
    text_a: str = Field(..., description="First text sample")
    text_b: str = Field(..., description="Second text sample")


class ActorCompareRequest(BaseModel):
    persona_a: Dict[str, Any] = Field(..., description="First persona data or name/ID")
    persona_b: Dict[str, Any] = Field(..., description="Second persona data or name/ID")


class MigrationDetectRequest(BaseModel):
    persona_a: Dict[str, Any] = Field(..., description="Candidate original persona")
    persona_b: Dict[str, Any] = Field(..., description="Candidate migrated persona")


class HypothesisTestRequest(BaseModel):
    persona_a: Dict[str, Any] = Field(..., description="Target persona A")
    persona_b: Dict[str, Any] = Field(..., description="Target persona B")


class AnomalyDetectRequest(BaseModel):
    persona: Dict[str, Any] = Field(..., description="Persona operational state")


# Initialize Router and App
router = APIRouter(prefix="/api/ai", tags=["AI Backend Pipeline"])


def _resolve_persona(val: Any) -> Dict[str, Any]:
    """Helper to resolve persona from string ID/name or dict object."""
    if isinstance(val, str):
        adapter = get_adapter()
        p = adapter.get_persona(val)
        if p is not None:
            return p
        return {"name": val, "posts": []}
    elif isinstance(val, dict):
        # If dict has 'name' or 'id' that matches known synthetic persona, merge it
        name_or_id = val.get("name") or val.get("id")
        if name_or_id and not val.get("posts"):
            adapter = get_adapter()
            known = adapter.get_persona(name_or_id)
            if known:
                return {**known, **val}
        return val
    return {"name": "Unknown", "posts": []}


@router.post("/stylometry/compare")
def api_stylometry_compare(req: StylometryCompareRequest) -> Dict[str, Any]:
    """
    Compares two text samples using character/word n-grams and statistical stylometry.
    Returns granular linguistic similarities and calibrated same-author probability.
    """
    try:
        return compare_texts(req.text_a, req.text_b)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actor/compare")
def api_actor_compare(req: ActorCompareRequest) -> Dict[str, Any]:
    """
    Performs full 9-signal multi-modal correlation between two threat actor personas.
    """
    try:
        pa = _resolve_persona(req.persona_a)
        pb = _resolve_persona(req.persona_b)
        engine = CorrelationEngine()
        return engine.correlate_personas(pa, pb)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/detect")
def api_migration_detect(req: MigrationDetectRequest) -> Dict[str, Any]:
    """
    Evaluates multi-signal persona migration hypothesis with calibrated analytical confidence.
    """
    try:
        pa = _resolve_persona(req.persona_a)
        pb = _resolve_persona(req.persona_b)
        return detect_migration(pa, pb)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hypothesis/test")
def api_hypothesis_test(req: HypothesisTestRequest) -> Dict[str, Any]:
    """
    Tests formal hypothesis of persona migration/association with supporting and contradictory evidence.
    """
    try:
        pa = _resolve_persona(req.persona_a)
        pb = _resolve_persona(req.persona_b)
        return test_hypothesis(pa, pb)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomaly/detect")
def api_anomaly_detect(req: AnomalyDetectRequest) -> Dict[str, Any]:
    """
    Detects behavioral, operational, and financial anomalies using Isolation Forest & LOF.
    """
    try:
        p = _resolve_persona(req.persona)
        detector = ThreatAnomalyDetector()
        detector.fit_on_corpus(None)
        anomalies = detector.detect_anomalies(p)
        return {
            "target": p.get("name", "Unknown"),
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "safety_notice": "Analytical anomaly detection flags operational pattern shifts."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actor/{actor_id}/profile")
def api_get_actor_profile(actor_id: str) -> Dict[str, Any]:
    """Retrieves full profile dossier for a synthetic threat actor."""
    adapter = get_adapter()
    profile = adapter.get_persona(actor_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Actor '{actor_id}' not found in investigation registry.")
    return profile


@router.get("/actor/{actor_id}/evidence")
def api_get_actor_evidence(actor_id: str, comparison_target: Optional[str] = Query(None)) -> Dict[str, Any]:
    """
    Retrieves evidence bundle for an actor, optionally correlated against a comparison target.
    """
    adapter = get_adapter()
    profile_a = adapter.get_persona(actor_id)
    if profile_a is None:
        raise HTTPException(status_code=404, detail=f"Actor '{actor_id}' not found.")

    target_b_id = comparison_target or "Shadow_X2026"
    profile_b = adapter.get_persona(target_b_id) or adapter.get_persona("DarkVortex")

    engine = CorrelationEngine()
    result = engine.correlate_personas(profile_a, profile_b)
    return {
        "target": profile_a.get("name"),
        "comparison_target": profile_b.get("name"),
        "evidence_coverage": result["evidence_coverage"],
        "supporting_evidence": result["supporting_evidence"],
        "contradictory_evidence": result["contradictory_evidence"],
        "missing_evidence": result["missing_evidence"],
        "methodology": result["methodology"],
        "safety_notice": result["safety_notice"]
    }


@router.get("/graph/actor-correlation")
def api_get_actor_correlation_graph(target: str = Query("ShadowX", description="Target Threat Actor Name")) -> Dict[str, Any]:
    """
    Generates Cytoscape.js compatible graph topology connecting threat actors,
    darknet handles, PGP keys, primary inflow wallets, secondary wallets (mixers, infra, off-ramp),
    and migration links.
    """
    try:
        from ai.inference.graph_generator import ThreatCorrelationGraphGenerator
        generator = ThreatCorrelationGraphGenerator()
        return generator.generate_full_correlation_graph(target_actor_name=target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/actor/{actor_id}")
def api_get_single_actor_graph(actor_id: str) -> Dict[str, Any]:
    """
    Generates focused graph elements for a single threat actor dossier.
    """
    try:
        from ai.inference.graph_generator import ThreatCorrelationGraphGenerator
        generator = ThreatCorrelationGraphGenerator()
        adapter = get_adapter()
        persona = adapter.get_persona(actor_id)
        if persona is None:
            raise HTTPException(status_code=404, detail=f"Actor '{actor_id}' not found.")
        sub = generator.generate_actor_subgraph(persona)
        return {
            "target": persona.get("name"),
            "elements": sub,
            "node_count": len(sub["nodes"]),
            "edge_count": len(sub["edges"]),
            "safety_notice": "Relationships represent potential associations."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def api_health() -> Dict[str, Any]:
    """Pipeline health check endpoint."""
    return {
        "status": "healthy",
        "service": "SIH26151 Threat Actor De-anonymization AI Engine",
        "version": "1.0.0",
        "models_loaded": {
            "stylometry_verifier": True,
            "anomaly_detector": True,
            "correlation_engine": True
        }
    }


@router.get("/models/info")
def api_models_info() -> Dict[str, Any]:
    """Returns metadata and metrics on trained models."""
    sty_model = get_stylometry_model()
    return {
        "pipeline_version": "1.0.0",
        "models": [
            {
                "model_name": "stylometry_verifier",
                "version": sty_model.version,
                "type": sty_model.metrics.get("model_type", "logistic_regression"),
                "methodology": "Character + Word N-Gram + Statistical Stylometry",
                "calibration": "Platt Scaling (Sigmoid)",
                "metrics": sty_model.metrics
            },
            {
                "model_name": "threat_anomaly_detector",
                "version": "1.0.0",
                "type": "Isolation Forest",
                "methodology": "Multivariate behavioral feature deviation"
            },
            {
                "model_name": "multi_signal_correlation_engine",
                "version": "1.0.0",
                "methodology": "Dynamic Available-Signal Weighted Fusion with Contradiction Penalties"
            }
        ],
        "datasets": [
            "PAN Authorship Verification Dataset (2022)",
            "safe_corpus.json (Anonymized dark web forum corpus)",
            "MITRE ATT&CK STIX Enterprise Bundle",
            "Elliptic Bitcoin Transaction Dataset",
            "Synthetic Threat Actor Investigation Records"
        ]
    }


from ai.blockchain.blockchain_routes import router as blockchain_router

# Standalone FastAPI Application creation
app = FastAPI(
    title="SIH26151 Threat Actor De-anonymization AI Backend",
    description="Machine Learning Training & Inference Engine with Read-Only Blockchain Intelligence",
    version="1.0.0"
)
app.include_router(router)
app.include_router(blockchain_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
