"""
Threat Actor & Wallet Correlation Graph Generator
SIH26151: Dark Web Threat Actor De-anonymization

Generates Cytoscape.js compatible graph topology (nodes and edges) for:
- Threat Actor Personas (e.g., ShadowX, Phant0m_Reaper, NullByte_VIP, Shadow_X2026)
- Darknet Handles & Forum Aliases (e.g., @x_shadow_99, @reaper_corp, @null_admin)
- PGP Cryptographic Keys (e.g., PGP: 0x89ABCDEF, PGP: 0xAA308F91)
- Primary Extortion & Inflow Wallets (Wallet A)
- Connected Secondary Wallets (Wallet B: Mixer/Tumbler, Wallet C: Infra/Proxies, Wallet D: Off-Ramp)
- Infrastructure Assets (C2 Domains, TLS Certs)
- Persona Migration & Correlation Edges with Confidence Weights

Output format is directly consumable by Cytoscape.js and frontend graph components.
"""

from typing import Dict, Any, List, Optional
from ai.preprocessing.synthetic import SyntheticInvestigationAdapter
from ai.correlation.scoring import CorrelationEngine


# Visual styling classes matching the investigation UI theme
NODE_TYPE_STYLES = {
    "threat_actor": {
        "shape": "hexagon",
        "color": "#e05656",
        "background_color": "#8b1e1e",
        "icon": "skull",
        "category": "Threat Actor"
    },
    "darknet_handle": {
        "shape": "round-rectangle",
        "color": "#1abc9c",
        "background_color": "#0e5a4b",
        "icon": "user",
        "category": "Darknet Handle"
    },
    "pgp_key": {
        "shape": "diamond",
        "color": "#9b59b6",
        "background_color": "#5b2c6f",
        "icon": "key",
        "category": "PGP Cryptographic Key"
    },
    "primary_wallet": {
        "shape": "ellipse",
        "color": "#e67e22",
        "background_color": "#873600",
        "icon": "wallet",
        "category": "Primary Inflow Wallet"
    },
    "connected_wallet": {
        "shape": "ellipse",
        "color": "#3498db",
        "background_color": "#1b4f72",
        "icon": "coins",
        "category": "Connected Secondary Wallet"
    },
    "infrastructure": {
        "shape": "barrel",
        "color": "#f1c40f",
        "background_color": "#7d6608",
        "icon": "server",
        "category": "C2 / Hosting Infrastructure"
    }
}


class ThreatCorrelationGraphGenerator:
    """Generates structured network graph representations for threat actor dossiers."""

    def __init__(self):
        self.adapter = SyntheticInvestigationAdapter()
        self.correlation_engine = CorrelationEngine()

    def generate_actor_subgraph(self, persona: Dict[str, Any]) -> Dict[str, Any]:
        """Generates nodes and edges for a single threat actor and their connected entities."""
        name = persona.get("name", "UnknownActor")
        actor_node_id = f"actor_{name.lower()}"
        alias = persona.get("alias", f"@{name.lower()}")
        handle_node_id = f"handle_{name.lower()}"

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        # 1. Threat Actor Node
        nodes.append({
            "data": {
                "id": actor_node_id,
                "label": name,
                "type": "threat_actor",
                "category": "Threat Actor",
                "threat_category": persona.get("threat_category", "Unknown"),
                "shape": NODE_TYPE_STYLES["threat_actor"]["shape"],
                "color": NODE_TYPE_STYLES["threat_actor"]["color"],
                "bg_color": NODE_TYPE_STYLES["threat_actor"]["background_color"],
                "details": {
                    "id": persona.get("id"),
                    "forums": persona.get("forums", []),
                    "active_period": persona.get("active_period", {})
                }
            },
            "classes": "threat-actor-node"
        })

        # 2. Darknet Handle Node
        nodes.append({
            "data": {
                "id": handle_node_id,
                "label": alias if alias.startswith("@") else f"@{alias}",
                "type": "darknet_handle",
                "category": "Darknet Handle",
                "shape": NODE_TYPE_STYLES["darknet_handle"]["shape"],
                "color": NODE_TYPE_STYLES["darknet_handle"]["color"],
                "bg_color": NODE_TYPE_STYLES["darknet_handle"]["background_color"]
            },
            "classes": "handle-node"
        })

        # Edge: Actor -> Primary Alias
        edges.append({
            "data": {
                "id": f"edge_{actor_node_id}_{handle_node_id}",
                "source": actor_node_id,
                "target": handle_node_id,
                "label": "Primary Alias",
                "relationship": "Primary Alias",
                "style": "solid",
                "color": "#1abc9c",
                "confidence": 1.0
            },
            "classes": "alias-edge"
        })

        # 3. PGP Key Node
        pgp_fp = persona.get("pgp_fingerprint")
        pgp_kid = persona.get("pgp_key_id", "0x" + (pgp_fp.replace(" ", "")[-8:] if pgp_fp else "UNKNOWN"))
        if pgp_fp or pgp_kid:
            pgp_node_id = f"pgp_{name.lower()}"
            short_label = f"PGP: 0x{pgp_kid.replace('0x', '')}"
            nodes.append({
                "data": {
                    "id": pgp_node_id,
                    "label": short_label,
                    "full_fingerprint": pgp_fp,
                    "type": "pgp_key",
                    "category": "PGP Cryptographic Key",
                    "shape": NODE_TYPE_STYLES["pgp_key"]["shape"],
                    "color": NODE_TYPE_STYLES["pgp_key"]["color"],
                    "bg_color": NODE_TYPE_STYLES["pgp_key"]["background_color"]
                },
                "classes": "pgp-node"
            })

            # Edge: Handle -> PGP Key
            edges.append({
                "data": {
                    "id": f"edge_{handle_node_id}_{pgp_node_id}",
                    "source": handle_node_id,
                    "target": pgp_node_id,
                    "label": "Signed Forum Post",
                    "relationship": "Signed Forum Post",
                    "style": "solid",
                    "color": "#9b59b6",
                    "confidence": 1.0
                },
                "classes": "pgp-edge"
            })

        # 4. Wallets Topology (Wallet A -> [Wallet B, Wallet C, Wallet D])
        wallets = persona.get("wallets", [])
        if wallets:
            w0 = wallets[0]
            w_a_id = f"wallet_a_{name.lower()}"
            nodes.append({
                "data": {
                    "id": w_a_id,
                    "label": "Wallet A (Primary Extortion Inflow)",
                    "address": w0.get("address", "1SyntheticBTCInflowWallet"),
                    "type": "primary_wallet",
                    "category": "Primary Inflow Wallet",
                    "shape": NODE_TYPE_STYLES["primary_wallet"]["shape"],
                    "color": NODE_TYPE_STYLES["primary_wallet"]["color"],
                    "bg_color": NODE_TYPE_STYLES["primary_wallet"]["background_color"],
                    "stats": {
                        "tx_frequency": w0.get("tx_frequency"),
                        "avg_tx_value": w0.get("avg_tx_value"),
                        "inbound_volume": w0.get("inbound_volume"),
                        "outbound_volume": w0.get("outbound_volume")
                    }
                },
                "classes": "primary-wallet-node"
            })

            # Edge: Actor -> Wallet A
            edges.append({
                "data": {
                    "id": f"edge_{actor_node_id}_{w_a_id}",
                    "source": actor_node_id,
                    "target": w_a_id,
                    "label": "Potential Association",
                    "relationship": "Potential Association",
                    "style": "dashed",
                    "color": "#e67e22",
                    "confidence": 0.85
                },
                "classes": "association-edge"
            })

            # Connected Secondary Wallets
            secondary_specs = [
                ("Wallet B (Mixer / Tumbler Hub)", "mixer", "#3498db"),
                ("Wallet C (Infrastructure & Proxies)", "infra", "#3498db"),
                ("Wallet D (Off-Ramp Exchange Liquidation)", "offramp", "#3498db")
            ]

            for s_idx, (s_label, s_tag, s_col) in enumerate(secondary_specs, start=1):
                sec_id = f"wallet_{s_tag}_{name.lower()}"
                nodes.append({
                    "data": {
                        "id": sec_id,
                        "label": s_label,
                        "type": "connected_wallet",
                        "category": "Connected Secondary Wallet",
                        "subtype": s_tag,
                        "shape": NODE_TYPE_STYLES["connected_wallet"]["shape"],
                        "color": s_col,
                        "bg_color": NODE_TYPE_STYLES["connected_wallet"]["background_color"]
                    },
                    "classes": "connected-wallet-node"
                })

                # Edge: Wallet A -> Secondary Wallet
                edges.append({
                    "data": {
                        "id": f"edge_{w_a_id}_{sec_id}",
                        "source": w_a_id,
                        "target": sec_id,
                        "label": "Potential Association",
                        "relationship": "Potential Association",
                        "style": "dashed",
                        "color": "#d35400",
                        "confidence": 0.78
                    },
                    "classes": "wallet-flow-edge"
                })

            # Inter-wallet flow edge (Wallet B -> Wallet C -> Wallet D)
            edges.append({
                "data": {
                    "id": f"edge_flow_bc_{name.lower()}",
                    "source": f"wallet_mixer_{name.lower()}",
                    "target": f"wallet_infra_{name.lower()}",
                    "label": "Potential Association",
                    "relationship": "Potential Association",
                    "style": "dashed",
                    "color": "#d35400",
                    "confidence": 0.72
                },
                "classes": "wallet-flow-edge"
            })
            edges.append({
                "data": {
                    "id": f"edge_flow_cd_{name.lower()}",
                    "source": f"wallet_infra_{name.lower()}",
                    "target": f"wallet_offramp_{name.lower()}",
                    "label": "Potential Association",
                    "relationship": "Potential Association",
                    "style": "dashed",
                    "color": "#d35400",
                    "confidence": 0.75
                },
                "classes": "wallet-flow-edge"
            })

        return {"nodes": nodes, "edges": edges}

    def generate_full_correlation_graph(self, target_actor_name: str = "ShadowX") -> Dict[str, Any]:
        """
        Generates comprehensive multi-actor correlation topology showing:
        - Target Actor (e.g. ShadowX) with full wallet & alias cluster
        - Associated Migration / Co-monitored Actors (e.g. Phant0m_Reaper, NullByte_VIP, Shadow_X2026)
        - Analytical migration and association links
        """
        all_nodes: List[Dict[str, Any]] = []
        all_edges: List[Dict[str, Any]] = []
        node_ids_seen = set()

        # Core personas to include in demo topology
        demo_actors = [
            self.adapter.get_persona("ShadowX"),
            {
                "id": "ACTOR-005",
                "name": "Phant0m_Reaper",
                "alias": "@reaper_corp",
                "threat_category": "Initial Access Broker",
                "pgp_key_id": "0xAA308F91",
                "wallets": []
            },
            {
                "id": "ACTOR-006",
                "name": "NullByte_VIP",
                "alias": "@null_admin",
                "threat_category": "Malware Author",
                "pgp_key_id": "0xB876144D3",
                "wallets": []
            },
            self.adapter.get_persona("Shadow_X2026")
        ]

        for p in demo_actors:
            if not p:
                continue
            sub = self.generate_actor_subgraph(p)
            for n in sub["nodes"]:
                nid = n["data"]["id"]
                if nid not in node_ids_seen:
                    node_ids_seen.add(nid)
                    all_nodes.append(n)
            for e in sub["edges"]:
                all_edges.append(e)

        # Multi-Signal Migration Edge (ShadowX -> Shadow_X2026)
        p_orig = self.adapter.get_persona("ShadowX")
        p_mig = self.adapter.get_persona("Shadow_X2026")
        if p_orig and p_mig:
            corr_result = self.correlation_engine.correlate_personas(p_orig, p_mig)
            conf = corr_result["overall_confidence"]
            all_edges.append({
                "data": {
                    "id": "edge_migration_shadowx_shadowx2026",
                    "source": "actor_shadowx",
                    "target": "actor_shadow_x2026",
                    "label": f"Migration Candidate ({conf:.0%})",
                    "relationship": "Migration Candidate",
                    "style": "dashed",
                    "color": "#f39c12",
                    "confidence": conf,
                    "signals": corr_result["signals"]
                },
                "classes": "migration-edge"
            })

        return {
            "case_id": f"CASE-SIH26151-{target_actor_name.upper()}",
            "title": "Threat Actor & Wallet Correlation Graph",
            "target": target_actor_name,
            "hierarchy_model": "SHADOWX -> Wallet A -> [Wallet B, Wallet C, Wallet D]",
            "engine": "Cytoscape.js Engine v3.x Compatible",
            "layout_recommended": "breadthfirst / concentric / dagre",
            "elements": {
                "nodes": all_nodes,
                "edges": all_edges
            },
            "node_count": len(all_nodes),
            "edge_count": len(all_edges),
            "entity_legend": [
                {"type": "threat_actor", "label": "Threat Actor (ShadowX)", "color": "#e05656"},
                {"type": "darknet_handle", "label": "Darknet Handle (@x_shadow_99)", "color": "#1abc9c"},
                {"type": "pgp_key", "label": "PGP Cryptographic Key", "color": "#9b59b6"},
                {"type": "primary_wallet", "label": "Primary Wallet (Wallet A)", "color": "#e67e22"},
                {"type": "connected_wallet", "label": "Connected Wallets (B, C, D)", "color": "#3498db"}
            ],
            "safety_notice": "SYNTHETIC DEMO: Blockchain data shown is synthetic demonstration data. Relationships between actors and wallets represent 'Potential Association' heuristics."
        }
