"""
Stylometric Feature Extraction Pipeline
SIH26151: Dark Web Threat Actor De-anonymization

Extracts rich stylometric signatures from raw text:
- Character n-grams (2-gram to 4-gram)
- Word n-grams (1-gram to 3-gram)
- Function-word frequency distribution (100+ standard stylistic markers)
- Vocabulary richness metrics (TTR, Root TTR, Yule's K, Simpson's D, Hapax Legomena)
- Structural & sentence-level statistics (avg sentence length, word length distribution)
- Punctuation distribution & special character usage patterns
- Casing & capitalization style

Provides unified pair-difference extraction for binary authorship classifiers.
"""

import math
import re
import string
from collections import Counter
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


# Curated list of 100+ closed-class English function words (style markers)
FUNCTION_WORDS = [
    "a", "about", "above", "after", "again", "against", "all", "almost", "along",
    "already", "also", "although", "always", "among", "an", "and", "another", "any",
    "anybody", "anyone", "anything", "anywhere", "are", "around", "as", "at", "be",
    "because", "been", "before", "being", "between", "both", "but", "by", "can",
    "cannot", "could", "did", "do", "does", "doing", "done", "down", "during", "each",
    "either", "enough", "even", "every", "everybody", "everyone", "everything",
    "everywhere", "few", "for", "from", "further", "had", "has", "have", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "if",
    "in", "into", "is", "it", "its", "itself", "just", "less", "me", "more", "most",
    "much", "must", "my", "myself", "neither", "no", "nobody", "none", "noone",
    "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on", "once",
    "one", "only", "onto", "or", "other", "others", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "several", "shall", "she", "should",
    "since", "so", "some", "somebody", "someone", "something", "somewhere", "still",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "therefore", "these", "they", "this", "those", "though", "through",
    "throughout", "thru", "thus", "to", "together", "too", "toward", "under", "until",
    "up", "upon", "us", "very", "was", "we", "well", "were", "what", "whatever",
    "when", "where", "which", "while", "who", "whom", "whose", "why", "will",
    "with", "within", "without", "would", "yet", "you", "your", "yours", "yourself"
]

PUNCT_CHARS = [".", ",", "!", "?", ";", ":", "-", "(", ")", "[", "]", "{", "}", "\"", "'", "/", "\\", "@", "#", "$", "%", "^", "&", "*", "_", "+", "=", "<", ">", "~", "`"]


class StylometryExtractor:
    """Extracts reproducible stylometric vectors and pairwise similarity metrics."""

    def __init__(self, max_char_features: int = 150, max_word_features: int = 150):
        self.max_char_features = max_char_features
        self.max_word_features = max_word_features
        self.char_vectorizer = TfidfVectorizer(
            analyzer="char",
            ngram_range=(2, 4),
            max_features=max_char_features,
            sublinear_tf=True
        )
        self.word_vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            max_features=max_word_features,
            sublinear_tf=True
        )
        self.is_fitted = False

    def fit_vectorizers(self, texts: List[str]) -> "StylometryExtractor":
        """Fits character and word TF-IDF vectorizers on reference training corpus."""
        valid_texts = [t for t in texts if t and len(t.strip()) > 10]
        if not valid_texts:
            valid_texts = ["sample text placeholder for fitting tfidf"]
        self.char_vectorizer.fit(valid_texts)
        self.word_vectorizer.fit(valid_texts)
        self.is_fitted = True
        return self

    def extract_statistical_features(self, text: str) -> Dict[str, float]:
        """
        Extracts statistical, lexical richness, punctuation, and casing features.
        Returns a dictionary of named numerical features.
        """
        feats: Dict[str, float] = {}
        if not text:
            return {k: 0.0 for k in self.get_statistical_feature_names()}

        # Tokenization
        raw_words = re.findall(r"\b\w+\b", text)
        words_lower = [w.lower() for w in raw_words]
        total_words = len(words_lower)
        char_count = len(text)

        # Sentence extraction
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        total_sentences = len(sentences)

        # 1. Structural & Length Statistics
        feats["avg_word_length"] = np.mean([len(w) for w in raw_words]) if total_words > 0 else 0.0
        feats["std_word_length"] = np.std([len(w) for w in raw_words]) if total_words > 1 else 0.0
        feats["avg_sentence_length_words"] = total_words / max(total_sentences, 1)
        feats["avg_sentence_length_chars"] = char_count / max(total_sentences, 1)

        # 2. Vocabulary Richness & Lexical Diversity
        if total_words > 0:
            unique_words = len(set(words_lower))
            feats["ttr"] = unique_words / total_words  # Type-Token Ratio
            feats["root_ttr"] = unique_words / math.sqrt(total_words)  # Guiraud's R
            
            word_counts = Counter(words_lower)
            hapax_legomena = sum(1 for c in word_counts.values() if c == 1)
            dis_legomena = sum(1 for c in word_counts.values() if c == 2)
            feats["hapax_ratio"] = hapax_legomena / total_words
            feats["dis_legomena_ratio"] = dis_legomena / total_words

            # Yule's Characteristic K
            m1 = total_words
            m2 = sum(count ** 2 for count in word_counts.values())
            feats["yules_k"] = 10000 * (m2 - m1) / max(m1 ** 2, 1)

            # Simpson's Diversity Index D
            feats["simpsons_d"] = sum(count * (count - 1) for count in word_counts.values()) / max(m1 * (m1 - 1), 1)
        else:
            feats["ttr"] = 0.0
            feats["root_ttr"] = 0.0
            feats["hapax_ratio"] = 0.0
            feats["dis_legomena_ratio"] = 0.0
            feats["yules_k"] = 0.0
            feats["simpsons_d"] = 0.0

        # 3. Function Word Frequencies (normalized per 1000 words)
        fword_counter = Counter(words_lower)
        for fw in FUNCTION_WORDS[:40]:  # Use top 40 key function words
            feats[f"fw_{fw}"] = (fword_counter.get(fw, 0) / max(total_words, 1)) * 1000.0

        # 4. Punctuation Distribution (normalized per 1000 chars)
        for p in PUNCT_CHARS[:20]:
            count = text.count(p)
            feats[f"pct_{ord(p)}"] = (count / max(char_count, 1)) * 1000.0

        # 5. Casing & Special Character Ratios
        feats["uppercase_ratio"] = sum(1 for c in text if c.isupper()) / max(char_count, 1)
        feats["digit_ratio"] = sum(1 for c in text if c.isdigit()) / max(char_count, 1)
        feats["whitespace_ratio"] = sum(1 for c in text if c.isspace()) / max(char_count, 1)
        feats["special_symbol_ratio"] = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(char_count, 1)

        # Repeated punctuation (e.g. '!!', '???', '...')
        feats["repeated_punct_count"] = len(re.findall(r"([!?.,]){2,}", text)) / max(total_sentences, 1)

        return feats

    def get_statistical_feature_names(self) -> List[str]:
        """Returns ordered list of statistical feature keys."""
        sample_feats = self.extract_statistical_features("Sample text to extract valid feature schema.")
        return sorted(list(sample_feats.keys()))

    def extract_vector(self, text: str) -> np.ndarray:
        """
        Extracts concatenated [statistical_features, tfidf_char, tfidf_word] for a single text.
        """
        stat_dict = self.extract_statistical_features(text)
        stat_vals = np.array([stat_dict[k] for k in sorted(stat_dict.keys())], dtype=float)

        if self.is_fitted:
            char_vec = self.char_vectorizer.transform([text]).toarray()[0]
            word_vec = self.word_vectorizer.transform([text]).toarray()[0]
            return np.concatenate([stat_vals, char_vec, word_vec])
        else:
            return stat_vals

    def extract_pair_features(self, text_a: str, text_b: str) -> np.ndarray:
        """
        Extracts pairwise difference & similarity representation between Text A and Text B:
        - Absolute difference |f_A - f_B|
        - Relative difference |f_A - f_B| / (f_A + f_B + eps)
        - Sub-modality cosine similarities (character, word, function-word, punctuation)
        """
        stat_a = self.extract_statistical_features(text_a)
        stat_b = self.extract_statistical_features(text_b)

        keys = sorted(stat_a.keys())
        va = np.array([stat_a[k] for k in keys], dtype=float)
        vb = np.array([stat_b[k] for k in keys], dtype=float)

        abs_diff = np.abs(va - vb)
        rel_diff = abs_diff / (va + vb + 1e-6)

        # Calculate modular cosine similarities
        if self.is_fitted:
            ca = self.char_vectorizer.transform([text_a]).toarray()[0]
            cb = self.char_vectorizer.transform([text_b]).toarray()[0]
            norm_ca = np.linalg.norm(ca)
            norm_cb = np.linalg.norm(cb)
            char_sim = float(np.dot(ca, cb) / (norm_ca * norm_cb)) if (norm_ca > 0 and norm_cb > 0) else 0.0

            wa = self.word_vectorizer.transform([text_a]).toarray()[0]
            wb = self.word_vectorizer.transform([text_b]).toarray()[0]
            norm_wa = np.linalg.norm(wa)
            norm_wb = np.linalg.norm(wb)
            word_sim = float(np.dot(wa, wb) / (norm_wa * norm_wb)) if (norm_wa > 0 and norm_wb > 0) else 0.0

            char_diff = np.abs(ca - cb)
            word_diff = np.abs(wa - wb)
            return np.concatenate([abs_diff, rel_diff, [char_sim, word_sim], char_diff, word_diff])
        else:
            return np.concatenate([abs_diff, rel_diff])

    def extract_batch_pair_features(self, texts_a: List[str], texts_b: List[str]) -> np.ndarray:
        """
        Fast batch vectorized pair feature extraction across text pairs.
        """
        stat_a_list = [self.extract_statistical_features(t) for t in texts_a]
        stat_b_list = [self.extract_statistical_features(t) for t in texts_b]

        keys = sorted(stat_a_list[0].keys())
        mat_va = np.array([[sa[k] for k in keys] for sa in stat_a_list], dtype=float)
        mat_vb = np.array([[sb[k] for k in keys] for sb in stat_b_list], dtype=float)

        abs_diff = np.abs(mat_va - mat_vb)
        rel_diff = abs_diff / (mat_va + mat_vb + 1e-6)

        if self.is_fitted:
            ca = self.char_vectorizer.transform(texts_a).toarray()
            cb = self.char_vectorizer.transform(texts_b).toarray()
            wa = self.word_vectorizer.transform(texts_a).toarray()
            wb = self.word_vectorizer.transform(texts_b).toarray()

            norm_ca = np.linalg.norm(ca, axis=1, keepdims=True)
            norm_cb = np.linalg.norm(cb, axis=1, keepdims=True)
            char_sims = np.sum(ca * cb, axis=1, keepdims=True) / (norm_ca * norm_cb + 1e-6)

            norm_wa = np.linalg.norm(wa, axis=1, keepdims=True)
            norm_wb = np.linalg.norm(wb, axis=1, keepdims=True)
            word_sims = np.sum(wa * wb, axis=1, keepdims=True) / (norm_wa * norm_wb + 1e-6)

            char_diff = np.abs(ca - cb)
            word_diff = np.abs(wa - wb)

            return np.hstack([abs_diff, rel_diff, char_sims, word_sims, char_diff, word_diff])
        else:
            return np.hstack([abs_diff, rel_diff])
