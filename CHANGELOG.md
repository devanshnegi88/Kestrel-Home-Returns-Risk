# Changelog

## Variant A - improved package

- Replaced the single-model scorer with a 50/50 CatBoost + Logistic Regression blend.
- Made validation unique-order and chronological.
- Deduplicated partner-feed reimports before fitting.
- Added stronger delivery-note, pincode and ratio/tenure features.
- Added business-threshold table and validation economics.
- Added API component scores and multi-model reasons.
- Added request validation, `/metadata`, and a polished browser UI.
- Added end-to-end API tests.
- Corrected inconsistent precision/F1 figures from the prior memo.
