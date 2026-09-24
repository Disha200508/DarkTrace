"""
Esplora Provider Backward Compatibility Module
SIH26151: Dark Web Threat Actor De-anonymization
"""

from ai.blockchain.provider.mempool_provider import MempoolBlockchainProvider

class EsploraProvider(MempoolBlockchainProvider):
    """EsploraProvider aliased to MempoolBlockchainProvider."""
    pass

__all__ = ["EsploraProvider", "MempoolBlockchainProvider"]
