"""
Synthetic Investigation Data Adapter
SIH26151: Dark Web Threat Actor De-anonymization

Provides synthetic, anonymized investigation records for threat actor profiling,
migration benchmarking, and multi-signal fusion testing.

Ethical & Safety Notice:
All data generated or contained here is 100% synthetic research demonstration data.
No real-world persons, private wallets, or actual systems are depicted.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class SyntheticInvestigationAdapter:
    """Manages synthetic threat actor persona dossiers for correlation and testing."""

    def __init__(self):
        self.personas: Dict[str, Dict[str, Any]] = self._init_synthetic_personas()

    def _init_synthetic_personas(self) -> Dict[str, Dict[str, Any]]:
        """Initializes a benchmark suite of synthetic threat personas."""
        return {
            "ShadowX": {
                "id": "ACTOR-001",
                "name": "ShadowX",
                "alias": "Shadow_Original",
                "threat_category": "Data Broker / Initial Access",
                "forums": ["Dread", "BreachForums", "XSS_Mirror"],
                "active_period": {"start": "2023-01-10", "end": "2023-11-15"},
                "posts": [
                    "WTS fresh enterprise SQL dump and internal DB schema. Payment strictly via escrow. No lowball offers.",
                    "Releasing new python stealer source with custom obf. Contact me via Session or PGP below.",
                    "Database breach updated with 450k credential records. DM for sample hash verification."
                ],
                "diurnal_hours": [0, 1, 2, 3, 21, 22, 23],  # Active late UTC night
                "active_days": [0, 1, 2, 3, 4],             # Weekday heavy
                "ttps": ["T1059", "T1190", "T1071", "T1566"],
                "pgp_fingerprint": "4A8F 90B2 12C3 D4E5 F6A7 B8C9 0123 4567 89AB CDEF",
                "pgp_key_id": "89ABCDEF",
                "pgp_created": "2022-12-01",
                "wallets": [
                    {
                        "address": "1ShadowX9947bc1qxy2kgdygjrsqtzq2n0yrf249",
                        "tx_frequency": 14.5,
                        "avg_tx_value": 2.4,
                        "inbound_volume": 35.2,
                        "outbound_volume": 34.8,
                        "connected_nodes": 8,
                        "burst_rate": 0.35,
                        "address_churn": 0.20
                    }
                ],
                "infrastructure": {
                    "domains": ["shadow-drop[.]is", "sx-payload-cdn[.]net"],
                    "asns": ["AS49453", "AS200052"],
                    "certificate_fingerprint": "SHA256:E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
                    "cert_issuer": "Let's Encrypt / Synthetic Test CA",
                    "churn_score": 0.25
                }
            },

            "Shadow_X2026": {
                "id": "ACTOR-002",
                "name": "Shadow_X2026",
                "alias": "Shadow_V2",
                "threat_category": "Data Broker / Initial Access",
                "forums": ["Dread", "Exploit_Synthetic", "DarkNet_Army"],
                "active_period": {"start": "2024-01-05", "end": "2024-09-20"},
                "posts": [
                    "WTS updated corporate DB dump with verified schema. Payment strictly in BTC via trusted escrow.",
                    "Updated python loader with advanced memory injection. DM on session with PGP.",
                    "Fresh breach dataset verified. Contact with PGP for proof of work."
                ],
                "diurnal_hours": [0, 1, 2, 3, 22, 23],      # High overlap with ShadowX
                "active_days": [0, 1, 2, 3, 4],
                "ttps": ["T1059", "T1190", "T1071"],        # Strong TTP overlap
                "pgp_fingerprint": "4A8F 90B2 12C3 D4E5 F6A7 B8C9 0123 4567 89AB CDEF",  # Exact key reuse
                "pgp_key_id": "89ABCDEF",
                "pgp_created": "2022-12-01",
                "wallets": [
                    {
                        "address": "1ShadowXNew2026bc1qxy2kgdygjrsqtzq2n0yrf250",
                        "tx_frequency": 13.8,
                        "avg_tx_value": 2.2,
                        "inbound_volume": 31.0,
                        "outbound_volume": 30.5,
                        "connected_nodes": 7,
                        "burst_rate": 0.32,
                        "address_churn": 0.22
                    }
                ],
                "infrastructure": {
                    "domains": ["shadow-drop-v2[.]is", "sx-payload-cdn2[.]net"],
                    "asns": ["AS49453"],
                    "certificate_fingerprint": "SHA256:E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
                    "cert_issuer": "Let's Encrypt / Synthetic Test CA",
                    "churn_score": 0.28
                }
            },

            "DarkVortex": {
                "id": "ACTOR-003",
                "name": "DarkVortex",
                "alias": "DV_Ransom",
                "threat_category": "Ransomware Operator",
                "forums": ["RansomHub_Mirror", "DarkForums"],
                "active_period": {"start": "2023-06-01", "end": "2024-04-10"},
                "posts": [
                    "All files have been encrypted using military grade AES-256 and RSA-4096. Contact negotiation desk.",
                    "Company network compromised via active directory persistence. Data exfiltration completed.",
                    "Pay ransom within 72 hours or all confidential archives will be published."
                ],
                "diurnal_hours": [8, 9, 10, 11, 12, 13, 14],  # Daytime UTC (disjoint from ShadowX)
                "active_days": [1, 2, 3, 4, 5, 6],
                "ttps": ["T1486", "T1053", "T1021", "T1003"],
                "pgp_fingerprint": "7C11 34E8 99A0 11B2 C3D4 E5F6 7890 1234 5678 9012",
                "pgp_key_id": "56789012",
                "pgp_created": "2023-05-15",
                "wallets": [
                    {
                        "address": "bc1qDarkVortexRansomPool9993820129381023",
                        "tx_frequency": 3.2,
                        "avg_tx_value": 45.0,
                        "inbound_volume": 180.0,
                        "outbound_volume": 178.5,
                        "connected_nodes": 22,
                        "burst_rate": 0.85,
                        "address_churn": 0.70
                    }
                ],
                "infrastructure": {
                    "domains": ["vortex-leak-portal[.]onion", "dv-decrypt-support[.]top"],
                    "asns": ["AS13335", "AS9009"],
                    "certificate_fingerprint": "SHA256:AA11BB22CC33DD44EE55FF660011223344556677889900AABBCCDDEEFF001122",
                    "cert_issuer": "DV Self-Signed Cert",
                    "churn_score": 0.80
                }
            },

            "GhostOperator": {
                "id": "ACTOR-004",
                "name": "GhostOperator",
                "alias": "PhantomLead",
                "threat_category": "Advanced Persistent Cyber Espionage",
                "forums": ["Underground_Sec"],
                "active_period": {"start": "2022-08-01", "end": "2024-02-15"},
                "posts": [
                    "Spearphishing targeting energy sector ICS SCADA systems with macro-enabled documents.",
                    "Deploying custom DLL side-loading with memory evasion to bypass EDR agents.",
                    "Exfiltrating telemetry data via encrypted DNS tunneling protocols."
                ],
                "diurnal_hours": [6, 7, 8, 9, 10, 11],
                "active_days": [0, 1, 2, 3, 4],
                "ttps": ["T1566", "T1055", "T1071", "T1068"],
                "pgp_fingerprint": "B552 1199 4433 2211 00AA BBCC DDEE FF11 2233 4455",
                "pgp_key_id": "22334455",
                "pgp_created": "2022-07-20",
                "wallets": [],  # Missing wallet data (test coverage handling)
                "infrastructure": {
                    "domains": ["ghost-c2-relay[.]biz", "update-telemetry-sync[.]org"],
                    "asns": ["AS15169"],
                    "certificate_fingerprint": "SHA256:77889900112233445566AABBCCDDEEFF77889900112233445566AABBCCDDEEFF",
                    "cert_issuer": "DigiCert Synthetic",
                    "churn_score": 0.15
                }
            }
        }

    def get_persona(self, persona_id_or_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a persona by exact name or ID."""
        for name, data in self.personas.items():
            if name.lower() == persona_id_or_name.lower() or data.get("id").lower() == persona_id_or_name.lower():
                return data
        return None

    def list_personas(self) -> List[Dict[str, Any]]:
        """Lists all registered synthetic personas."""
        return list(self.personas.values())
