# Data quality review

## Pack inventory

- `train.csv`: labelled order history.
- `test_unlabelled.csv`: current dispatch snapshot.
- `customers.csv`: customer reference table.
- `products.csv`: SKU/product reference table.
- `sample_submission.csv`: required submission shape.
- `ops-policy.pdf`: operational economics and process rules.
- `email-thread.txt`: stakeholder expectations and constraints.
- `README.txt`: field definitions.

## Checks performed

- Reference joins are validated as many-to-one for customer and product keys.
- Submission IDs are checked against `sample_submission.csv` in exact order.
- Duplicate historical `order_id` values are removed before model fitting because the source note says partner-feed reimports can duplicate orders.
- Duplicate labels were checked; duplicated order IDs have consistent return labels.
- Missing delivery notes are retained through explicit `note_missing`/length features.
- Default pincode `000000` is retained as an explicit feature because the data dictionary defines it as a missing-address/default system value.
- Current test rows have no return label and no reverse-pickup timestamps.
