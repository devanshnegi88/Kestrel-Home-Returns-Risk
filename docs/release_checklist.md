# Release checklist

## Submission

- [x] `predictions.csv` has columns `order_id,score`.
- [x] Row count matches `sample_submission.csv`.
- [x] Submission IDs are unique and preserve sample order.
- [x] Scores are numeric and within 0-1.

## Modeling

- [x] Duplicate order IDs identified and de-duplicated before fitting.
- [x] Chronological, unique-order 80/20 validation used.
- [x] Post-return service/pickup features excluded.
- [x] Model comparison recorded.
- [x] Business threshold separated from arbitrary classification threshold.

## Service

- [x] `/health` returns HTTP 200.
- [x] `/predict` returns score, band, action, component scores and reasons.
- [x] Browser UI calls `/predict`.
- [x] API does not request excluded leakage fields.
- [x] Unknown customer/SKU returns a clear 400 error.

## Tests

- [x] Exact submission format test.
- [x] Model artifact test.
- [x] API health test.
- [x] End-to-end prediction test.

## Documentation

- [x] README with clean-machine start.
- [x] Validation and leakage audit.
- [x] Model comparison.
- [x] One-page business memo.
- [x] Operational decision framework.
- [x] Model card.
- [x] Completed submission form.
- [x] Screen-recording script.
