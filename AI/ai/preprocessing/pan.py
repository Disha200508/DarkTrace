"""
PAN Authorship Verification Preprocessor
SIH26151: Dark Web Threat Actor De-anonymization

Loads and processes the PAN Authorship Verification dataset from 2022/dataset0 and dataset1.
Extracts high-quality pairs (text_a, text_b) for same-author and different-author verification
without data leakage, respecting predefined train/validation/test splits.
"""

import os
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class AuthorPair:
    pair_id: str
    text_a: str
    text_b: str
    label: int  # 1 = same author, 0 = different author
    author_a: str
    author_b: str
    split: str  # train, validation, test
    dataset_name: str
    site: str = ""


class PANPreprocessor:
    """Preprocesses PAN Authorship Verification datasets into binary comparison pairs."""

    def __init__(self, base_dir: str = "2022"):
        self.base_dir = base_dir

    def clean_text(self, text: str) -> str:
        """Cleans and standardizes text preserving stylometric features."""
        if not text:
            return ""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse excessive whitespace
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def parse_problem_folder(self, folder_path: str, split_name: str, dataset_name: str = "dataset0") -> List[AuthorPair]:
        """
        Parses all problem-*.txt and truth-problem-*.json files in a directory.
        Constructs balanced same-author and different-author text pairs.
        """
        if not os.path.exists(folder_path):
            return []

        files = os.listdir(folder_path)
        txt_files = [f for f in files if f.startswith("problem-") and f.endswith(".txt")]
        
        pairs: List[AuthorPair] = []
        author_corpus: Dict[str, List[str]] = {}

        for txt_file in txt_files:
            prob_num = txt_file.replace("problem-", "").replace(".txt", "")
            truth_file = f"truth-problem-{prob_num}.json"
            truth_path = os.path.join(folder_path, truth_file)
            txt_path = os.path.join(folder_path, txt_file)

            if not os.path.exists(truth_path):
                continue

            try:
                with open(txt_path, "r", encoding="utf-8", errors="ignore") as tf:
                    raw_text = tf.read()
                with open(truth_path, "r", encoding="utf-8", errors="ignore") as jf:
                    truth = json.load(jf)
            except Exception:
                continue

            paragraphs = [p.strip() for p in raw_text.split("\n") if p.strip()]
            paragraph_authors = truth.get("paragraph-authors", [])
            structure = truth.get("structure", [])
            site = truth.get("site", "")

            if not paragraphs or len(paragraphs) != len(paragraph_authors):
                # If paragraph counts don't align, skip or fallback
                continue

            # Group paragraphs by author index (1, 2, ...)
            author_paragraphs: Dict[int, List[str]] = {}
            for p_idx, auth_idx in enumerate(paragraph_authors):
                if auth_idx not in author_paragraphs:
                    author_paragraphs[auth_idx] = []
                author_paragraphs[auth_idx].append(paragraphs[p_idx])

            # Resolve global author IDs from structure if available
            # structure contains author IDs corresponding to transitions
            author_id_map: Dict[int, str] = {}
            if structure:
                unique_indices = sorted(list(set(paragraph_authors)))
                for u_idx in unique_indices:
                    # Map to structure ID if within range, else make local unique ID
                    if u_idx <= len(structure):
                        author_id_map[u_idx] = f"author_{structure[u_idx - 1]}"
                    else:
                        author_id_map[u_idx] = f"ds0_{prob_num}_a{u_idx}"

            # 1. DIFFERENT-AUTHOR PAIR (Author 1 vs Author 2)
            if len(author_paragraphs) >= 2:
                text_a = self.clean_text("\n\n".join(author_paragraphs[1]))
                text_b = self.clean_text("\n\n".join(author_paragraphs[2]))
                auth_a_id = author_id_map.get(1, f"prob_{prob_num}_1")
                auth_b_id = author_id_map.get(2, f"prob_{prob_num}_2")

                if len(text_a) >= 50 and len(text_b) >= 50:
                    pairs.append(AuthorPair(
                        pair_id=f"{dataset_name}_{split_name}_diff_{prob_num}",
                        text_a=text_a,
                        text_b=text_b,
                        label=0,
                        author_a=auth_a_id,
                        author_b=auth_b_id,
                        split=split_name,
                        dataset_name=dataset_name,
                        site=site
                    ))

            # 2. SAME-AUTHOR PAIR (Split paragraphs of Author 1 or 2)
            for auth_idx, paras in author_paragraphs.items():
                auth_id = author_id_map.get(auth_idx, f"prob_{prob_num}_{auth_idx}")
                # Store full text in corpus for potential cross-problem pairing
                full_auth_text = self.clean_text("\n\n".join(paras))
                if len(full_auth_text) >= 100:
                    if auth_id not in author_corpus:
                        author_corpus[auth_id] = []
                    author_corpus[auth_id].append(full_auth_text)

                if len(paras) >= 2:
                    mid = len(paras) // 2
                    part_a = self.clean_text("\n\n".join(paras[:mid]))
                    part_b = self.clean_text("\n\n".join(paras[mid:]))
                    if len(part_a) >= 40 and len(part_b) >= 40:
                        pairs.append(AuthorPair(
                            pair_id=f"{dataset_name}_{split_name}_same_{prob_num}_a{auth_idx}",
                            text_a=part_a,
                            text_b=part_b,
                            label=1,
                            author_a=auth_id,
                            author_b=auth_id,
                            split=split_name,
                            dataset_name=dataset_name,
                            site=site
                        ))

        # 3. Pair cross-problem texts from same author if they exist
        cross_pairs = 0
        for auth_id, text_list in author_corpus.items():
            if len(text_list) >= 2:
                for i in range(len(text_list) - 1):
                    pairs.append(AuthorPair(
                        pair_id=f"{dataset_name}_{split_name}_same_cross_{auth_id}_{i}",
                        text_a=text_list[i],
                        text_b=text_list[i+1],
                        label=1,
                        author_a=auth_id,
                        author_b=auth_id,
                        split=split_name,
                        dataset_name=dataset_name,
                        site=""
                    ))
                    cross_pairs += 1

        return pairs

    def load_all_splits(self) -> Dict[str, List[AuthorPair]]:
        """
        Loads and returns train, validation, and test splits from dataset0 and dataset1.
        """
        splits = {
            "train": self.parse_problem_folder(os.path.join(self.base_dir, "dataset0", "train"), "train", "dataset0"),
            "validation": self.parse_problem_folder(os.path.join(self.base_dir, "dataset0", "validation"), "validation", "dataset0"),
            "test": self.parse_problem_folder(os.path.join(self.base_dir, "dataset0", "test"), "test", "dataset0")
        }
        # Add dataset1 test pairs if available
        ds1_test = self.parse_problem_folder(os.path.join(self.base_dir, "dataset1", "test"), "test", "dataset1")
        if ds1_test:
            splits["test_ds1"] = ds1_test

        return splits
