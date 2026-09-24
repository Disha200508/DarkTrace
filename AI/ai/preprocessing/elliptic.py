"""
Elliptic Bitcoin Dataset Preprocessor & Adapter
SIH26151: Dark Web Threat Actor De-anonymization

Loads and processes the Elliptic Bitcoin dataset for transaction and graph behavior modeling.
Calculates wallet behavior distributions, graph degree metrics, transaction burst features,
and adapts behavioral profiles for synthetic investigation wallets.

Ethical / Safety Note:
Elliptic labels are used strictly for behavioral and structural graph modeling.
No real-world identities or private individuals are deanonymized.
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple


class EllipticPreprocessor:
    """Loads and transforms Elliptic Bitcoin dataset into graph & behavioral representations."""

    def __init__(self, data_dir: str = "archive/elliptic_bitcoin_dataset"):
        self.data_dir = data_dir
        self.classes_path = os.path.join(data_dir, "elliptic_txs_classes.csv")
        self.edges_path = os.path.join(data_dir, "elliptic_txs_edgelist.csv")
        self.features_path = os.path.join(data_dir, "elliptic_txs_features.csv")

    def check_dataset_exists(self) -> bool:
        """Verifies dataset files exist."""
        return (
            os.path.exists(self.classes_path) and
            os.path.exists(self.edges_path) and
            os.path.exists(self.features_path)
        )

    def load_summary_sample(self, sample_size: int = 10000) -> Dict[str, Any]:
        """
        Loads classes and edge graph distributions.
        Returns aggregated behavioral distributions across licit (class 2) vs illicit (class 1).
        """
        if not self.check_dataset_exists():
            return {"status": "unavailable", "records": 0}

        # Load classes
        df_classes = pd.read_csv(self.classes_path)
        # Load sample edges
        df_edges = pd.read_csv(self.edges_path, nrows=sample_size * 2)

        # Compute graph degrees
        in_degrees = df_edges["txId2"].value_counts().to_dict()
        out_degrees = df_edges["txId1"].value_counts().to_dict()

        # Merge with sample classes
        labeled_classes = df_classes[df_classes["class"] != "unknown"].copy()
        sample_labeled = labeled_classes.sample(min(sample_size, len(labeled_classes)), random_state=42)

        sample_labeled["in_degree"] = sample_labeled["txId"].map(in_degrees).fillna(0)
        sample_labeled["out_degree"] = sample_labeled["txId"].map(out_degrees).fillna(0)
        sample_labeled["total_degree"] = sample_labeled["in_degree"] + sample_labeled["out_degree"]

        illicit_stats = sample_labeled[sample_labeled["class"] == "1"]
        licit_stats = sample_labeled[sample_labeled["class"] == "2"]

        return {
            "total_transactions": len(df_classes),
            "labeled_count": len(labeled_classes),
            "illicit_count": len(df_classes[df_classes["class"] == "1"]),
            "licit_count": len(df_classes[df_classes["class"] == "2"]),
            "illicit_avg_in_degree": float(illicit_stats["in_degree"].mean()) if not illicit_stats.empty else 0.0,
            "illicit_avg_out_degree": float(illicit_stats["out_degree"].mean()) if not illicit_stats.empty else 0.0,
            "licit_avg_in_degree": float(licit_stats["in_degree"].mean()) if not licit_stats.empty else 0.0,
            "licit_avg_out_degree": float(licit_stats["out_degree"].mean()) if not licit_stats.empty else 0.0,
        }

    def extract_wallet_features(self, wallet_profile: Dict[str, Any]) -> np.ndarray:
        """
        Extracts standardized 8-dimensional behavioral vector from wallet activity:
        [tx_frequency, avg_tx_value, inbound_vol, outbound_vol, in_out_ratio, degree, burst_rate, churn_rate]
        """
        tx_freq = float(wallet_profile.get("tx_frequency", 1.0))
        avg_val = float(wallet_profile.get("avg_tx_value", 0.5))
        in_vol = float(wallet_profile.get("inbound_volume", 1.0))
        out_vol = float(wallet_profile.get("outbound_volume", 1.0))
        ratio = float(wallet_profile.get("in_out_ratio", in_vol / max(out_vol, 0.001)))
        degree = float(wallet_profile.get("connected_nodes", 2.0))
        burst = float(wallet_profile.get("burst_rate", 0.0))
        churn = float(wallet_profile.get("address_churn", 0.0))

        vec = np.array([
            np.log1p(max(0.0, tx_freq)),
            np.log1p(max(0.0, avg_val)),
            np.log1p(max(0.0, in_vol)),
            np.log1p(max(0.0, out_vol)),
            np.clip(ratio, 0.0, 10.0),
            np.log1p(max(0.0, degree)),
            np.clip(burst, 0.0, 1.0),
            np.clip(churn, 0.0, 1.0)
        ], dtype=float)

        return vec
