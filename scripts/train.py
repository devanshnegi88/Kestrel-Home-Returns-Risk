from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.modeling import (
    ROOT,
    CAT_COLUMNS,
    dedupe_historical,
    fit_catboost,
    load_tables,
    make_features,
    merge_refs,
    prepare_linear_pipeline,
    predict_dataframe,
)


CALL_COST = 45.0
RETURN_COST = 1150.0
RETURN_PREVENTION = 0.35
CALL_BREAK_EVEN = CALL_COST / (RETURN_COST * RETURN_PREVENTION)
REVIEW_THRESHOLD = 0.50
BLEND_CAT = 0.50
BLEND_LOG = 0.50


def grouped_time_split(df: pd.DataFrame, train_fraction: float = 0.80):
    x = df.copy()
    x["_dt"] = pd.to_datetime(x["order_placed_at"], errors="coerce")
    order_dates = x.groupby("order_id")["_dt"].min().sort_values()
    cut = order_dates.iloc[int(len(order_dates) * train_fraction)]
    train = x[x["_dt"] < cut].drop(columns="_dt")
    valid = x[x["_dt"] >= cut].drop(columns="_dt")
    return train, valid, str(cut)


def metrics_at_threshold(y, p, threshold: float) -> dict:
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "threshold": threshold,
        "accuracy": accuracy_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
    }


def business_at_threshold(y, p, threshold: float) -> dict:
    called = p >= threshold
    called_n = int(called.sum())
    observed_returns = int(y[called].sum())
    saved = observed_returns * RETURN_PREVENTION * RETURN_COST
    calls = called_n * CALL_COST
    return {
        "threshold": threshold,
        "orders_flagged": called_n,
        "observed_returns_in_flagged_set": observed_returns,
        "estimated_returns_prevented": observed_returns * RETURN_PREVENTION,
        "gross_return_cost_avoided_inr": saved,
        "call_cost_inr": calls,
        "net_value_inr": saved - calls,
        "observed_return_rate_in_flagged_set": (observed_returns / called_n) if called_n else 0.0,
    }


def main():
    train_raw, test_raw, customers, products = load_tables()
    merged = merge_refs(train_raw, customers, products)
    test_merged = merge_refs(test_raw, customers, products)

    # Remove known partner-feed duplicate reimports for training/validation.
    history = dedupe_historical(merged)
    fit, valid, split_at = grouped_time_split(history, 0.80)

    X_fit = make_features(fit)
    X_valid = make_features(valid)
    y_fit = fit["returned"].astype(int)
    y_valid = valid["returned"].astype(int)

    # Model component 1: CatBoost handles the mixed categorical/numeric structure.
    cat_model, cat_columns = fit_catboost(
        X_fit,
        y_fit,
        X_valid,
        y_valid,
        iterations=400,
    )
    p_cat = cat_model.predict_proba(X_valid[cat_model.feature_names_])[:, 1]

    # Model component 2: regularized linear model provides a complementary view.
    linear = prepare_linear_pipeline(X_fit)
    linear.fit(X_fit, y_fit)
    p_lin = linear.predict_proba(X_valid)[:, 1]

    p_blend = BLEND_CAT * p_cat + BLEND_LOG * p_lin

    baseline = float(max(y_valid.mean(), 1 - y_valid.mean()))
    component_metrics = {
        "catboost": {
            "accuracy_at_0.50": float(accuracy_score(y_valid, p_cat >= 0.50)),
            "precision_at_0.50": float(precision_score(y_valid, p_cat >= 0.50, zero_division=0)),
            "recall_at_0.50": float(recall_score(y_valid, p_cat >= 0.50, zero_division=0)),
            "f1_at_0.50": float(f1_score(y_valid, p_cat >= 0.50, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_valid, p_cat)),
            "pr_auc": float(average_precision_score(y_valid, p_cat)),
            "brier": float(brier_score_loss(y_valid, p_cat)),
        },
        "logistic_regression": {
            "accuracy_at_0.50": float(accuracy_score(y_valid, p_lin >= 0.50)),
            "precision_at_0.50": float(precision_score(y_valid, p_lin >= 0.50, zero_division=0)),
            "recall_at_0.50": float(recall_score(y_valid, p_lin >= 0.50, zero_division=0)),
            "f1_at_0.50": float(f1_score(y_valid, p_lin >= 0.50, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_valid, p_lin)),
            "pr_auc": float(average_precision_score(y_valid, p_lin)),
            "brier": float(brier_score_loss(y_valid, p_lin)),
        },
        "blend": {
            "accuracy_at_0.50": float(accuracy_score(y_valid, p_blend >= 0.50)),
            "precision_at_0.50": float(precision_score(y_valid, p_blend >= 0.50, zero_division=0)),
            "recall_at_0.50": float(recall_score(y_valid, p_blend >= 0.50, zero_division=0)),
            "f1_at_0.50": float(f1_score(y_valid, p_blend >= 0.50, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_valid, p_blend)),
            "pr_auc": float(average_precision_score(y_valid, p_blend)),
            "brier": float(brier_score_loss(y_valid, p_blend)),
        },
    }
    thresholds = [0.112, 0.20, 0.30, 0.40, 0.50]
    threshold_metrics = [metrics_at_threshold(y_valid, p_blend, t) for t in thresholds]
    business = [business_at_threshold(y_valid.to_numpy(), p_blend, t) for t in [CALL_BREAK_EVEN, 0.20, 0.30, 0.40, 0.50]]

    # Find the best observed accuracy threshold, explicitly labelled as retrospective
    # validation-only and not used as an operational hold rule.
    grid = np.linspace(0.02, 0.98, 193)
    grid_acc = [accuracy_score(y_valid, p_blend >= t) for t in grid]
    best_i = int(np.argmax(grid_acc))
    best_acc_threshold = float(grid[best_i])

    report = {
        "data": {
            "train_rows_raw": int(len(train_raw)),
            "historical_unique_orders": int(history.order_id.nunique()),
            "historical_duplicate_rows_removed": int(len(merged) - len(history)),
            "test_rows": int(len(test_raw)),
            "return_rate_raw": float(train_raw.returned.mean()),
            "return_rate_unique_history": float(history.returned.mean()),
            "validation_cut": split_at,
            "fit_rows": int(len(fit)),
            "validation_rows": int(len(valid)),
        },
        "leakage_audit": {
            "excluded": ["pickup_scheduled_at", "last_service_event_type"],
            "reason": "Historical returned rows contain reverse-pickup service information; these fields can occur after a return starts and are unavailable for a clean dispatch-time prediction.",
            "raw_date_fields_removed": ["order_placed_at", "signup_date", "launch_date"],
            "target_removed": ["returned"],
        },
        "model": {
            "type": "50/50 probability blend of CatBoost and regularized Logistic Regression",
            "catboost_iterations": int(cat_model.tree_count_),
            "catboost_depth": 7,
            "logistic_C": 0.2,
            "blend_weight_catboost": BLEND_CAT,
            "blend_weight_logistic": BLEND_LOG,
            "feature_count": int(X_fit.shape[1]),
        },
        "component_metrics": component_metrics,
        "overall": {
            "accuracy_at_0.50": float(accuracy_score(y_valid, p_blend >= 0.50)),
            "precision_at_0.50": float(precision_score(y_valid, p_blend >= 0.50, zero_division=0)),
            "recall_at_0.50": float(recall_score(y_valid, p_blend >= 0.50, zero_division=0)),
            "f1_at_0.50": float(f1_score(y_valid, p_blend >= 0.50, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_valid, p_blend)),
            "pr_auc": float(average_precision_score(y_valid, p_blend)),
            "brier": float(brier_score_loss(y_valid, p_blend)),
            "majority_baseline_accuracy": baseline,
            "best_validation_accuracy": float(grid_acc[best_i]),
            "best_validation_accuracy_threshold": best_acc_threshold,
        },
        "threshold_metrics": threshold_metrics,
        "business_thresholds": business,
    }

    # Final fit on all unique labelled history.
    X_all = make_features(history)
    y_all = history["returned"].astype(int)
    cat_final, cat_columns = fit_catboost(X_all, y_all, iterations=int(cat_model.tree_count_))
    linear_final = prepare_linear_pipeline(X_all)
    linear_final.fit(X_all, y_all)

    cat_final.save_model(str(ROOT / "model" / "kestrel_catboost.cbm"))
    joblib.dump(linear_final, ROOT / "model" / "kestrel_logistic.joblib", compress=3)

    metadata = {
        "feature_columns": list(X_all.columns),
        "cat_columns": cat_columns,
        "blend_weight_catboost": BLEND_CAT,
        "blend_weight_logistic": BLEND_LOG,
        "risk_review_threshold": REVIEW_THRESHOLD,
        "call_break_even_probability": CALL_BREAK_EVEN,
        "leakage_columns_excluded": ["pickup_scheduled_at", "last_service_event_type"],
        "training_history_is_deduped_by_order_id": True,
        "canonical_duplicate_source": "crm",
        "validation_split": "unique-order chronological 80/20",
        "score_definition": "50/50 average of CatBoost and Logistic Regression predicted probabilities",
        "score_caveat": "Validated as a ranking score; probability calibration should be monitored post-deployment.",
    }
    (ROOT / "model" / "metadata.json").write_text(json.dumps(metadata, indent=2))

    # Exact sample shape/order.
    X_test = make_features(test_merged)
    scores = predict_dataframe(X_test, cat_final, linear_final, metadata)
    sample = pd.read_csv(ROOT / "data" / "sample_submission.csv")
    score_map = dict(zip(test_raw["order_id"], scores))
    predictions = sample[["order_id"]].copy()
    predictions["score"] = predictions["order_id"].map(score_map)
    if predictions["score"].isna().any():
        raise RuntimeError("Submission IDs did not fully map to model scores")
    predictions.to_csv(ROOT / "predictions.csv", index=False)

    (ROOT / "docs" / "validation.json").write_text(json.dumps(report, indent=2))

    # Threshold table for humans.
    pd.DataFrame(business).to_csv(ROOT / "docs" / "business_thresholds.csv", index=False)

    # Top global features from CatBoost component.
    fi = sorted(
        zip(X_all.columns, cat_final.get_feature_importance()),
        key=lambda z: z[1],
        reverse=True,
    )[:25]
    (ROOT / "docs" / "top_features.txt").write_text(
        "\n".join(f"{name}\t{score:.4f}" for name, score in fi)
    )

    print(json.dumps(report["overall"], indent=2))
    print("Predictions:", predictions.shape)
    print("Score range:", float(predictions.score.min()), float(predictions.score.max()))


if __name__ == "__main__":
    main()
