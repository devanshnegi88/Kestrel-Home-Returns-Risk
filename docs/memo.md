# Kestrel Home - Returns Risk: one-page decision memo

**To:** Ritu Deshpande, Head of D2C Operations  
**Decision:** Deploy as a **returns-risk ranking + confirmation-call queue**. Do **not** automate a >24h dispatch hold yet.

## The decision

The model is strong enough to prioritize attention before dispatch, but the supplied evidence does not support the requested 95% useful accuracy target or a fully automatic dispatch hold. Start with a controlled call/review workflow and capture outcomes.

## What the data says

The labelled history has **11,155 rows and 10,504 unique orders**. The **651 duplicate rows** are partner-feed reimports and are de-duplicated before training. Unique-order return rate is **11.42%**. The current dispatch snapshot contains **2,096 orders**.

The final model is a **50/50 CatBoost + regularized Logistic Regression blend** using only pre-dispatch information. `last_service_event_type` and `pickup_scheduled_at` are excluded because they can reveal the return workflow itself.

On a unique-order chronological 80/20 holdout: **89.39% accuracy at 0.50, 78.79% precision, 10.74% recall, 18.91% F1, 0.778 ROC-AUC, 0.404 PR-AUC, and 0.086 Brier**. Majority baseline is **88.48% accuracy**. Best retrospective accuracy is **89.67% at threshold 0.375**. The 95% target is not honestly achieved.

## Rupees

The policy gives **₹1,150 per return**, **₹45 per confirmation call**, and about **35% prevention** on called orders. Break-even is **11.18%**. On validation, the 11.18% queue contained **650 orders**, with a **24.8% observed return rate** and estimated **₹35,552 net value** under the 35% prevention assumption.

For the unlabeled test snapshot, **663 orders score at/above 11.18%** and **44 score at/above 50%**.

## What to do next week

1. Put the **663 test orders** above the 11.18% benchmark into the confirmation-call workflow.
2. Keep the **44 highest-risk orders** in a manual-review queue.
3. Log call outcome, cancellation, return outcome and final return reason.
4. Review performance by channel, product family, Shield status, source and score band.
5. Quantify the rupee cost of >24h hold cancellations before creating an automatic hold policy.
6. Re-train and re-check calibration on the next labelled batch.

**Bottom line:** use the model to spend operational attention where risk is concentrated; do not claim that it meets the 95% board bar when the leakage-safe evidence does not show that.
