from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Kestrel Home | Returns Risk",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
    .block-container {max-width: 1250px; padding-top: 1.5rem;}
    .hero {padding: 1.4rem 1.6rem; border: 1px solid #e6e9ef; border-radius: 16px; background: linear-gradient(135deg,#f8fafc,#eef5ff); margin-bottom: 1rem;}
    .hero h1 {margin:0; font-size:2rem;}
    .hero p {margin:.35rem 0 0; color:#5b6472;}
    .risk-card {padding:1.1rem 1.25rem; border:1px solid #e6e9ef; border-radius:14px; background:#fff;}
    .risk-score {font-size:2.8rem; font-weight:750; line-height:1;}
    .muted {color:#6b7280; font-size:.9rem;}
    .reason {padding:.7rem .8rem; border-left:4px solid #2563eb; background:#f8fafc; border-radius:8px; margin:.45rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_API = os.getenv("KESTREL_API_URL", "http://127.0.0.1:8000")

@st.cache_data(show_spinner=False)
def load_example():
    path = os.path.join(ROOT, "examples", "predict.json")
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def api_get(path: str, base_url: str):
    r = requests.get(base_url.rstrip("/") + path, timeout=5)
    r.raise_for_status()
    return r.json()


def api_predict(payload: dict, base_url: str):
    r = requests.post(base_url.rstrip("/") + "/predict", json=payload, timeout=15)
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(detail)
    return r.json()


def pct(x):
    return f"{x*100:.1f}%"

st.markdown(
    """
    <div class="hero">
      <h1>🏠 Kestrel Home — Returns Risk</h1>
      <p>Pre-dispatch risk screening for D2C and partner-outlet orders. The screen calls the FastAPI scoring endpoint; it does not run a separate model.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Service status")
    api_url = DEFAULT_API
    if st.button("Check scoring service", use_container_width=True):
        try:
            health = api_get("/health", api_url)
            st.success(f"Scoring service online · {health.get('features','?')} features")
        except Exception as exc:
            st.error(f"Scoring service unavailable: {exc}")
    st.caption("FastAPI runs privately on port 8000 as the scoring backend. This Streamlit screen is the only user-facing interface.")
    st.divider()
    st.caption("Policy benchmark")
    st.metric("Return cost", "₹1,150")
    st.metric("Confirmation call", "₹45")
    st.metric("Pilot prevention", "35%")
    st.caption("The 11.18% call benchmark is derived from the supplied policy economics and is not a model accuracy threshold.")

example = load_example()

with st.form("order_form"):
    st.subheader("1. Enter a dispatch-time order")
    if st.form_submit_button("Load example", use_container_width=False):
        st.session_state["load_example"] = True

    if st.session_state.get("load_example") and example:
        defaults = example
    else:
        defaults = {}

    c1, c2, c3 = st.columns(3)
    with c1:
        order_id = st.text_input("Order ID", value=str(defaults.get("order_id", "DEMO-10001")))
        order_placed_at = st.text_input("Order placed at (IST)", value=str(defaults.get("order_placed_at", "2025-09-25 14:30:00")))
        customer_id = st.text_input("Customer ID", value=str(defaults.get("customer_id", "")))
        sku = st.text_input("SKU", value=str(defaults.get("sku", "")))
    with c2:
        sales_channel = st.selectbox("Sales channel", ["app", "web", "marketplace", "partner_outlet"], index=["app","web","marketplace","partner_outlet"].index(defaults.get("sales_channel","web")))
        payment_mode = st.selectbox("Payment mode", ["prepaid_upi", "prepaid_card", "cod", "emi"], index=["prepaid_upi","prepaid_card","cod","emi"].index(defaults.get("payment_mode","prepaid_card")))
        discount_pct = st.number_input("Discount %", 0.0, 100.0, float(defaults.get("discount_pct", 0)))
        qty = st.number_input("Quantity", 1, 100, int(defaults.get("qty", 1)))
        order_value_inr = st.number_input("Order value (₹)", 0.0, 1000000.0, float(defaults.get("order_value_inr", 5000)))
    with c3:
        promised_delivery_days = st.number_input("Promised delivery days", 0, 60, int(defaults.get("promised_delivery_days", 4)))
        delivery_pincode = st.number_input("Delivery pincode", 0, 999999, int(defaults.get("delivery_pincode", 411001)))
        is_gift = st.selectbox("Gift order", ["N", "Y"], index=["N","Y"].index(defaults.get("is_gift","N")))
        prior_orders = st.number_input("Customer prior orders", 0, 1000, int(defaults.get("customer_prior_orders", 0)))
        prior_returns = st.number_input("Customer prior returns", 0, 1000, int(defaults.get("customer_prior_returns", 0)))
    delivery_note = st.text_area("Delivery note", value=str(defaults.get("delivery_note", "")), height=90)
    source = st.selectbox("Source", ["crm", "partner_feed"], index=["crm","partner_feed"].index(defaults.get("source","crm")))
    submitted = st.form_submit_button("🔎 Score return risk", type="primary", use_container_width=True)

if submitted:
    payload = {
        "order_id": order_id,
        "order_placed_at": order_placed_at,
        "customer_id": customer_id,
        "sku": sku,
        "sales_channel": sales_channel,
        "payment_mode": payment_mode,
        "discount_pct": discount_pct,
        "qty": qty,
        "order_value_inr": order_value_inr,
        "promised_delivery_days": promised_delivery_days,
        "delivery_pincode": delivery_pincode,
        "is_gift": is_gift,
        "customer_prior_orders": prior_orders,
        "customer_prior_returns": prior_returns,
        "delivery_note": delivery_note,
        "source": source,
    }
    with st.spinner("Calling Kestrel scoring API…"):
        try:
            result = api_predict(payload, api_url)
            st.session_state["result"] = result
        except Exception as exc:
            st.error(f"Prediction failed: {exc}")
            st.info("Start the API with: `uvicorn app.main:app --reload --port 8000`")

result = st.session_state.get("result")
if result:
    score = float(result["return_risk_score"])
    band = result.get("risk_band", "standard")
    action = result.get("action", "")
    band_label = {"high":"HIGH RISK", "call":"CALL CANDIDATE", "standard":"STANDARD FLOW"}.get(band, band.upper())

    st.divider()
    st.subheader("2. Decision")
    a, b, c, d = st.columns(4)
    with a:
        st.metric("Return-risk score", pct(score))
    with b:
        st.metric("Risk band", band_label)
    with c:
        st.metric("CatBoost", pct(result["component_scores"]["catboost"]))
    with d:
        st.metric("Logistic regression", pct(result["component_scores"]["logistic_regression"]))

    st.progress(min(max(score, 0.0), 1.0), text=f"Model score: {score:.1%}")
    if band == "high":
        st.error(f"**{action}**")
    elif band == "call":
        st.warning(f"**{action}**")
    else:
        st.success(f"**{action}**")

    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("3. Why the model is flagging this order")
        reasons = result.get("reasons", [])
        if not reasons:
            st.info("No strong individual feature contribution was returned.")
        for r in reasons:
            direction = "increases" if r.get("impact", 0) > 0 else "reduces"
            st.markdown(
                f'<div class="reason"><b>{r.get("feature","Feature")}</b><br>{r.get("text", "This feature " + direction + " risk.")}</div>',
                unsafe_allow_html=True,
            )
    with right:
        st.subheader("4. Operational guardrails")
        p = result.get("policy", {})
        st.write(f"**Call benchmark:** {p.get('call_break_even_probability', 0):.2%}")
        st.write(f"**Manual-review threshold:** {result.get('return_risk_score',0):.2%} is evaluated against the configured high-risk threshold.")
        st.write(f"**Return cost:** ₹{p.get('return_cost_inr', 1150):,.0f}")
        st.write(f"**Confirmation call:** ₹{p.get('confirmation_call_cost_inr', 45):,.0f}")
        st.caption(result.get("caveat", ""))

st.divider()
st.caption("Kestrel Home Returns Risk v2 · Streamlit is the presentation layer; scoring is performed by the FastAPI endpoint.")
