"""
Blockchain Intelligence Service Orchestrator
SIH26151: Dark Web Threat Actor De-anonymization

Coordinates:
- Bitcoin address / hash validation
- Provider abstraction & mode selection (Mempool.space live API vs Synthetic Demo Provider)
- In-memory TTL caching
- Analytical metric calculation & flow analysis
- Cytoscape.js transaction graph construction with connected components & validated edges
- AI wallet behavior representation & similarity matching (Similarity != Identity)
- Forensic Risk Score calculation & Investigation Dossier formatting

Safety Notice:
Strictly read-only; no private keys, no signing, no broadcasting.
All outputs represent 'Observable Transaction Connections' or 'Potential Associations'.
"""

import os
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from dotenv import load_dotenv

# Ensure .env is loaded on startup
load_dotenv(override=True)

from ai.blockchain.validator import validate_bitcoin_address, validate_transaction_hash
from ai.blockchain.cache import GLOBAL_BLOCKCHAIN_CACHE
from ai.blockchain.provider.base_provider import BlockchainProvider
from ai.blockchain.provider.mempool_provider import MempoolBlockchainProvider
from ai.blockchain.provider.synthetic_provider import SyntheticBlockchainProvider, DemoBlockchainProvider
from ai.blockchain.analytics import BlockchainAnalyticsEngine
from ai.preprocessing.synthetic import SyntheticInvestigationAdapter
from ai.features.wallet import WalletExtractor


class BlockchainService:
    """High-level facade for read-only Bitcoin intelligence lookups and AI analysis."""

    def __init__(self):
        # Reload env to pick up any runtime environment adjustments
        load_dotenv(override=True)

        self.analytics = BlockchainAnalyticsEngine()
        self.synthetic_adapter = SyntheticInvestigationAdapter()
        self.wallet_extractor = WalletExtractor()

        # Initialize providers
        self.synthetic_provider = SyntheticBlockchainProvider()
        self.mempool_provider = MempoolBlockchainProvider()
        
        # Aliases for backwards compatibility
        self.demo_provider = self.synthetic_provider
        self.live_provider = self.mempool_provider

        # Demo mode toggle (read directly from BLOCKCHAIN_DEMO_MODE)
        demo_env = os.getenv("BLOCKCHAIN_DEMO_MODE", "false").strip().lower()
        self.demo_mode = demo_env in ("true", "1", "yes")

        print(f"[SIH26151 Blockchain] Active Provider: {self.get_active_provider().provider_name} | Demo Mode: {self.demo_mode}")

    def set_demo_mode(self, enabled: bool) -> None:
        """Toggles between Live Public API and Offline Demo Mode."""
        self.demo_mode = enabled

    def get_active_provider(self) -> BlockchainProvider:
        """Selects active provider based on mode configuration."""
        if self.demo_mode:
            return self.synthetic_provider
        return self.mempool_provider

    def analyze_address(
        self,
        address: str,
        comparison_actor_id: Optional[str] = None,
        force_refresh: bool = False,
        demo_mode_override: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end address lookup, analytics, graph generation, and AI correlation.
        """
        # 1. Input Validation
        is_valid, addr_type, err = validate_bitcoin_address(address)
        if not is_valid:
            raise ValueError(err or "Invalid Bitcoin address format.")

        clean_addr = address.strip()
        is_demo = self.demo_mode if demo_mode_override is None else demo_mode_override
        cache_key = f"addr_analysis_{clean_addr}_{'demo' if is_demo else 'live'}"

        # 2. Cache Lookup
        if not force_refresh:
            cached = GLOBAL_BLOCKCHAIN_CACHE.get(cache_key)
            if cached:
                cached["from_cache"] = True
                return cached

        # 3. Provider Selection & Data Fetching
        if is_demo:
            provider = self.synthetic_provider
            source_label = "SYNTHETIC DEMO"
        else:
            provider = self.mempool_provider
            source_label = "LIVE PUBLIC BLOCKCHAIN"

        info = provider.get_address_info(clean_addr)
        txs = provider.get_address_transactions(clean_addr, limit=25)
        utxo_details = provider.get_address_utxos_detailed(clean_addr)
        utxos = utxo_details.get("utxos", [])

        # 4. Core Analytics Calculation
        stats = self.analytics.calculate_wallet_statistics(info, txs, utxos, utxo_details=utxo_details)
        behavior = self.analytics.generate_behavior_profile(stats, txs)
        flow = self.analytics.calculate_flow_analysis(stats, txs)
        graph = self.analytics.build_transaction_graph(clean_addr, txs)
        anomalies = self.analytics.detect_behavioral_anomalies(stats, txs)
        forensic_risk = self.analytics.calculate_forensic_risk_score(stats, anomalies, graph)

        # 5. AI Integration: Compare Live/Observed Vector against Synthetic Threat Actor Wallets
        ai_similarity_score = None
        compared_target = None
        if comparison_actor_id:
            target_persona = self.synthetic_adapter.get_persona(comparison_actor_id)
        else:
            target_persona = self.synthetic_adapter.get_persona("ShadowX")

        if target_persona and target_persona.get("wallets"):
            compared_target = target_persona.get("name")
            target_w = target_persona["wallets"][0]
            target_vec = self.wallet_extractor.elliptic_prep.extract_wallet_features(target_w)
            live_vec = np.array(behavior["vector_8d"])

            norm_t = np.linalg.norm(target_vec)
            norm_l = np.linalg.norm(live_vec)
            if norm_t > 0 and norm_l > 0:
                ai_similarity_score = float(np.dot(target_vec, live_vec) / (norm_t * norm_l))
                ai_similarity_score = round(float(np.clip(ai_similarity_score, 0.0, 1.0)), 4)

        # 6. Provenance & Dossier Entry
        if is_demo:
            provenance_info = {
                "source": "Synthetic Demonstration Data",
                "provider": provider.provider_name,
                "mode": "DEMO",
                "retrieved_at": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime())
            }
        else:
            provenance_info = {
                "source": "Public Bitcoin Blockchain",
                "provider": provider.provider_name,
                "mode": "LIVE",
                "retrieved_at": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime())
            }

        # 7. Construct Master Standardized Output JSON
        response_payload = {
            "address": clean_addr,
            "address_type": addr_type,
            "network": provider.network_name,
            "source_type": source_label,
            "provider": provider.provider_name,
            "demo_mode": is_demo,
            "retrieved_at": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),

            "summary": {
                "transaction_count": stats["total_transactions"],
                "total_received_btc": stats["total_received_btc"],
                "total_spent_btc": stats["total_spent_btc"],
                "unspent_btc": stats["total_unspent_btc"],
                "observable_utxos": stats["observable_utxos"],
                "utxo_status": stats["utxo_status"],
                "utxo_note": stats["utxo_note"],
                "first_seen": stats["first_seen"],
                "last_seen": stats["last_seen"],
                "observed_window": stats["observed_window"],
                "active_days": stats["active_days"],
                "average_transaction_value": stats["average_transaction_value"],
                "median_transaction_value": stats["median_transaction_value"],
                "largest_transaction": stats["largest_transaction"]
            },

            "behavior": behavior["profile"],

            "ai_integration": {
                "wallet_behavior_score": ai_similarity_score,
                "compared_target": compared_target,
                "interpretation": "Potential Behavioral Association based on 8-D transaction flow vector cosine similarity",
                "methodology": "Elliptic Bitcoin Representation Alignment",
                "disclaimer": "Behavioral similarity indicates pattern correlation and does NOT imply identity probability or wallet ownership."
            },

            "flow_analysis": flow,

            "forensic_risk": forensic_risk,

            "anomalies": anomalies,

            "transactions": txs,

            "utxos": utxos,

            "graph": {
                "nodes": graph["nodes"],
                "edges": graph["edges"],
                "node_count": graph["node_count"],
                "edge_count": graph["edge_count"],
                "clustering": graph["clustering"]
            },

            "investigation_dossier_entry": {
                "section": "BLOCKCHAIN OBSERVATION",
                "network": provider.network_name,
                "address": clean_addr,
                "first_seen": stats["first_seen"],
                "last_seen": stats["last_seen"],
                "observed_window": stats["observed_window"],
                "transaction_count": stats["total_transactions"],
                "total_received": f"{stats['total_received_btc']} BTC",
                "total_spent": f"{stats['total_spent_btc']} BTC",
                "observable_utxo": f"{stats['total_unspent_btc']} BTC",
                "observable_utxos_count": stats["observable_utxos"],
                "utxo_status": stats["utxo_status"],
                "average_transaction": f"{stats['average_transaction_value']} BTC",
                "largest_transaction": f"{stats['largest_transaction']} BTC",
                "forensic_risk_score": forensic_risk["forensic_risk_score"],
                "risk_level": forensic_risk["risk_level"],
                "provenance": provenance_info
            },

            "limitations": [
                "Observable blockchain behavior does not establish real-world ownership or identity.",
                "Connections between addresses represent observable transaction flow heuristics only.",
                "Public blockchain records reflect immutable on-chain data."
            ],
            "from_cache": False
        }

        # Store in Cache
        GLOBAL_BLOCKCHAIN_CACHE.set(cache_key, response_payload)
        return response_payload

    def get_transaction_details(self, txid: str, demo_mode_override: Optional[bool] = None) -> Dict[str, Any]:
        """Validates and retrieves single transaction details."""
        is_valid, err = validate_transaction_hash(txid)
        if not is_valid:
            raise ValueError(err or "Invalid transaction hash.")

        clean_txid = txid.strip()
        is_demo = self.demo_mode if demo_mode_override is None else demo_mode_override
        cache_key = f"tx_details_{clean_txid}_{'demo' if is_demo else 'live'}"
        
        cached = GLOBAL_BLOCKCHAIN_CACHE.get(cache_key)
        if cached:
            return cached

        provider = self.synthetic_provider if is_demo else self.mempool_provider
        tx_data = provider.get_transaction(clean_txid)

        GLOBAL_BLOCKCHAIN_CACHE.set(cache_key, tx_data)
        return tx_data
