# Model card - Kestrel Returns Risk

## Intended use

Pre-dispatch ranking of orders by likelihood of return. The main operational use is prioritizing confirmation calls and manual review.

## Not intended for

- Treating the score as a guaranteed outcome.
- Using service/pickup fields generated after a return starts.
- Automatically holding an order for more than 24 hours without measuring the cancellation economics.
- Publishing the supplied customer/operational data outside the engagement team.

## Inputs used

Order placement details, customer history supplied before the order, product attributes, commercial fields, source/channel/payment information, pincode-derived geography, and simple delivery-note indicators.

## Inputs excluded

`pickup_scheduled_at`, `last_service_event_type`, raw timestamps, `returned`, and raw `customer_id`.

## Model

50/50 blend of CatBoost + regularized Logistic Regression.

## Validation

Unique-order chronological 80/20 split. See `validation.md` and `docs/validation.json`.

## Explainability

The API returns employee-readable reasons derived from CatBoost SHAP values and logistic-model feature contributions. The application never asks a generative model to invent reasons.

## Monitoring plan

After deployment, retain order ID, score, action, call outcome, cancellation, return outcome, and final return reason. Review weekly by channel, product family, Shield status, source, and score band. Re-train on new labelled data and re-check calibration before changing thresholds.
