# Kestrel Home - Returns Risk: validation and leakage audit

## 1. Evaluation design

The raw history contains **11,155 rows** but only **10,504 unique order IDs**. The data pack says partner-outlet orders can be re-imported from the partner feed, so **651 duplicate rows were removed** before modeling. The CRM copy is retained as the canonical row for duplicated order IDs.

Validation is **chronological and group-safe**: unique orders are sorted by order timestamp, with the first 80% used for fitting and the latest 20% held out. No order ID is split across train and validation.

- Fit rows: **8,403**
- Validation rows: **2,101**
- Validation starts at: **2026-04-02 00:23:00**
- Raw-row return rate: **11.36%**
- Unique-order return rate: **11.42%**

## 2. Leakage audit

The test file is the warehouse snapshot at dispatch. The policy describes reverse pickup as part of the returns process, and the historical export contains `REVERSE_PICKUP` on returned orders. These fields would therefore give the model information unavailable for a clean pre-dispatch prediction.

| Field | Treatment | Reason |
| --- | --- | --- |
| `last_service_event_type` | **Excluded** | Can contain `REVERSE_PICKUP`, a direct return-workflow proxy. |
| `pickup_scheduled_at` | **Excluded** | Reverse-pickup booking is downstream of the return workflow. |
| `returned` | **Excluded** | Target only. |
| Raw date strings | **Excluded after derivation** | Converted into calendar/tenure features rather than used as raw timestamps. |
| `customer_id` | **Excluded** | Avoids memorizing customer identity; provided prior-order/return history is used instead. |

The production API does not request the two leakage fields.

## 3. Feature design

Features are limited to information available at dispatch and include customer prior-order/return history; SKU/family/model/warranty/product age; sales channel, payment, source and Shield status; discount, order value, price/list-price relationship, quantity and promised delivery window; default-pincode and coarse geography signals; delivery-note presence/length/keywords; order time/day/month; and customer/product tenure.

## 4. Final model

The final scorer is a **50/50 probability blend** of CatBoost and regularized Logistic Regression. The feature count is **70**.

The blend was selected during model comparison because it improved rare-class ranking and Brier score characteristics relative to a single model on the chronological holdout.

## 5. Validation results

At score threshold 0.50:

| Metric | Result |
| --- | ---: |
| Accuracy | **89.39%** |
| Precision | **78.79%** |
| Recall | **10.74%** |
| F1 | **18.91%** |
| ROC-AUC | **0.778** |
| PR-AUC | **0.404** |
| Brier score | **0.086** |
| Majority baseline accuracy | **88.48%** |

Best retrospective validation accuracy: **89.67%** at threshold **0.375**. This is evidence only, not an operational hold rule.

### The 95% board target

The requested 95% accuracy bar is **not claimed as achieved by a useful leakage-safe classifier**. With returns at about 11-12%, accuracy is heavily dominated by the negative class. The package therefore prioritizes ranking quality, rare-class capture, and business economics rather than manufacturing the 95% headline through post-return fields or an extreme threshold.

## 6. Policy economics

The policy gives a **₹45 confirmation-call cost**, **₹1,150 return cost**, and about **35% return prevention** on called orders. Break-even is:

`45 / (1,150 × 0.35) = 11.18%`

Validation economics, using observed flagged-set return rates and the stated 35% prevention assumption:

| Score threshold | Orders flagged | Observed return rate | Gross avoided cost | Call cost | Net value |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 11.2% | 650 | 24.8% | ₹64,802 | ₹29,250 | ₹35,552 |
| 20.0% | 287 | 36.2% | ₹41,860 | ₹12,915 | ₹28,945 |
| 30.0% | 134 | 51.5% | ₹27,772 | ₹6,030 | ₹21,742 |
| 40.0% | 70 | 62.9% | ₹17,710 | ₹3,150 | ₹14,560 |
| 50.0% | 33 | 78.8% | ₹10,465 | ₹1,485 | ₹8,980 |

The 11.18% threshold is a **policy break-even benchmark**, not proof of perfect score calibration. Collect actual call outcomes and returns before treating it as a stable production threshold.

## 7. Test-set output

The submission file contains **2,096** rows in exact sample order.

- Scores at/above 11.18%: **663**
- Scores at/above 50%: **44**
- Minimum score: **0.010**
- Median score: **0.072**
- 95th percentile: **0.332**
- Maximum score: **0.891**

## 8. Limitations

The current test set has no outcome label, so its real-world precision/recall cannot yet be measured. The next labelled batch should be used to monitor score bands, calibration, drift and subgroup performance. The supplied policy gives a ~12% cancellation frequency for >24h holds but does not supply its rupee cost, so no automatic hold threshold is claimed.
