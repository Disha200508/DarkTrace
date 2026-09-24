"""
Abstract Blockchain Provider Interface
SIH26151: Dark Web Threat Actor De-anonymization

Defines provider-agnostic interface for read-only public Bitcoin blockchain lookups.
All network providers (Mempool, Esplora, Demo) implement this contract.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BlockchainProvider(ABC):
    """Abstract base class for read-only Bitcoin blockchain providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the blockchain data provider."""
        pass

    @property
    @abstractmethod
    def network_name(self) -> str:
        """Network identifier (e.g., 'bitcoin-mainnet')."""
        pass

    @abstractmethod
    def get_address_info(self, address: str) -> Dict[str, Any]:
        """
        Retrieves address balance, transaction counts, and confirmation stats.
        """
        pass

    @abstractmethod
    def get_address_transactions(self, address: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Retrieves recent transactions involving the specified address.
        """
        pass

    @abstractmethod
    def get_transaction(self, txid: str) -> Dict[str, Any]:
        """
        Retrieves transaction details (inputs, outputs, fee, confirmation status).
        """
        pass

    @abstractmethod
    def get_address_utxos(self, address: str) -> List[Dict[str, Any]]:
        """
        Retrieves currently unspent transaction outputs (UTXOs) for the address.
        """
        pass

    def get_address_utxos_detailed(self, address: str) -> Dict[str, Any]:
        """
        Retrieves UTXOs along with provider status and enumeration limits.
        """
        utxos = self.get_address_utxos(address)
        return {
            "utxos": utxos,
            "observable_utxos": len(utxos),
            "utxo_status": "AVAILABLE",
            "utxo_note": None
        }

    @abstractmethod
    def is_healthy(self) -> bool:
        """Checks if provider endpoint is reachable and operational."""
        pass
