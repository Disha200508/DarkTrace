"""
Bitcoin Address and Transaction Hash Validation
SIH26151: Dark Web Threat Actor De-anonymization

Validates Bitcoin addresses (Legacy, P2SH, Bech32, Bech32m Taproot)
and transaction hash identifiers before any network requests.
"""

import re
from typing import Tuple, Optional


# Base58 character set (standard 26-35 chars, with allowance for synthetic demo identifiers up to 50 chars)
BASE58_REGEX = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{26,35}$")
SYNTHETIC_ADDR_REGEX = re.compile(r"^[13][a-zA-Z0-9]{20,50}$")

# Bech32 / Bech32m character set
BECH32_REGEX = re.compile(r"^bc1[02-9ac-hj-np-z]{11,87}$", re.IGNORECASE)
SYNTHETIC_BECH32_REGEX = re.compile(r"^bc1[a-zA-Z0-9]{11,87}$", re.IGNORECASE)

# 64-character Hexadecimal Transaction Hash
TXID_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")


def validate_bitcoin_address(address: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates a Bitcoin address format.
    Returns: (is_valid, address_type, error_message)

    Supported address types:
    - Legacy (P2PKH): Starts with '1'
    - Nested SegWit / Script (P2SH): Starts with '3'
    - Native SegWit (Bech32): Starts with 'bc1q'
    - Taproot (Bech32m): Starts with 'bc1p'
    - Synthetic Demo Addresses: (1... or bc1... demo identifiers)
    """
    if not address or not isinstance(address, str):
        return False, None, "Invalid Bitcoin address: Input is empty or not a string."

    clean_addr = address.strip()

    # 1. Native SegWit & Taproot (Bech32 / Bech32m / Synthetic Bech32)
    if clean_addr.lower().startswith("bc1"):
        if BECH32_REGEX.match(clean_addr) or SYNTHETIC_BECH32_REGEX.match(clean_addr):
            lower = clean_addr.lower()
            if lower.startswith("bc1p"):
                return True, "Taproot (P2TR / Bech32m)", None
            elif lower.startswith("bc1q"):
                return True, "Native SegWit (P2WPKH/P2WSH / Bech32)", None
            else:
                return True, "SegWit (Bech32)", None
        return False, None, "Invalid Bitcoin address: Malformed Bech32/Bech32m format."

    # 2. Legacy P2PKH (Starts with '1')
    if clean_addr.startswith("1"):
        if BASE58_REGEX.match(clean_addr) or SYNTHETIC_ADDR_REGEX.match(clean_addr):
            return True, "Legacy (P2PKH / Base58)", None
        return False, None, "Invalid Bitcoin address: Malformed Legacy (1...) format."

    # 3. P2SH (Starts with '3')
    if clean_addr.startswith("3"):
        if BASE58_REGEX.match(clean_addr) or SYNTHETIC_ADDR_REGEX.match(clean_addr):
            return True, "Script / Nested SegWit (P2SH / Base58)", None
        return False, None, "Invalid Bitcoin address: Malformed P2SH (3...) format."

    # 4. Testnet / Regtest prefixes (informative error)
    if clean_addr.startswith(("m", "n", "2", "tb1")):
        return False, None, "Invalid Bitcoin address: Testnet addresses are not supported in mainnet analysis."

    return False, None, "Invalid Bitcoin address: Unrecognized Bitcoin address format."


def validate_transaction_hash(txid: str) -> Tuple[bool, Optional[str]]:
    """
    Validates a 64-character hexadecimal transaction ID hash.
    Returns: (is_valid, error_message)
    """
    if not txid or not isinstance(txid, str):
        return False, "Invalid transaction hash: Input is empty or not a string."

    clean_txid = txid.strip()
    if TXID_REGEX.match(clean_txid):
        return True, None

    return False, "Invalid transaction hash: Must be a 64-character hexadecimal string."
