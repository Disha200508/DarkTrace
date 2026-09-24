"""
Unit & Integration Tests for Read-Only Blockchain Intelligence Module
SIH26151: Dark Web Threat Actor De-anonymization

Tests:
1. Address validation (Legacy, P2SH, SegWit, Taproot, Invalid)
2. Transaction hash validation
3. Provider responses (Mempool & Synthetic Demo Provider)
4. UTXO limit handling (>500 UTXOs -> observable_utxos=None, status=UNAVAILABLE_PROVIDER_LIMIT)
5. Observed window handling (partial page vs complete history)
6. Graph consistency (every edge connects valid nodes, dynamic clustering)
7. Multi-address tests (High-UTXO Genesis, zero-tx, active, invalid)
8. In-memory caching and TTL
9. FastAPI endpoints and AI behavioral similarity scoring
"""

import unittest
from fastapi.testclient import TestClient

from ai.blockchain.validator import validate_bitcoin_address, validate_transaction_hash
from ai.blockchain.cache import BlockchainCache
from ai.blockchain.provider.synthetic_provider import SyntheticBlockchainProvider
from ai.blockchain.provider.mempool_provider import MempoolBlockchainProvider
from ai.blockchain.analytics import BlockchainAnalyticsEngine
from ai.blockchain.service import BlockchainService
from ai.api.ai_routes import app


class TestBlockchainModule(unittest.TestCase):
    """Test suite for blockchain module components."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.service = BlockchainService()
        cls.analytics = BlockchainAnalyticsEngine()
        cls.demo_provider = SyntheticBlockchainProvider()
        cls.mempool_provider = MempoolBlockchainProvider()

    # 1. Address Validation Tests
    def test_01_valid_legacy_address(self):
        is_valid, addr_type, err = validate_bitcoin_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        self.assertTrue(is_valid)
        self.assertIn("Legacy", addr_type)
        self.assertIsNone(err)

    def test_02_valid_p2sh_address(self):
        is_valid, addr_type, err = validate_bitcoin_address("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy")
        self.assertTrue(is_valid)
        self.assertIn("P2SH", addr_type)
        self.assertIsNone(err)

    def test_03_valid_bech32_address(self):
        is_valid, addr_type, err = validate_bitcoin_address("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq")
        self.assertTrue(is_valid)
        self.assertIn("SegWit", addr_type)
        self.assertIsNone(err)

    def test_04_valid_taproot_address(self):
        valid_tr = "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"
        is_valid, addr_type, err = validate_bitcoin_address(valid_tr)
        self.assertTrue(is_valid)
        self.assertIn("Taproot", addr_type)

    def test_05_invalid_addresses(self):
        invalid_cases = [
            "",
            "not_an_address",
            "1InvalidChars0OIl",
            "bc1invalidbech32characters!!",
            "0x1234567890abcdef1234567890abcdef12345678"
        ]
        for inv in invalid_cases:
            is_valid, _, err = validate_bitcoin_address(inv)
            self.assertFalse(is_valid)
            self.assertIsNotNone(err)

    # 2. Transaction Hash Validation Tests
    def test_06_valid_transaction_hash(self):
        valid_txid = "a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d"
        is_valid, err = validate_transaction_hash(valid_txid)
        self.assertTrue(is_valid)
        self.assertIsNone(err)

    def test_07_invalid_transaction_hash(self):
        invalid_txids = ["short_hash", "z" * 64, "1234", ""]
        for inv in invalid_txids:
            is_valid, err = validate_transaction_hash(inv)
            self.assertFalse(is_valid)
            self.assertIsNotNone(err)

    # 3. Provider & Analytics Tests
    def test_08_demo_provider_deterministic_output(self):
        addr = "1ShadowX9947bc1qxy2kgdygjrsqtzq2n0yrf249"
        info1 = self.demo_provider.get_address_info(addr)
        info2 = self.demo_provider.get_address_info(addr)
        self.assertEqual(info1["total_received_btc"], info2["total_received_btc"])
        self.assertGreater(info1["total_transactions"], 0)

        txs = self.demo_provider.get_address_transactions(addr)
        self.assertGreater(len(txs), 0)
        self.assertIn("direction", txs[0])

    def test_09_wallet_analytics_and_behavior(self):
        addr = "1ShadowX9947bc1qxy2kgdygjrsqtzq2n0yrf249"
        info = self.demo_provider.get_address_info(addr)
        txs = self.demo_provider.get_address_transactions(addr)
        utxo_details = self.demo_provider.get_address_utxos_detailed(addr)

        stats = self.analytics.calculate_wallet_statistics(info, txs, utxo_details["utxos"], utxo_details=utxo_details)
        self.assertIn("average_transaction_value", stats)
        self.assertIn("observed_window", stats)
        self.assertIn("observable_utxos", stats)

        behavior = self.analytics.generate_behavior_profile(stats, txs)
        self.assertEqual(len(behavior["vector_8d"]), 8)
        self.assertIn("counterparty_diversity", behavior["profile"])

        flow = self.analytics.calculate_flow_analysis(stats, txs)
        self.assertIn("net_observable_flow_btc", flow)

        graph = self.analytics.build_transaction_graph(addr, txs)
        self.assertGreater(len(graph["nodes"]), 0)
        self.assertGreater(len(graph["edges"]), 0)

    # 4. Cache Tests
    def test_10_cache_ttl_and_stats(self):
        cache = BlockchainCache(default_ttl_seconds=2)
        cache.set("test_key", {"data": 123})
        self.assertEqual(cache.get("test_key"), {"data": 123})
        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 1)

    # 5. FastAPI Endpoints Tests
    def test_11_api_get_status(self):
        resp = self.client.get("/api/blockchain/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("active_provider", data)
        self.assertIn("supported_address_types", data)

    def test_12_api_get_address_demo_mode(self):
        resp = self.client.get("/api/blockchain/address/1ShadowX9947bc1qxy2kgdygjrsqtzq2n0yrf249?demo=true")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["address"], "1ShadowX9947bc1qxy2kgdygjrsqtzq2n0yrf249")
        self.assertIn("summary", data)
        self.assertIn("behavior", data)
        self.assertIn("graph", data)
        self.assertIn("ai_integration", data)
        self.assertIn("investigation_dossier_entry", data)
        self.assertIn("limitations", data)

    def test_13_api_get_invalid_address(self):
        resp = self.client.get("/api/blockchain/address/invalid_address_123")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.json())

    def test_14_api_get_transaction(self):
        txid = "a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d"
        resp = self.client.get(f"/api/blockchain/transaction/{txid}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["txid"], txid)
        self.assertIn("inputs", data)
        self.assertIn("outputs", data)

    def test_15_api_analyze_unified_address(self):
        resp = self.client.post("/api/blockchain/analyze", json={
            "query": "1ShadowX9947bc1qxy2kgdygjrsqtzq2n0yrf249",
            "demo_mode": True
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("summary", data)
        self.assertIn("forensic_risk", data)

    def test_16_api_analyze_unified_transaction(self):
        txid = "b2075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48e"
        resp = self.client.post("/api/blockchain/analyze", json={
            "query": txid,
            "demo_mode": True
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["query_type"], "TRANSACTION")

    def test_17_api_mode_toggle(self):
        resp = self.client.post("/api/blockchain/mode", json={"demo_mode": True})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["demo_mode"])

    # 6. Specific Fix Tests: UTXO Limit Handling
    def test_18_utxo_limit_handling(self):
        """When provider returns >500 UTXO limit, observable_utxos must be null and status UNAVAILABLE_PROVIDER_LIMIT."""
        mock_limit_details = {
            "utxos": [],
            "observable_utxos": None,
            "utxo_status": "UNAVAILABLE_PROVIDER_LIMIT",
            "utxo_note": "Complete UTXO enumeration unavailable because the provider limits this address to 500 UTXOs."
        }
        info = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "total_transactions": 66000,
            "total_received_btc": 57.45,
            "total_spent_btc": 0.0,
            "total_unspent_btc": 57.45
        }
        stats = self.analytics.calculate_wallet_statistics(info, [], [], utxo_details=mock_limit_details)
        self.assertIsNone(stats["observable_utxos"])
        self.assertEqual(stats["utxo_status"], "UNAVAILABLE_PROVIDER_LIMIT")
        self.assertIn("500 UTXOs", stats["utxo_note"])
        self.assertEqual(stats["total_unspent_btc"], 57.45)

    # 7. Specific Fix Tests: Observed Window Partial vs Complete
    def test_19_observed_window_partial_vs_complete(self):
        """If total_tx > len(txs), complete must be False and first_seen/last_seen must be null."""
        info_partial = {"address": "1TestPartial", "total_transactions": 100, "total_received_btc": 1.0}
        txs_partial = [{"timestamp": 1700000000, "output_value_btc": 0.5, "direction": "INBOUND"}]
        stats_p = self.analytics.calculate_wallet_statistics(info_partial, txs_partial, [])
        self.assertFalse(stats_p["observed_window"]["complete"])
        self.assertIsNone(stats_p["first_seen"])
        self.assertIsNone(stats_p["last_seen"])
        self.assertIsNotNone(stats_p["observed_window"]["first_observed"])

        # Complete history case
        info_complete = {"address": "1TestComplete", "total_transactions": 1, "total_received_btc": 1.0}
        stats_c = self.analytics.calculate_wallet_statistics(info_complete, txs_partial, [])
        self.assertTrue(stats_c["observed_window"]["complete"])
        self.assertIsNotNone(stats_c["first_seen"])
        self.assertIsNotNone(stats_c["last_seen"])

    # 8. Specific Fix Tests: Graph Edge Node Integrity
    def test_20_graph_edge_node_consistency(self):
        """Every edge.source and edge.target must exist in nodes."""
        addr = "1ShadowX9947bc1qxy2kgdygjrsqtzq2n0yrf249"
        txs = self.demo_provider.get_address_transactions(addr)
        graph = self.analytics.build_transaction_graph(addr, txs, max_nodes=5)

        node_ids = {n["data"]["id"] for n in graph["nodes"]}
        for edge in graph["edges"]:
            self.assertIn(edge["data"]["source"], node_ids)
            self.assertIn(edge["data"]["target"], node_ids)
        self.assertIsInstance(graph["clustering"]["connected_clusters"], int)

    # 9. AI Behavioral Similarity Output Structure
    def test_21_ai_similarity_score_format(self):
        """AI score must express behavioral similarity without identity claims."""
        resp = self.client.get("/api/blockchain/address/1ShadowX9947bc1qxy2kgdygjrsqtzq2n0yrf249?demo=true")
        self.assertEqual(resp.status_code, 200)
        ai_data = resp.json().get("ai_integration", {})
        self.assertIn("wallet_behavior_score", ai_data)
        self.assertIn("interpretation", ai_data)
        self.assertIn("disclaimer", ai_data)
        self.assertIn("behavioral similarity", ai_data["disclaimer"].lower())


if __name__ == "__main__":
    unittest.main()
