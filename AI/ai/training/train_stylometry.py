"""
PAN Authorship Verification Training Pipeline
SIH26151: Dark Web Threat Actor De-anonymization

Trains and benchmarks multiple candidate stylometric models on PAN 2022 dataset:
1. Logistic Regression
2. Random Forest
3. Gradient Boosting / XGBoost
4. Linear SVM with Platt Calibration

Evaluates on validation split, selects optimal model, calibrates probabilities,
and serializes artifacts for production inference.
"""

import os
import sys
import json
import numpy as np
from datetime import datetime
from ai.preprocessing.pan import PANPreprocessor
from ai.models.stylometry_model import StylometryModel


def run_stylometry_training():
    print("=" * 70)
    print("SIH26151: TRAINING PAN AUTHORSHIP VERIFICATION MODEL")
    print("=" * 70)

    # 1. Load PAN dataset
    print("[1/5] Loading PAN Authorship Verification dataset from 2022/...")
    prep = PANPreprocessor(base_dir="2022")
    splits = prep.load_all_splits()

    train_pairs = splits.get("train", [])
    val_pairs = splits.get("validation", [])
    test_pairs = splits.get("test", [])

    print(f"  Training pairs:   {len(train_pairs)} (Same: {sum(1 for p in train_pairs if p.label==1)}, Diff: {sum(1 for p in train_pairs if p.label==0)})")
    print(f"  Validation pairs: {len(val_pairs)} (Same: {sum(1 for p in val_pairs if p.label==1)}, Diff: {sum(1 for p in val_pairs if p.label==0)})")
    print(f"  Test pairs:       {len(test_pairs)} (Same: {sum(1 for p in test_pairs if p.label==1)}, Diff: {sum(1 for p in test_pairs if p.label==0)})")

    if not train_pairs or not val_pairs:
        raise ValueError("PAN dataset pairs could not be loaded!")

    # 2. Benchmark candidate model architectures
    candidates = ["logistic_regression", "random_forest", "gradient_boosting", "linear_svm"]
    results = {}
    models = {}

    print("\n[2/5] Benchmarking candidate architectures...")
    best_candidate = None
    best_f1 = -1.0

    for candidate in candidates:
        print(f"\n  -> Training candidate: {candidate.upper()}...")
        model = StylometryModel(model_name=candidate)
        metrics = model.fit_and_evaluate(train_pairs, val_pairs, candidate_type=candidate)
        results[candidate] = metrics
        models[candidate] = model

        print(f"     Validation Accuracy: {metrics['accuracy']:.4f}")
        print(f"     Validation F1-Score: {metrics['f1']:.4f}")
        print(f"     Validation ROC-AUC:  {metrics['roc_auc']:.4f}")
        print(f"     Same-Author Acc:     {metrics['same_author_accuracy']:.4f}")
        print(f"     Diff-Author Acc:     {metrics['different_author_accuracy']:.4f}")
        print(f"     Brier Score Loss:    {metrics['brier_score']:.4f}")

        # Choose model based on validation F1 score and calibration balance
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            best_candidate = candidate

    print(f"\n[3/5] Optimal model selected: {best_candidate.upper()} (Val F1: {best_f1:.4f})")
    best_model = models[best_candidate]

    # 3. Evaluate Best Model on Unseen Test Split
    print("\n[4/5] Evaluating selected model on Test Split...")
    test_a = [p.text_a for p in test_pairs]
    test_b = [p.text_b for p in test_pairs]
    test_X = best_model.extractor.extract_batch_pair_features(test_a, test_b)
    test_y = np.array([p.label for p in test_pairs])
    test_X_scaled = best_model.scaler.transform(test_X)

    test_probs = best_model.predict_proba_raw(test_X_scaled)
    test_preds = (test_probs >= 0.5).astype(int)

    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
    test_acc = accuracy_score(test_y, test_preds)
    test_prec = precision_score(test_y, test_preds, zero_division=0)
    test_rec = recall_score(test_y, test_preds, zero_division=0)
    test_f1 = f1_score(test_y, test_preds, zero_division=0)
    test_auc = roc_auc_score(test_y, test_probs)
    test_cm = confusion_matrix(test_y, test_preds).tolist()

    same_mask = (test_y == 1)
    diff_mask = (test_y == 0)
    same_acc = accuracy_score(test_y[same_mask], test_preds[same_mask])
    diff_acc = accuracy_score(test_y[diff_mask], test_preds[diff_mask])

    print("=" * 70)
    print("FINAL TEST SET PERFORMANCE METRICS")
    print("=" * 70)
    print(f"  Test Accuracy:                 {test_acc:.4f}")
    print(f"  Test Precision:                {test_prec:.4f}")
    print(f"  Test Recall:                   {test_rec:.4f}")
    print(f"  Test F1-Score:                 {test_f1:.4f}")
    print(f"  Test ROC-AUC:                  {test_auc:.4f}")
    print(f"  Same-Author Accuracy:          {same_acc:.4f}")
    print(f"  Different-Author Accuracy:     {diff_acc:.4f}")
    print(f"  Confusion Matrix (TN, FP, FN, TP): {test_cm}")
    print("=" * 70)

    # 4. Save trained artifacts
    print("\n[5/5] Saving serialized model artifacts to ai/saved_models/...")
    best_model.save("ai/saved_models")

    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "selected_model": best_candidate,
        "validation_metrics": results[best_candidate],
        "test_metrics": {
            "accuracy": round(float(test_acc), 4),
            "precision": round(float(test_prec), 4),
            "recall": round(float(test_rec), 4),
            "f1": round(float(test_f1), 4),
            "roc_auc": round(float(test_auc), 4),
            "same_author_accuracy": round(float(same_acc), 4),
            "different_author_accuracy": round(float(diff_acc), 4),
            "confusion_matrix": test_cm
        },
        "all_candidates": results
    }

    with open("ai/saved_models/training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Training and evaluation successfully completed.")
    return best_model, summary


if __name__ == "__main__":
    run_stylometry_training()
