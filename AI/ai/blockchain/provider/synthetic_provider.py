"""
Offline Synthetic Demo Blockchain Provider
SIH26151: Dark Web Threat Actor De-anonymization

Provides deterministic, synthetic Bitcoin blockchain responses for offline demonstrations,
unit testing, and presentations without requiring live internet/API connectivity.
"""

import hashlib
import time
from typing import Dict, Any, List, Optional
from ai.blockchain.provider.base_provider import BlockchainProvider


class SyntheticBlockchainProvider(BlockchainProvider):
    """Deterministic synthetic blockchain provider for offline presentation/testing."""

    def __init__(self):
        pass

    @property
    def provider_name(self) -> str:
        return "Synthetic Demonstration Provider (Offline Mock)"

    @property
    def network_name(self) -> str:
        return "bitcoin-mainnet (synthetic demo)"

    def _hash_seed(self, text: str) -> int:
        """Returns integer hash seed for deterministic mock data generation."""
        return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)

    def get_address_info(self, address: str) -> Dict[str, Any]:
        """Generates deterministic address overview."""
        seed = self._hash_seed(address)
        tx_count = 5 + (seed % 45)
        total_received = round(1.5 + (seed % 100) * 0.42, 6)
        total_spent = round(total_received * (0.60 + (seed % 35) * 0.01), 6)
        unspent = round(max(0.0, total_received - total_spent), 6)

        return {
            "address": address,
            "network": self.network_name,
            "total_transactions": tx_count,
            "confirmed_transactions": tx_count,
            "unconfirmed_transactions": 0,
            "total_received_btc": total_received,
            "total_spent_btc": total_spent,
            "total_unspent_btc": unspent,
            "source": self.provider_name
        }

    def get_address_transactions(self, address: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Generates deterministic transaction history."""
        seed = self._hash_seed(address)
        tx_count = min(limit, 6 + (seed % 12))
        base_time = int(time.time()) - (tx_count * 86400 * 3)

        txs = []
        counterparties = [
            "1SyntheticInflowExchange8839210bc",
            "bc1qMixerDepositPool88492019381023",
            "1InfraHostingProxyProvider8829102",
            "bc1qOffRampLiquidationOTC99482012"
        ]

        for i in range(tx_count):
            tx_time = base_time + (i * 86400 * 3) + ((seed + i) % 1800)
            tx_seed = (seed * 31 + i * 17) & 0xFFFFFFFF
            val = round(0.15 + (tx_seed % 200) * 0.025, 6)
            is_inbound = (i % 2 == 0)
            fee = 0.000045 + (i * 0.000005)
            tx_hash = hashlib.sha256(f"{address}_{i}_{tx_seed}".encode()).hexdigest()

            cp = counterparties[i % len(counterparties)]
            if is_inbound:
                inputs = [{"address": cp, "value_btc": val + fee, "txid": tx_hash, "vout": 0}]
                outputs = [{"address": address, "value_btc": val}]
                direction = "INBOUND"
            else:
                inputs = [{"address": address, "value_btc": val + fee, "txid": tx_hash, "vout": 0}]
                outputs = [{"address": cp, "value_btc": val}]
                direction = "OUTBOUND"

            txs.append({
                "txid": tx_hash,
                "block_height": 800000 + i * 120,
                "timestamp": tx_time,
                "time_iso": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime(tx_time)),
                "fee_btc": fee,
                "inputs": inputs,
                "outputs": outputs,
                "input_value_btc": val + fee,
                "output_value_btc": val,
                "confirmed": True,
                "direction": direction,
                "source": self.provider_name
            })

        return txs

    def get_transaction(self, txid: str) -> Dict[str, Any]:
        """Generates mock single transaction details."""
        seed = self._hash_seed(txid)
        val = round(0.5 + (seed % 50) * 0.1, 4)
        return {
            "txid": txid,
            "block_height": 810000 + (seed % 5000),
            "timestamp": int(time.time()) - 86400 * 5,
            "time_iso": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime(time.time() - 86400 * 5)),
            "fee_btc": 0.00005,
            "inputs": [{"address": "1SampleSyntheticSender88392", "value_btc": val + 0.00005}],
            "outputs": [{"address": "1SampleSyntheticReceiver88392", "value_btc": val}],
            "input_value_btc": val + 0.00005,
            "output_value_btc": val,
            "confirmed": True,
            "direction": "EXTERNAL",
            "source": self.provider_name
        }

    def get_address_utxos(self, address: str) -> List[Dict[str, Any]]:
        """Generates deterministic mock UTXOs."""
        seed = self._hash_seed(address)
        utxo_count = 1 + (seed % 3)
        utxos = []
        for i in range(utxo_count):
            utxos.append({
                "txid": hashlib.sha256(f"{address}_utxo_{i}".encode()).hexdigest(),
                "vout": i,
                "value_btc": round(0.25 + (seed % 20) * 0.05, 4),
                "confirmed": True,
                "block_height": 820000 + i * 10
            })
        return utxos

    def is_healthy(self) -> bool:
        return True


# Backward-compatible alias
DemoBlockchainProvider = SyntheticBlockchainProvider
