# Submission Form - Kestrel Home Returns Risk (Variant A)

## 1. What did you submit?

`predictions.csv`, source code, trained model artifacts, FastAPI service, browser UI, tests, leakage/validation audit, business-threshold analysis, one-page memo, recording script, and this completed form.

## 2. Expected score and why?

The submission contains a continuous **0-1 return-risk score**, with higher values meaning higher predicted return likelihood. I expect it to rank orders meaningfully because the chronological holdout produced **0.778 ROC-AUC** and **0.404 PR-AUC**. The current test file has **2,096 rows** and the prediction file preserves the exact sample order.

I do **not** expect a useful 95% classification-accuracy result. The latest chronological validation reached **89.39% at 0.50** versus **88.48% majority accuracy**, with best retrospective accuracy **89.67% at 0.375**.

## 3. Leakage controls

Excluded: `last_service_event_type`, `pickup_scheduled_at`, raw date strings, `returned`, and raw `customer_id`. `REVERSE_PICKUP` is a downstream return-workflow signal, and `pickup_scheduled_at` is a return logistics field. The API does not ask for those fields.

Historical partner-feed reimports were also de-duplicated by `order_id` before fitting.

## 4. Operational recommendation

Use the model as a **confirmation-call queue** at the policy-derived 11.18% benchmark and a **50% high-risk manual-review band**. In the test snapshot, **663 orders** are in the call queue and **44** are in the high-risk tail.

The policy states that >24h-held orders are cancelled about 12% of the time, but it does not give the rupee cancellation cost. Therefore the project does not claim a defensible automatic hold threshold.

## 5. Validation

Unique-order chronological 80/20 split.

- Accuracy @ 0.50: **89.39%**
- Precision @ 0.50: **78.79%**
- Recall @ 0.50: **10.74%**
- F1 @ 0.50: **18.91%**
- ROC-AUC: **0.778**
- PR-AUC: **0.404**
- Brier: **0.086**
- Majority baseline: **88.48%**

## 6. AI / tools / cost

Built and tested with local Python tooling, CatBoost, scikit-learn, FastAPI and ChatGPT assistance. No paid API key, hosted LLM or per-order inference API is required at runtime. The prediction and reasons are produced locally by the trained models.

## 7. Tried / changed / discarded

- Discarded service/pickup fields because they leak the return workflow.
- Replaced random-style evidence with chronological, unique-order validation.
- Added duplicate-order handling after confirming the partner-feed reimport pattern.
- Added a complementary logistic component to improve ranking/calibration characteristics.
- Separated policy economics from arbitrary classification thresholds.
- Did not manufacture a 95% accuracy claim.

## 8. Clean-machine start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. API example: `examples/predict.json`.
