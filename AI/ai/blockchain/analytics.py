"""
Blockchain Wallet Analytics & Graph Constructor
SIH26151: Dark Web Threat Actor De-anonymization

Performs safe, read-only analytical operations on normalized public Bitcoin transaction data:
- Comprehensive wallet metrics (in/out volumes, averages, medians, active days, frequencies)
- 8-Dimensional behavior vector aligned with Elliptic dataset feature extraction
- Flow analysis (Inbound, Outbound, Net Observable Flow)
- Safe transaction graph construction for Cytoscape.js
- Graph clustering & counterparty diversity
- Behavioral anomaly detection (bursts, volume spikes, dormancy gaps)
- Extended Forensic Risk Score calculation

Ethical & Safety Notice:
All relationships represent 'Observable Transaction Connections' or 'Potential Associations'.
Never attributes real-world identity or claims ownership.
"""

import math
import statistics
import time
from typing import Dict, Any, List, Optional, Tuple, Set
import numpy as np
import networkx as nx


class BlockchainAnalyticsEngine:
    """Calculates safe behavioral statistics, graphs, and anomaly indicators."""

    def __init__(self):
        pass

    def calculate_wallet_statistics(
        self,
        info: Dict[str, Any],
        txs: List[Dict[str, Any]],
        utxos: List[Dict[str, Any]],
        utxo_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculates comprehensive transaction statistics."""
        target_addr = info.get("address", "")
        total_tx = info.get("total_transactions", len(txs))

        inbound_txs = [t for t in txs if t.get("direction") == "INBOUND"]
        outbound_txs = [t for t in txs if t.get("direction") == "OUTBOUND"]

        # Transaction value distribution
        all_amounts = []
        for t in txs:
            if t.get("direction") == "INBOUND":
                all_amounts.append(t.get("output_value_btc", 0.0))
            elif t.get("direction") == "OUTBOUND":
                all_amounts.append(t.get("input_value_btc", 0.0))
            else:
                all_amounts.append(t.get("output_value_btc", 0.0))

        valid_amounts = [a for a in all_amounts if a > 0]
        avg_val = float(statistics.mean(valid_amounts)) if valid_amounts else 0.0
        med_val = float(statistics.median(valid_amounts)) if valid_amounts else 0.0
        max_val = float(max(valid_amounts)) if valid_amounts else 0.0
        min_val = float(min(valid_amounts)) if valid_amounts else 0.0

        # Activity dates and observed window
        timestamps = [t.get("timestamp") for t in txs if t.get("timestamp")]
        if timestamps:
            first_obs_ts = min(timestamps)
            last_obs_ts = max(timestamps)
            first_obs_iso = time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime(first_obs_ts))
            last_obs_iso = time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime(last_obs_ts))
            span_days = max(1, (last_obs_ts - first_obs_ts) // 86400)
            unique_days = len(set(time.strftime("%Y-%m-%d", time.gmtime(ts)) for ts in timestamps))
        else:
            first_obs_iso = None
            last_obs_iso = None
            span_days = 1
            unique_days = 0

        # Complete history verification
        # History is verified complete only if total_tx == 0 OR len(txs) >= total_tx
        is_history_complete = (total_tx == 0) or (len(txs) >= total_tx and total_tx > 0)

        observed_window = {
            "first_observed": first_obs_iso,
            "last_observed": last_obs_iso,
            "complete": is_history_complete
        }

        first_seen = first_obs_iso if is_history_complete else None
        last_seen = last_obs_iso if is_history_complete else None

        # Transaction frequency per week
        weeks = max(1.0, span_days / 7.0)
        tx_freq_per_week = total_tx / weeks

        # UTXO status handling
        if utxo_details:
            observable_utxos = utxo_details.get("observable_utxos")
            utxo_status = utxo_details.get("utxo_status", "AVAILABLE")
            utxo_note = utxo_details.get("utxo_note")
        else:
            observable_utxos = len(utxos)
            utxo_status = "AVAILABLE"
            utxo_note = None

        total_unspent_btc = round(float(info.get("total_unspent_btc", 0.0)), 8)

        return {
            "address": target_addr,
            "total_transactions": total_tx,
            "inbound_count": len(inbound_txs),
            "outbound_count": len(outbound_txs),
            "total_received_btc": round(float(info.get("total_received_btc", 0.0)), 8),
            "total_spent_btc": round(float(info.get("total_spent_btc", 0.0)), 8),
            "total_unspent_btc": total_unspent_btc,
            "observable_utxos": observable_utxos,
            "observable_utxo_count": observable_utxos,
            "utxo_status": utxo_status,
            "utxo_note": utxo_note,
            "average_transaction_value": round(avg_val, 6),
            "median_transaction_value": round(med_val, 6),
            "largest_transaction": round(max_val, 6),
            "smallest_transaction": round(min_val, 6),
            "active_days": unique_days,
            "operational_span_days": span_days,
            "transaction_frequency_per_week": round(tx_freq_per_week, 2),
            "first_seen": first_seen,
            "last_seen": last_seen,
            "observed_window": observed_window
        }

    def generate_behavior_profile(
        self,
        stats: Dict[str, Any],
        txs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extracts standardized behavior vector aligned with Elliptic dataset feature extraction:
        [tx_frequency, avg_tx_value, inbound_vol, outbound_vol, in_out_ratio, degree, burst_rate, churn_rate]
        """
        in_vol = stats.get("total_received_btc", 1.0)
        out_vol = stats.get("total_spent_btc", 1.0)
        ratio = in_vol / max(out_vol, 0.001)

        # Counterparties (inbound and outbound unique addresses)
        counterparties: Set[str] = set()
        for t in txs:
            for vin in t.get("inputs", []):
                addr = vin.get("address")
                if addr and addr != stats.get("address") and not addr.startswith("Coinbase"):
                    counterparties.add(addr)
            for vout in t.get("outputs", []):
                addr = vout.get("address")
                if addr and addr != stats.get("address") and not addr.startswith("OP_RETURN"):
                    counterparties.add(addr)

        degree = len(counterparties)

        # Burstiness: variance in inter-transaction intervals
        timestamps = sorted([t.get("timestamp") for t in txs if t.get("timestamp")])
        if len(timestamps) >= 3:
            deltas = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            mean_delta = statistics.mean(deltas)
            std_delta = statistics.stdev(deltas) if len(deltas) > 1 else 0.0
            # Coefficient of variation as burst metric
            burst_score = min(1.0, std_delta / (mean_delta + 1e-4))
        else:
            burst_score = 0.20

        # Normalized profile for AI comparison
        profile = {
            "transaction_frequency": round(min(1.0, stats.get("transaction_frequency_per_week", 1.0) / 20.0), 4),
            "average_value": round(min(1.0, math.log1p(stats.get("average_transaction_value", 0.0)) / 5.0), 4),
            "median_value": round(min(1.0, math.log1p(stats.get("median_transaction_value", 0.0)) / 5.0), 4),
            "inbound_ratio": round(min(1.0, ratio / (ratio + 1.0)), 4),
            "outbound_ratio": round(min(1.0, 1.0 / (ratio + 1.0)), 4),
            "active_days_ratio": round(min(1.0, stats.get("active_days", 1) / max(stats.get("operational_span_days", 1), 1)), 4),
            "counterparty_count": degree,
            "counterparty_diversity": round(min(1.0, degree / max(stats.get("total_transactions", 1) * 2, 1)), 4),
            "burst_activity": round(burst_score, 4)
        }

        # 8-D vector compatible with Elliptic ML comparator
        vector_8d = np.array([
            np.log1p(stats.get("transaction_frequency_per_week", 1.0)),
            np.log1p(stats.get("average_transaction_value", 0.5)),
            np.log1p(in_vol),
            np.log1p(out_vol),
            np.clip(ratio, 0.0, 10.0),
            np.log1p(float(degree)),
            np.clip(burst_score, 0.0, 1.0),
            np.clip(profile["counterparty_diversity"], 0.0, 1.0)
        ], dtype=float)

        return {
            "profile": profile,
            "vector_8d": vector_8d.tolist(),
            "counterparties": sorted(list(counterparties))[:20]
        }

    def calculate_flow_analysis(self, stats: Dict[str, Any], txs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates inbound, outbound, and net observable cryptocurrency flows."""
        in_btc = stats.get("total_received_btc", 0.0)
        out_btc = stats.get("total_spent_btc", 0.0)
        net_btc = in_btc - out_btc

        return {
            "inbound_btc": round(in_btc, 8),
            "outbound_btc": round(out_btc, 8),
            "net_observable_flow_btc": round(net_btc, 8),
            "inbound_transaction_count": stats.get("inbound_count", 0),
            "outbound_transaction_count": stats.get("outbound_count", 0),
            "flow_status": "NET_ACCUMULATION" if net_btc > 0 else ("NET_OUTFLOW" if net_btc < 0 else "BALANCED")
        }

    def build_transaction_graph(
        self,
        target_address: str,
        txs: List[Dict[str, Any]],
        max_nodes: int = 50
    ) -> Dict[str, Any]:
        """
        Constructs a Cytoscape.js compatible graph showing Target Address, Input/Output addresses,
        and transaction routing edges (SENT_TO, RECEIVED_FROM, INPUT_OF, OUTPUT_OF).
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        seen_nodes: Set[str] = set()

        # 1. Target Address Node
        target_id = f"addr_{target_address}"
        nodes.append({
            "data": {
                "id": target_id,
                "label": f"{target_address[:8]}...{target_address[-6:]}",
                "full_address": target_address,
                "type": "target_address",
                "category": "Target Address",
                "shape": "hexagon",
                "color": "#e05656",
                "bg_color": "#8b1e1e"
            },
            "classes": "target-address-node"
        })
        seen_nodes.add(target_id)

        for idx, tx in enumerate(txs[:12]):
            txid = tx.get("txid", f"tx_{idx}")
            tx_node_id = f"tx_{txid[:12]}"
            tx_val = tx.get("output_value_btc", 0.0)

            # Transaction Junction Node
            if tx_node_id not in seen_nodes and len(nodes) < max_nodes:
                nodes.append({
                    "data": {
                        "id": tx_node_id,
                        "label": f"TX: {txid[:6]}... ({tx_val:.3f} BTC)",
                        "full_txid": txid,
                        "type": "transaction",
                        "category": "Transaction Record",
                        "shape": "rectangle",
                        "color": "#f39c12",
                        "bg_color": "#7e5109",
                        "value_btc": tx_val,
                        "timestamp": tx.get("time_iso")
                    },
                    "classes": "tx-node"
                })
                seen_nodes.add(tx_node_id)

            # Process Inputs
            for vin in tx.get("inputs", [])[:2]:
                in_addr = vin.get("address", "")
                if not in_addr or in_addr.startswith("Coinbase"):
                    continue
                in_node_id = f"addr_{in_addr}"
                if in_node_id not in seen_nodes and len(nodes) < max_nodes:
                    nodes.append({
                        "data": {
                            "id": in_node_id,
                            "label": f"{in_addr[:6]}...{in_addr[-4:]}",
                            "full_address": in_addr,
                            "type": "input_address",
                            "category": "Input Address",
                            "shape": "ellipse",
                            "color": "#3498db",
                            "bg_color": "#1b4f72"
                        },
                        "classes": "input-address-node"
                    })
                    seen_nodes.add(in_node_id)

                # Edge: Input Address -> Transaction
                edges.append({
                    "data": {
                        "id": f"e_{in_node_id}_{tx_node_id}",
                        "source": in_node_id,
                        "target": tx_node_id,
                        "label": "INPUT_OF",
                        "relationship": "Observable Transaction Connection",
                        "style": "solid",
                        "color": "#3498db"
                    }
                })

            # Process Outputs
            for vout in tx.get("outputs", [])[:2]:
                out_addr = vout.get("address", "")
                if not out_addr or out_addr.startswith("OP_RETURN"):
                    continue
                out_node_id = f"addr_{out_addr}"
                if out_node_id not in seen_nodes and len(nodes) < max_nodes:
                    nodes.append({
                        "data": {
                            "id": out_node_id,
                            "label": f"{out_addr[:6]}...{out_addr[-4:]}",
                            "full_address": out_addr,
                            "type": "output_address",
                            "category": "Output Address",
                            "shape": "ellipse",
                            "color": "#2ecc71",
                            "bg_color": "#145a32"
                        },
                        "classes": "output-address-node"
                    })
                    seen_nodes.add(out_node_id)

                # Edge: Transaction -> Output Address
                edges.append({
                    "data": {
                        "id": f"e_{tx_node_id}_{out_node_id}",
                        "source": tx_node_id,
                        "target": out_node_id,
                        "label": "OUTPUT_OF",
                        "relationship": "Observable Transaction Connection",
                        "style": "solid",
                        "color": "#2ecc71"
                    }
                })

        # Validate that every edge's source and target strictly exist in nodes
        valid_node_ids = {n["data"]["id"] for n in nodes}
        validated_edges = [
            e for e in edges
            if e["data"]["source"] in valid_node_ids and e["data"]["target"] in valid_node_ids
        ]

        # Calculate connected components using NetworkX dynamically
        g = nx.Graph()
        for nid in valid_node_ids:
            g.add_node(nid)
        for e in validated_edges:
            g.add_edge(e["data"]["source"], e["data"]["target"])
        connected_clusters = nx.number_connected_components(g) if valid_node_ids else 0

        return {
            "nodes": nodes,
            "edges": validated_edges,
            "node_count": len(nodes),
            "edge_count": len(validated_edges),
            "clustering": {
                "method": "connected_components",
                "connected_clusters": connected_clusters,
                "label": "Transaction-connected cluster"
            }
        }

    def detect_behavioral_anomalies(
        self,
        stats: Dict[str, Any],
        txs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identifies observable transaction anomalies without criminal presumption."""
        anomalies: List[Dict[str, Any]] = []

        # 1. Unusually large transaction relative to average
        avg_val = stats.get("average_transaction_value", 0.0)
        max_val = stats.get("largest_transaction", 0.0)
        if avg_val > 0 and max_val > (avg_val * 4.0) and max_val > 1.0:
            anomalies.append({
                "anomaly_type": "Unusually Large Transaction Volume",
                "severity": "Medium",
                "anomaly_score": round(min(1.0, max_val / (avg_val * 5.0)), 2),
                "description": f"Maximum single transaction value ({max_val:.4f} BTC) is {max_val/avg_val:.1f}x higher than the observed average ({avg_val:.4f} BTC).",
                "supporting_features": ["largest_transaction", "average_transaction_value"]
            })

        # 2. Transaction Burst Activity
        freq = stats.get("transaction_frequency_per_week", 0.0)
        if freq > 15.0:
            anomalies.append({
                "anomaly_type": "High Transaction Velocity Burst",
                "severity": "High" if freq > 30 else "Medium",
                "anomaly_score": round(min(1.0, freq / 40.0), 2),
                "description": f"Elevated transaction frequency ({freq:.1f} tx/week) indicates rapid automated or batch processing.",
                "supporting_features": ["transaction_frequency_per_week"]
            })

        # 3. High Counterparty Fan-Out / Mixing Hub Pattern
        in_cnt = stats.get("inbound_count", 0)
        out_cnt = stats.get("outbound_count", 0)
        if (in_cnt >= 5 and out_cnt == 1) or (in_cnt == 1 and out_cnt >= 5):
            anomalies.append({
                "anomaly_type": "Asymmetric Fan-In / Fan-Out Flow",
                "severity": "Medium",
                "anomaly_score": 0.65,
                "description": "High asymmetry between inbound consolidation and outbound distribution counterparties.",
                "supporting_features": ["inbound_count", "outbound_count"]
            })

        return anomalies

    def calculate_forensic_risk_score(
        self,
        stats: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
        graph_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates explainable Forensic Risk Score (0..100) combining:
        - Transaction velocity & burst rate (30%)
        - Flow asymmetry & mixing structure (25%)
        - Counterparty connectivity degree (25%)
        - Behavioral anomaly severity (20%)
        """
        freq_comp = min(30.0, stats.get("transaction_frequency_per_week", 1.0) * 1.5)
        flow_comp = 15.0 if stats.get("inbound_count", 0) > 0 and stats.get("outbound_count", 0) > 0 else 5.0
        degree_comp = min(25.0, graph_stats.get("node_count", 2) * 1.5)
        anom_comp = min(20.0, len(anomalies) * 7.0)

        total_score = round(freq_comp + flow_comp + degree_comp + anom_comp, 1)
        total_score = float(np.clip(total_score, 5.0, 95.0))

        risk_level = "ELEVATED" if total_score >= 65 else ("MODERATE" if total_score >= 35 else "LOW")

        return {
            "forensic_risk_score": total_score,
            "risk_level": risk_level,
            "components": {
                "transaction_velocity": round(freq_comp, 1),
                "flow_asymmetry": round(flow_comp, 1),
                "graph_connectivity": round(degree_comp, 1),
                "behavioral_anomalies": round(anom_comp, 1)
            },
            "disclaimer": "Forensic Risk Score is an analytical heuristic for prioritization, not confirmation of illicit activity."
        }
