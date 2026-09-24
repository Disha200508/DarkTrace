"""
FastAPI Router for Read-Only Blockchain Module
SIH26151: Dark Web Threat Actor De-anonymization

Exposes:
- GET /api/blockchain/address/{address}
- GET /api/blockchain/transaction/{txid}
- GET /api/blockchain/status
- POST /api/blockchain/analyze
- POST /api/blockchain/mode

Safety Note:
Read-only queries only. Never handles private keys, signatures, or broadcasts.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ai.blockchain.service import BlockchainService
from ai.blockchain.validator import validate_bitcoin_address, validate_transaction_hash
from ai.blockchain.cache import GLOBAL_BLOCKCHAIN_CACHE

router = APIRouter(prefix="/api/blockchain", tags=["Read-Only Blockchain Intelligence"])

# Singleton service instance
_BLOCKCHAIN_SERVICE = BlockchainService()


class AnalyzeRequest(BaseModel):
    query: str = Field(..., description="Bitcoin address or transaction hash")
    comparison_target: Optional[str] = Field(None, description="Optional synthetic threat actor to correlate against")
    demo_mode: Optional[bool] = Field(None, description="Force demo mode on/off")


class ModeRequest(BaseModel):
    demo_mode: bool = Field(..., description="Set true for Offline Demo Mode, false for Live Public API")


@router.get("/address/{address}")
def api_get_address_info(
    address: str,
    target: Optional[str] = Query(None, description="Optional target threat actor ID to compare behavior"),
    demo: Optional[bool] = Query(None, description="Force demo mode"),
    refresh: bool = Query(False, description="Bypass cache and force refresh")
) -> Dict[str, Any]:
    """
    Retrieves public Bitcoin blockchain summary, transactions, behavior profile,
    Cytoscape graph, and AI correlation score for a Bitcoin address.
    """
    try:
        if demo is not None:
            _BLOCKCHAIN_SERVICE.set_demo_mode(demo)
        return _BLOCKCHAIN_SERVICE.analyze_address(
            address=address,
            comparison_actor_id=target,
            force_refresh=refresh
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain lookup error: {str(e)}")


@router.get("/transaction/{txid}")
def api_get_transaction(txid: str) -> Dict[str, Any]:
    """
    Retrieves transaction inputs, outputs, fee, confirmation status, and timeline entry.
    """
    try:
        return _BLOCKCHAIN_SERVICE.get_transaction_details(txid)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction lookup error: {str(e)}")


@router.post("/analyze")
def api_analyze_blockchain_query(req: AnalyzeRequest) -> Dict[str, Any]:
    """
    Unified analyzer for either a Bitcoin address or a 64-char transaction hash.
    """
    query = req.query.strip()
    if req.demo_mode is not None:
        _BLOCKCHAIN_SERVICE.set_demo_mode(req.demo_mode)

    # Check if address
    is_addr, _, _ = validate_bitcoin_address(query)
    if is_addr:
        try:
            return _BLOCKCHAIN_SERVICE.analyze_address(
                address=query,
                comparison_actor_id=req.comparison_target
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Check if transaction hash
    is_tx, _ = validate_transaction_hash(query)
    if is_tx:
        try:
            tx_data = _BLOCKCHAIN_SERVICE.get_transaction_details(query)
            is_demo = _BLOCKCHAIN_SERVICE.demo_mode
            return {
                "query_type": "TRANSACTION",
                "transaction": tx_data,
                "provenance": {
                    "source": "Synthetic Demonstration Data" if is_demo else "Public Bitcoin Blockchain",
                    "provider": _BLOCKCHAIN_SERVICE.get_active_provider().provider_name,
                    "mode": "DEMO" if is_demo else "LIVE"
                },
                "safety_notice": "Public transaction records reflect on-chain observations."
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(
        status_code=400,
        detail="Invalid input: Must be a valid Bitcoin address (Legacy, P2SH, Bech32, Taproot) or a 64-character transaction hash."
    )


@router.post("/mode")
def api_set_blockchain_mode(req: ModeRequest) -> Dict[str, Any]:
    """
    Toggles between Live Public Blockchain API and Offline Synthetic Demo Mode.
    """
    _BLOCKCHAIN_SERVICE.set_demo_mode(req.demo_mode)
    return {
        "status": "success",
        "demo_mode": _BLOCKCHAIN_SERVICE.demo_mode,
        "active_provider": _BLOCKCHAIN_SERVICE.get_active_provider().provider_name,
        "mode_label": "DEMO MODE" if _BLOCKCHAIN_SERVICE.demo_mode else "LIVE PUBLIC DATA"
    }


@router.get("/status")
def api_get_blockchain_status() -> Dict[str, Any]:
    """
    Returns blockchain module status, active provider, cache statistics, and connectivity.
    """
    provider = _BLOCKCHAIN_SERVICE.get_active_provider()
    return {
        "module": "Read-Only Blockchain Intelligence Module",
        "version": "1.0.0",
        "demo_mode": _BLOCKCHAIN_SERVICE.demo_mode,
        "mode_label": "DEMO MODE" if _BLOCKCHAIN_SERVICE.demo_mode else "LIVE PUBLIC DATA",
        "active_provider": provider.provider_name,
        "network": provider.network_name,
        "provider_healthy": provider.is_healthy(),
        "cache_stats": GLOBAL_BLOCKCHAIN_CACHE.get_stats(),
        "supported_address_types": [
            "Legacy (1...)",
            "P2SH / Nested SegWit (3...)",
            "Native SegWit Bech32 (bc1q...)",
            "Taproot Bech32m (bc1p...)"
        ],
        "safety_guarantees": [
            "Strictly GET / read-only operations",
            "No private keys or credentials processed",
            "No transaction signing or broadcasting",
            "Observable behavioral association only"
        ]
    }
