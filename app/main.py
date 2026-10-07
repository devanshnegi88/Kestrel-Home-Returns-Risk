from __future__ import annotations

from pathlib import Path
import json

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .modeling import (
    load_artifacts,
    load_tables,
    merge_refs,
    make_features,
    catboost_reasons,
    logistic_reasons,
)

ROOT = Path(__file__).resolve().parents[1]
CAT_MODEL, LINEAR_MODEL, META = load_artifacts()
_, _, CUSTOMERS, PRODUCTS = load_tables()

app = FastAPI(
    title="Kestrel Home Returns Risk",
    description="Leakage-safe pre-dispatch return-risk scoring with operational reasons.",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


class Order(BaseModel):
    order_id: str | None = None
    order_placed_at: str = Field(min_length=10)
    customer_id: str
    sku: str
    sales_channel: str
    payment_mode: str
    discount_pct: float = Field(ge=0, le=100)
    qty: int = Field(ge=1)
    order_value_inr: float = Field(ge=0)
    promised_delivery_days: int = Field(ge=0)
    delivery_pincode: int = Field(ge=0, le=999999)
    is_gift: str
    customer_prior_orders: int = Field(ge=0)
    customer_prior_returns: int = Field(ge=0)
    delivery_note: str | None = None
    source: str = "crm"


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": "CatBoost + Logistic Regression blend",
        "features": len(META["feature_columns"]),
        "version": app.version,
    }


@app.get("/")
def home():
    return {"service": "Kestrel Returns Risk API", "status": "ok", "ui": "Streamlit on port 8501"}


@app.get("/metadata")
def metadata() -> dict:
    return {
        "call_break_even_probability": META["call_break_even_probability"],
        "risk_review_threshold": META["risk_review_threshold"],
        "blend": {
            "catboost": META["blend_weight_catboost"],
            "logistic_regression": META["blend_weight_logistic"],
        },
    }


@app.post("/predict")
def predict(order: Order) -> dict:
    raw = pd.DataFrame([order.model_dump()])
    try:
        merged = merge_refs(raw, CUSTOMERS, PRODUCTS)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Reference join failed: {exc}") from exc

    if merged["city"].isna().any():
        raise HTTPException(status_code=400, detail="Unknown customer_id; it must exist in customers.csv")
    if merged["family"].isna().any():
        raise HTTPException(status_code=400, detail="Unknown sku; it must exist in products.csv")

    X = make_features(merged)
    X = X[META["feature_columns"]]
    cat_X = X.copy()
    for c in META["cat_columns"]:
        if c in cat_X:
            cat_X[c] = cat_X[c].fillna("MISSING").astype(str)

    p_cat = float(CAT_MODEL.predict_proba(cat_X)[0, 1])
    p_lin = float(LINEAR_MODEL.predict_proba(X)[0, 1])
    score = META["blend_weight_catboost"] * p_cat + META["blend_weight_logistic"] * p_lin

    reasons = catboost_reasons(CAT_MODEL, X, META["cat_columns"], top_n=2)
    reasons += logistic_reasons(LINEAR_MODEL, X, top_n=2)
    reasons = sorted(reasons, key=lambda r: abs(r["impact"]), reverse=True)[:4]

    call_break_even = float(META["call_break_even_probability"])
    review_threshold = float(META["risk_review_threshold"])
    if score >= review_threshold:
        action = "HIGH RISK — manual review before dispatch"
        band = "high"
    elif score >= call_break_even:
        action = "CALL CANDIDATE — confirmation call before dispatch"
        band = "call"
    else:
        action = "STANDARD FLOW"
        band = "standard"

    return {
        "order_id": order.order_id,
        "return_risk_score": round(float(score), 6),
        "risk_band": band,
        "action": action,
        "component_scores": {
            "catboost": round(p_cat, 6),
            "logistic_regression": round(p_lin, 6),
        },
        "reasons": reasons,
        "policy": {
            "call_break_even_probability": round(call_break_even, 6),
            "return_cost_inr": 1150,
            "confirmation_call_cost_inr": 45,
            "pilot_return_prevention_rate": 0.35,
            "hold_over_24h_cancellation_rate": 0.12,
        },
        "caveat": "The score is validated as a risk ranking. Treat it as probability-like, not a guarantee; operational thresholds should be monitored after deployment.",
    }
