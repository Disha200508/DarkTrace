"""
Stylometry Authorship Verification ML Model
SIH26151: Dark Web Threat Actor De-anonymization

Implements binary authorship verification between Text A and Text B.
Trains multiple candidate classifiers (Logistic Regression, Random Forest, XGBoost, Linear SVM),
calibrates posterior probabilities with Platt Scaling / Isotonic Regression,
and provides uncertainty-aware inference.
"""

import os
import json
import joblib
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, brier_score_loss
)
from ai.features.stylometry import StylometryExtractor


class StylometryModel:
    """End-to-end trained model for binary authorship verification."""

    def __init__(self, model_name: str = "calibrated_ensemble"):
        self.model_name = model_name
        self.extractor = StylometryExtractor()
        self.scaler = StandardScaler()
        self.classifier: Optional[Any] = None
        self.calibrator: Optional[Any] = None
        self.metrics: Dict[str, Any] = {}
        self.version = "1.0.0"

    def fit_and_evaluate(
        self,
        train_pairs: List[Any],
        val_pairs: List[Any],
        candidate_type: str = "logistic_regression"
    ) -> Dict[str, Any]:
        """
        Fits vectorizers, extracts pair features, scales, trains classifier,
        calibrates probabilities, and calculates validation metrics.
        """
        # 1. Fit TF-IDF on all training texts
        all_train_texts = [p.text_a for p in train_pairs] + [p.text_b for p in train_pairs]
        self.extractor.fit_vectorizers(all_train_texts)

        # 2. Extract pair features via fast batch vectorization
        train_a = [p.text_a for p in train_pairs]
        train_b = [p.text_b for p in train_pairs]
        X_train = self.extractor.extract_batch_pair_features(train_a, train_b)
        y_train = np.array([p.label for p in train_pairs])

        val_a = [p.text_a for p in val_pairs]
        val_b = [p.text_b for p in val_pairs]
        X_val = self.extractor.extract_batch_pair_features(val_a, val_b)
        y_val = np.array([p.label for p in val_pairs])

        # 3. Fit scaler
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # 4. Initialize candidate classifier
        if candidate_type == "logistic_regression":
            base_clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight="balanced")
        elif candidate_type == "random_forest":
            base_clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, class_weight="balanced")
        elif candidate_type == "gradient_boosting":
            base_clf = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
        elif candidate_type == "linear_svm":
            base_clf = LinearSVC(C=1.0, max_iter=2000, random_state=42, class_weight="balanced")
        else:
            base_clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)

        # 5. Fit & Calibrate with Platt scaling (sigmoid)
        if hasattr(base_clf, "predict_proba"):
            base_clf.fit(X_train_scaled, y_train)
            self.classifier = base_clf
            self.calibrator = CalibratedClassifierCV(base_clf, cv="prefit", method="sigmoid")
            self.calibrator.fit(X_val_scaled, y_val)
        else:
            # LinearSVC does not have predict_proba
            cal_cv = CalibratedClassifierCV(base_clf, cv=3, method="sigmoid")
            cal_cv.fit(X_train_scaled, y_train)
            self.classifier = cal_cv
            self.calibrator = cal_cv

        # 6. Evaluate on Validation Set
        val_probs = self.predict_proba_raw(X_val_scaled)
        val_preds = (val_probs >= 0.5).astype(int)

        acc = accuracy_score(y_val, val_preds)
        prec = precision_score(y_val, val_preds, zero_division=0)
        rec = recall_score(y_val, val_preds, zero_division=0)
        f1 = f1_score(y_val, val_preds, zero_division=0)
        roc_auc = roc_auc_score(y_val, val_probs)
        brier = brier_score_loss(y_val, val_probs)
        cm = confusion_matrix(y_val, val_preds).tolist()

        # Same-Author vs Different-Author breakdown
        same_mask = (y_val == 1)
        diff_mask = (y_val == 0)
        same_acc = accuracy_score(y_val[same_mask], val_preds[same_mask]) if np.sum(same_mask) > 0 else 0.0
        diff_acc = accuracy_score(y_val[diff_mask], val_preds[diff_mask]) if np.sum(diff_mask) > 0 else 0.0

        self.metrics = {
            "model_type": candidate_type,
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4),
            "roc_auc": round(float(roc_auc), 4),
            "brier_score": round(float(brier), 4),
            "confusion_matrix": cm,
            "same_author_accuracy": round(float(same_acc), 4),
            "different_author_accuracy": round(float(diff_acc), 4),
            "train_samples": len(train_pairs),
            "val_samples": len(val_pairs)
        }
        return self.metrics

    def predict_proba_raw(self, X_scaled: np.ndarray) -> np.ndarray:
        """Helper to get calibrated probabilities for class 1 (same author)."""
        if self.calibrator is not None:
            return self.calibrator.predict_proba(X_scaled)[:, 1]
        elif hasattr(self.classifier, "predict_proba"):
            return self.classifier.predict_proba(X_scaled)[:, 1]
        else:
            return np.full(len(X_scaled), 0.5)

    def compare_texts(self, text_a: str, text_b: str) -> Dict[str, Any]:
        """
        Inference function: compares two texts and produces sub-modality similarities,
        overall stylometric score, calibrated same-author probability, and classification.
        """
        if not text_a or not text_b or len(text_a.strip()) < 10 or len(text_b.strip()) < 10:
            return {
                "character_similarity": 0.0,
                "word_similarity": 0.0,
                "vocabulary_similarity": 0.0,
                "punctuation_similarity": 0.0,
                "syntax_similarity": 0.0,
                "stylometric_score": 0.0,
                "same_author_probability": 0.0,
                "classification": "Insufficient Text Length",
                "model_name": "stylometry_verifier",
                "model_version": self.version,
                "methodology": "Character + Word N-Gram + Statistical Stylometry"
            }

        # Sub-modality extraction
        stat_a = self.extractor.extract_statistical_features(text_a)
        stat_b = self.extractor.extract_statistical_features(text_b)

        # 1. Vocabulary similarity (TTR, Yule's K, Simpson's D)
        vocab_keys = ["ttr", "root_ttr", "hapax_ratio", "yules_k", "simpsons_d"]
        va = np.array([stat_a.get(k, 0.0) for k in vocab_keys])
        vb = np.array([stat_b.get(k, 0.0) for k in vocab_keys])
        vocab_sim = 1.0 - np.mean(np.abs(va - vb) / (np.abs(va) + np.abs(vb) + 1e-4))
        vocab_sim = float(np.clip(vocab_sim, 0.0, 1.0))

        # 2. Punctuation similarity
        pct_keys = [k for k in stat_a.keys() if k.startswith("pct_") or k == "repeated_punct_count"]
        pa = np.array([stat_a.get(k, 0.0) for k in pct_keys])
        pb = np.array([stat_b.get(k, 0.0) for k in pct_keys])
        n_pa, n_pb = np.linalg.norm(pa), np.linalg.norm(pb)
        pct_sim = float(np.dot(pa, pb) / (n_pa * n_pb)) if (n_pa > 0 and n_pb > 0) else 0.5

        # 3. Syntax / Structural similarity
        syn_keys = ["avg_word_length", "std_word_length", "avg_sentence_length_words", "avg_sentence_length_chars"]
        sa = np.array([stat_a.get(k, 0.0) for k in syn_keys])
        sb = np.array([stat_b.get(k, 0.0) for k in syn_keys])
        syn_sim = 1.0 - np.mean(np.abs(sa - sb) / (np.abs(sa) + np.abs(sb) + 1e-4))
        syn_sim = float(np.clip(syn_sim, 0.0, 1.0))

        # 4. Character & Word TF-IDF similarity
        if self.extractor.is_fitted:
            ca = self.extractor.char_vectorizer.transform([text_a]).toarray()[0]
            cb = self.extractor.char_vectorizer.transform([text_b]).toarray()[0]
            n_ca, n_cb = np.linalg.norm(ca), np.linalg.norm(cb)
            char_sim = float(np.dot(ca, cb) / (n_ca * n_cb)) if (n_ca > 0 and n_cb > 0) else 0.0

            wa = self.extractor.word_vectorizer.transform([text_a]).toarray()[0]
            wb = self.extractor.word_vectorizer.transform([text_b]).toarray()[0]
            n_wa, n_wb = np.linalg.norm(wa), np.linalg.norm(wb)
            word_sim = float(np.dot(wa, wb) / (n_wa * n_wb)) if (n_wa > 0 and n_wb > 0) else 0.0
        else:
            char_sim = 0.5
            word_sim = 0.5

        # Extract pairwise full feature vector & run trained classifier
        pair_feat = self.extractor.extract_pair_features(text_a, text_b)
        scaled_feat = self.scaler.transform([pair_feat]) if hasattr(self.scaler, "mean_") and self.scaler.mean_ is not None else pair_feat.reshape(1, -1)

        if self.calibrator is not None:
            raw_prob = float(self.calibrator.predict_proba(scaled_feat)[0, 1])
        elif self.classifier is not None and hasattr(self.classifier, "predict_proba"):
            raw_prob = float(self.classifier.predict_proba(scaled_feat)[0, 1])
        else:
            raw_prob = float(0.3 * char_sim + 0.25 * word_sim + 0.2 * vocab_sim + 0.15 * pct_sim + 0.1 * syn_sim)

        # Lexical & syntactic consistency bounding:
        # Prevent false-positive overconfidence on completely disjoint vocabulary
        lexical_sim = float(0.35 * char_sim + 0.35 * word_sim + 0.15 * vocab_sim + 0.15 * pct_sim)
        if word_sim < 0.12 and char_sim < 0.60:
            prob = min(raw_prob, max(0.10, lexical_sim * 1.2))
        else:
            prob = raw_prob

        prob = float(np.clip(prob, 0.0, 1.0))
        stylometric_score = round(prob, 4)

        if prob >= 0.70:
            classification = "Potential Same-Author Pattern"
        elif prob >= 0.45:
            classification = "Inconclusive / Moderate Stylistic Similarity"
        else:
            classification = "Potential Different-Author Pattern"

        return {
            "character_similarity": round(float(np.clip(char_sim, 0.0, 1.0)), 4),
            "word_similarity": round(float(np.clip(word_sim, 0.0, 1.0)), 4),
            "vocabulary_similarity": round(float(np.clip(vocab_sim, 0.0, 1.0)), 4),
            "punctuation_similarity": round(float(np.clip(pct_sim, 0.0, 1.0)), 4),
            "syntax_similarity": round(float(np.clip(syn_sim, 0.0, 1.0)), 4),
            "stylometric_score": stylometric_score,
            "same_author_probability": stylometric_score,
            "classification": classification,
            "model_name": "stylometry_verifier",
            "model_version": self.version,
            "feature_version": "1.0.0",
            "methodology": "Character + Word N-Gram + Statistical Stylometry"
        }

    def save(self, save_dir: str = "ai/saved_models") -> None:
        """Serializes model artifacts."""
        os.makedirs(save_dir, exist_ok=True)
        joblib.dump(self.classifier, os.path.join(save_dir, "model.pkl"))
        joblib.dump(self.calibrator, os.path.join(save_dir, "calibrator.pkl"))
        joblib.dump(self.scaler, os.path.join(save_dir, "scaler.pkl"))
        joblib.dump(self.extractor, os.path.join(save_dir, "extractor.pkl"))
        with open(os.path.join(save_dir, "feature_config.json"), "w") as f:
            json.dump({
                "model_version": self.version,
                "metrics": self.metrics,
                "statistical_features": self.extractor.get_statistical_feature_names()
            }, f, indent=2)

    def load(self, save_dir: str = "ai/saved_models") -> "StylometryModel":
        """Loads serialized model artifacts."""
        model_p = os.path.join(save_dir, "model.pkl")
        cal_p = os.path.join(save_dir, "calibrator.pkl")
        scaler_p = os.path.join(save_dir, "scaler.pkl")
        ext_p = os.path.join(save_dir, "extractor.pkl")
        cfg_p = os.path.join(save_dir, "feature_config.json")

        if os.path.exists(model_p):
            self.classifier = joblib.load(model_p)
        if os.path.exists(cal_p):
            self.calibrator = joblib.load(cal_p)
        if os.path.exists(scaler_p):
            self.scaler = joblib.load(scaler_p)
        if os.path.exists(ext_p):
            self.extractor = joblib.load(ext_p)
        if os.path.exists(cfg_p):
            with open(cfg_p, "r") as f:
                cfg = json.load(f)
                self.metrics = cfg.get("metrics", {})
        return self
