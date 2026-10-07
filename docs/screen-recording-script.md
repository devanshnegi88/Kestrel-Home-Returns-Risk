# Kestrel Home — 3-minute recording script

## 0:00–0:20 — What was built
“I built a pre-dispatch returns-risk system for Kestrel Home. The key constraint was avoiding post-return leakage, so I excluded reverse-pickup/service workflow fields from the predictive feature set.”

## 0:20–0:55 — Start the system
Show two terminals:

```bash
uvicorn app.main:app --reload --port 8000
streamlit run app/streamlit_app.py
```

Open Streamlit and click **Check API**.

## 0:55–1:45 — Live scoring
Enter or load the example order and click **Score return risk**.

Show:
- return-risk score
- CatBoost and Logistic Regression component scores
- risk band
- recommended action
- model-derived reasons

Say: “The Streamlit screen is only the operator layer. It sends the order to FastAPI `/predict`, which performs the same production scoring path.”

## 1:45–2:15 — Business decision
Show the policy figures in the UI.

Say: “The policy says a return costs ₹1,150 and a confirmation call costs ₹45. The supplied pilot prevented about 35% of otherwise-occurring returns. I therefore use the model as a ranking and decision-support tool, rather than claiming that every high score is guaranteed to return.”

## 2:15–2:45 — Evidence
Show `validation.md` and `docs/model_comparison.md`.

Say: “The validation is chronological. The 95% accuracy request is not met by a defensible leakage-safe model, so I report that honestly. The model improves on the majority baseline and gives a useful ranking signal.”

## 2:45–3:00 — Submission
Show `predictions.csv`, `submission-form.md`, and the project README.

Say: “The package contains the test predictions, reproducible training code, API, Streamlit UI, validation evidence, memo, submission form, and clean-machine startup instructions.”
