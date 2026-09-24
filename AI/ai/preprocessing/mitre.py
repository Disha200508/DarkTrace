"""
MITRE ATT&CK STIX Preprocessor & Knowledge Base
SIH26151: Dark Web Threat Actor De-anonymization

Loads and parses enterprise ATT&CK STIX data. Builds an in-memory searchable
knowledge base of techniques, sub-techniques, tactics, and provides keyword/semantic
extraction capabilities for actor TTP profiling.
"""

import os
import json
import re
import glob
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Technique:
    id: str
    name: str
    description: str
    tactics: List[str]
    subtechnique: bool
    parent_id: Optional[str]
    platforms: List[str]
    detection: str


class MitreAttackKB:
    """Knowledge base and extractor for MITRE ATT&CK Enterprise STIX dataset."""

    def __init__(self, stix_path: Optional[str] = None):
        self.stix_path = stix_path or self._find_latest_stix()
        self.techniques: Dict[str, Technique] = {}
        self.name_to_id: Dict[str, str] = {}
        self.tactic_to_techniques: Dict[str, List[str]] = {}
        self._keyword_index: Dict[str, Set[str]] = {}
        self._load_stix()

    def _find_latest_stix(self) -> str:
        """Finds latest enterprise attack STIX JSON file."""
        candidates = glob.glob("attack-stix-data/enterprise-attack/*.json")
        if candidates:
            return sorted(candidates)[-1]
        default_path = "attack-stix-data/enterprise-attack/enterprise-attack.json"
        return default_path

    def _load_stix(self) -> None:
        """Parses the STIX bundle JSON."""
        if not os.path.exists(self.stix_path):
            # Try to search recursively
            all_stix = glob.glob("**/enterprise-attack*.json", recursive=True)
            if all_stix:
                self.stix_path = all_stix[0]
            else:
                return

        with open(self.stix_path, "r", encoding="utf-8", errors="ignore") as f:
            bundle = json.load(f)

        objects = bundle.get("objects", [])
        for obj in objects:
            if obj.get("type") == "attack-pattern" and not obj.get("revoked", False):
                ext_refs = obj.get("external_references", [])
                mitre_id = next((ref.get("external_id") for ref in ext_refs if ref.get("source_name") == "mitre-attack"), None)
                if not mitre_id:
                    continue

                name = obj.get("name", "")
                desc = obj.get("description", "")
                is_sub = obj.get("x_mitre_is_subtechnique", False)
                parent_id = mitre_id.split(".")[0] if is_sub and "." in mitre_id else None
                platforms = obj.get("x_mitre_platforms", [])
                detection = obj.get("x_mitre_detection", "")
                tactics = [
                    phase.get("phase_name", "")
                    for phase in obj.get("kill_chain_phases", [])
                    if phase.get("kill_chain_name") == "mitre-attack"
                ]

                tech = Technique(
                    id=mitre_id,
                    name=name,
                    description=desc,
                    tactics=tactics,
                    subtechnique=is_sub,
                    parent_id=parent_id,
                    platforms=platforms,
                    detection=detection
                )
                self.techniques[mitre_id] = tech
                self.name_to_id[name.lower()] = mitre_id

                for tac in tactics:
                    if tac not in self.tactic_to_techniques:
                        self.tactic_to_techniques[tac] = []
                    self.tactic_to_techniques[tac].append(mitre_id)

                # Build keyword index from name and key terms
                keywords = re.findall(r"\b[a-zA-Z]{4,}\b", f"{name} {desc[:200]}".lower())
                for kw in set(keywords):
                    if kw not in self._keyword_index:
                        self._keyword_index[kw] = set()
                    self._keyword_index[kw].add(mitre_id)

    def get_technique(self, tech_id: str) -> Optional[Technique]:
        """Lookup technique by ID (e.g., 'T1059' or 'T1059.001')."""
        return self.techniques.get(tech_id)

    def search_by_name(self, query: str) -> List[Technique]:
        """Search techniques by name substring."""
        query = query.lower()
        return [t for t in self.techniques.values() if query in t.name.lower()]

    def extract_ttps_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extracts candidate TTPs from text using explicit TTP mentions (e.g. T1059),
        technique names, and characteristic cyber keywords.
        Returns candidate TTP IDs, names, and extraction confidence.
        """
        if not text:
            return {"ttp_ids": [], "ttp_names": [], "ttp_confidence": 0.0, "evidence": []}

        found_ids: Set[str] = set()
        evidence: List[str] = []

        # 1. Check for explicit MITRE ATT&CK IDs (e.g. T1059, T1059.001, T1566)
        explicit_matches = re.findall(r"\b(T\d{4}(?:\.\d{3})?)\b", text, flags=re.IGNORECASE)
        for em in explicit_matches:
            uid = em.upper()
            if uid in self.techniques:
                found_ids.add(uid)
                evidence.append(f"Explicit technique mention: {uid} ({self.techniques[uid].name})")

        # 2. Key phrase / tool mapping for common dark web & threat actor techniques
        rule_mappings = {
            r"\b(powershell|cmd\.exe|bash|sh|command line|terminal)\b": "T1059",
            r"\b(phishing|spearphishing|malicious attachment|credential harvesting link)\b": "T1566",
            r"\b(sql injection|sqli|database dump|leak|db breach)\b": "T1190",
            r"\b(tor proxy|c2|command and control|hidden service|reverse shell)\b": "T1071",
            r"\b(ransomware|encryptor|aes-256|decryptor|ransom note)\b": "T1486",
            r"\b(mimikatz|lsass|dump credentials|hashdump|procdump)\b": "T1003",
            r"\b(keylogger|keystroke logger|screen capture|screenshot grabber)\b": "T1056",
            r"\b(rdp|remote desktop|vnc|ssh tunnel)\b": "T1021",
            r"\b(privilege escalation|uac bypass|kernel exploit|cve-\d{4}-\d+)\b": "T1068",
            r"\b(scheduled task|cron job|persistence|registry run)\b": "T1053"
        }

        for pattern, tech_id in rule_mappings.items():
            if tech_id in self.techniques:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    found_ids.add(tech_id)
                    evidence.append(f"Behavioral pattern match '{match.group(0)}' -> {tech_id} ({self.techniques[tech_id].name})")

        ttp_ids = sorted(list(found_ids))
        ttp_names = [self.techniques[tid].name for tid in ttp_ids]
        confidence = min(0.95, 0.40 + 0.15 * len(ttp_ids)) if ttp_ids else 0.0

        return {
            "ttp_ids": ttp_ids,
            "ttp_names": ttp_names,
            "ttp_confidence": round(confidence, 3),
            "evidence": evidence
        }

    def all_technique_ids(self) -> List[str]:
        """Returns sorted list of all known technique IDs."""
        return sorted(list(self.techniques.keys()))
