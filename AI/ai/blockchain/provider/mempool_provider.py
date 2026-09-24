"""
Mempool.space Public Bitcoin Blockchain API Provider
SIH26151: Dark Web Threat Actor De-anonymization

Implements read-only queries against Mempool.space REST APIs:
- GET /api/address/:address
- GET /api/address/:address/txs
- GET /api/address/:address/txs/chain[?after_txid=...]
- GET /api/address/:address/txs/mempool
- GET /api/address/:address/utxo
- GET /api/v1/validate-address/:address
- GET /api/tx/:txid

Safety & Reliability:
- Strictly read-only GET requests.
- Exponential backoff retries and rate limit (429) backoff.
- Graceful handling of large UTXO address endpoints (400 >500 UTXOs).
"""

import os
import time
import requests
from typing import Dict, Any, List, Optional
from ai.blockchain.provider.base_provider import BlockchainProvider

SATOSHIS_PER_BTC = 100_000_000.0


class MempoolBlockchainProvider(BlockchainProvider):
    """Mempool.space REST API Client for public Bitcoin blockchain exploration."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: int = 10,
        max_retries: int = 2
    ):
        raw_url = base_url or os.getenv("BLOCKCHAIN_API_URL") or "https://mempool.space/api"
        self.base_url = raw_url.rstrip("/")
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "SIH26151-DarkWebThreatIntel/1.0 (Research Demo; Read-Only)"
        })

    @property
    def provider_name(self) -> str:
        return "Mempool.space"

    @property
    def network_name(self) -> str:
        return "bitcoin-mainnet"

    def _http_get(self, endpoint: str) -> Any:
        """Executes GET request against Mempool API with exponential backoff retries."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        last_err = None

        for attempt in range(self.max_retries + 1):
            try:
                resp = self._session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except Exception:
                        return resp.text
                elif resp.status_code == 404:
                    return None
                elif resp.status_code == 400 and ("utxo" in endpoint or "unspent" in resp.text.lower()):
                    # Mempool returns HTTP 400 when an address has >500 UTXOs
                    return {"_utxo_limit_exceeded": True, "_error_msg": resp.text.strip()}
                elif resp.status_code == 429:
                    # Rate limit backoff
                    time.sleep(1.0 * (2 ** attempt))
                    continue
                else:
                    last_err = f"Provider returned HTTP {resp.status_code}: {resp.text[:120]}"
            except requests.exceptions.Timeout:
                last_err = f"Request to {url} timed out after {self.timeout}s."
            except requests.exceptions.RequestException as e:
                last_err = f"Network connection error: {str(e)}"

            time.sleep(0.5 * (2 ** attempt))

        raise RuntimeError(f"Blockchain API error [{endpoint}]: {last_err}")

    def validate_address_api(self, address: str) -> Dict[str, Any]:
        """Calls /api/v1/validate-address/:address if available."""
        v1_url = self.base_url.replace("/api", "") + f"/api/v1/validate-address/{address}"
        try:
            resp = self._session.get(v1_url, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {"isvalid": True, "address": address}

    def get_address_info(self, address: str) -> Dict[str, Any]:
        """
        Retrieves address balance, transaction counts, and confirmation stats.
        GET /api/address/:address
        """
        data = self._http_get(f"address/{address}")
        if data is None:
            # Address never had transactions on chain
            return {
                "address": address,
                "network": self.network_name,
                "total_transactions": 0,
                "confirmed_transactions": 0,
                "unconfirmed_transactions": 0,
                "total_received_btc": 0.0,
                "total_spent_btc": 0.0,
                "total_unspent_btc": 0.0,
                "source": self.provider_name
            }

        chain_stats = data.get("chain_stats", {})
        mempool_stats = data.get("mempool_stats", {})

        funded_sats = chain_stats.get("funded_txo_sum", 0) + mempool_stats.get("funded_txo_sum", 0)
        spent_sats = chain_stats.get("spent_txo_sum", 0) + mempool_stats.get("spent_txo_sum", 0)
        unspent_sats = funded_sats - spent_sats
        tx_count = chain_stats.get("tx_count", 0) + mempool_stats.get("tx_count", 0)

        return {
            "address": address,
            "network": self.network_name,
            "total_transactions": tx_count,
            "confirmed_transactions": chain_stats.get("tx_count", 0),
            "unconfirmed_transactions": mempool_stats.get("tx_count", 0),
            "total_received_btc": round(funded_sats / SATOSHIS_PER_BTC, 8),
            "total_spent_btc": round(spent_sats / SATOSHIS_PER_BTC, 8),
            "total_unspent_btc": round(max(0.0, unspent_sats / SATOSHIS_PER_BTC), 8),
            "source": self.provider_name
        }

    def get_address_transactions(self, address: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Retrieves recent transactions for address and normalizes them.
        GET /api/address/:address/txs
        """
        raw_txs = self._http_get(f"address/{address}/txs")
        if not isinstance(raw_txs, list):
            raw_txs = []

        txs = []
        for tx in raw_txs[:limit]:
            if isinstance(tx, dict):
                txs.append(self._normalize_mempool_tx(tx, target_address=address))
        return txs

    def get_address_transactions_chain(self, address: str, after_txid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves confirmed transactions for address with pagination.
        GET /api/address/:address/txs/chain[?after_txid=...]
        """
        endpoint = f"address/{address}/txs/chain"
        if after_txid:
            endpoint += f"?after_txid={after_txid}"
        raw_txs = self._http_get(endpoint)
        if not isinstance(raw_txs, list):
            return []
        return [self._normalize_mempool_tx(tx, target_address=address) for tx in raw_txs if isinstance(tx, dict)]

    def get_address_transactions_mempool(self, address: str) -> List[Dict[str, Any]]:
        """
        Retrieves unconfirmed transactions in mempool for address.
        GET /api/address/:address/txs/mempool
        """
        raw_txs = self._http_get(f"address/{address}/txs/mempool")
        if not isinstance(raw_txs, list):
            return []
        return [self._normalize_mempool_tx(tx, target_address=address) for tx in raw_txs if isinstance(tx, dict)]

    def get_transaction(self, txid: str) -> Dict[str, Any]:
        """
        Retrieves single transaction details.
        GET /api/tx/:txid
        """
        raw_tx = self._http_get(f"tx/{txid}")
        if not raw_tx or not isinstance(raw_tx, dict):
            raise ValueError(f"Transaction hash '{txid}' not found on Bitcoin mainnet via {self.provider_name}.")
        return self._normalize_mempool_tx(raw_tx)

    def get_address_utxos_detailed(self, address: str) -> Dict[str, Any]:
        """
        Retrieves unspent transaction outputs (UTXOs) with provider limit detection.
        GET /api/address/:address/utxo
        """
        raw_utxos = self._http_get(f"address/{address}/utxo")
        if isinstance(raw_utxos, dict) and raw_utxos.get("_utxo_limit_exceeded"):
            return {
                "utxos": [],
                "observable_utxos": None,
                "utxo_status": "UNAVAILABLE_PROVIDER_LIMIT",
                "utxo_note": "Complete UTXO enumeration unavailable because the provider limits this address to 500 UTXOs."
            }

        if not isinstance(raw_utxos, list):
            return {
                "utxos": [],
                "observable_utxos": 0,
                "utxo_status": "AVAILABLE",
                "utxo_note": None
            }

        utxos = []
        for u in raw_utxos:
            if isinstance(u, dict):
                status = u.get("status", {})
                val_sats = u.get("value", 0)
                utxos.append({
                    "txid": u.get("txid"),
                    "vout": u.get("vout"),
                    "value_btc": round(val_sats / SATOSHIS_PER_BTC, 8),
                    "confirmed": status.get("confirmed", False),
                    "block_height": status.get("block_height")
                })

        return {
            "utxos": utxos,
            "observable_utxos": len(utxos),
            "utxo_status": "AVAILABLE",
            "utxo_note": None
        }

    def get_address_utxos(self, address: str) -> List[Dict[str, Any]]:
        """
        Retrieves unspent transaction outputs (UTXOs) list.
        """
        detailed = self.get_address_utxos_detailed(address)
        return detailed["utxos"]

    def _normalize_mempool_tx(self, tx: Dict[str, Any], target_address: Optional[str] = None) -> Dict[str, Any]:
        """Normalizes a Mempool.space transaction payload into standard unified schema."""
        txid = tx.get("txid", "")
        status = tx.get("status", {})
        confirmed = status.get("confirmed", False)
        block_height = status.get("block_height")
        block_time = status.get("block_time", int(time.time()))
        fee_sats = tx.get("fee", 0)

        # Parse inputs
        inputs = []
        total_in_sats = 0
        is_inbound = False
        is_outbound = False

        for vin in tx.get("vin", []):
            prevout = vin.get("prevout") or {}
            in_addr = prevout.get("scriptpubkey_address")
            in_val_sats = prevout.get("value", 0)
            total_in_sats += in_val_sats
            inputs.append({
                "address": in_addr or "Coinbase / Unknown",
                "value_btc": round(in_val_sats / SATOSHIS_PER_BTC, 8),
                "txid": vin.get("txid"),
                "vout": vin.get("vout")
            })
            if target_address and in_addr == target_address:
                is_outbound = True

        # Parse outputs
        outputs = []
        total_out_sats = 0
        for vout in tx.get("vout", []):
            out_addr = vout.get("scriptpubkey_address")
            out_val_sats = vout.get("value", 0)
            total_out_sats += out_val_sats
            outputs.append({
                "address": out_addr or "OP_RETURN / Unparsed",
                "value_btc": round(out_val_sats / SATOSHIS_PER_BTC, 8)
            })
            if target_address and out_addr == target_address:
                is_inbound = True

        # Determine flow direction relative to target address
        if is_inbound and not is_outbound:
            direction = "INBOUND"
        elif is_outbound and not is_inbound:
            direction = "OUTBOUND"
        elif is_inbound and is_outbound:
            direction = "SELF_TRANSFER / CHANGE"
        else:
            direction = "EXTERNAL"

        return {
            "txid": txid,
            "block_height": block_height,
            "timestamp": block_time,
            "time_iso": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime(block_time)),
            "fee_btc": round(fee_sats / SATOSHIS_PER_BTC, 8),
            "inputs": inputs,
            "outputs": outputs,
            "input_value_btc": round(total_in_sats / SATOSHIS_PER_BTC, 8),
            "output_value_btc": round(total_out_sats / SATOSHIS_PER_BTC, 8),
            "confirmed": confirmed,
            "direction": direction,
            "source": self.provider_name
        }

    def is_healthy(self) -> bool:
        """Verifies connection to Mempool.space API."""
        try:
            resp = self._session.get(f"{self.base_url}/blocks/tip/height", timeout=4)
            return resp.status_code == 200
        except Exception:
            return False
