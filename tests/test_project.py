from pathlib import Path
import sys
import pandas as pd
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_predictions_shape_and_ids():
    p = pd.read_csv(ROOT / "predictions.csv")
    s = pd.read_csv(ROOT / "data/sample_submission.csv")
    assert list(p.columns) == ["order_id", "score"]
    assert len(p) == len(s)
    assert p.order_id.tolist() == s.order_id.tolist()
    assert p.score.between(0, 1).all()
    assert p.order_id.is_unique


def test_model_artifacts():
    assert (ROOT / "model/kestrel_catboost.cbm").exists()
    assert (ROOT / "model/kestrel_logistic.joblib").exists()
    assert (ROOT / "model/metadata.json").exists()


def test_api_health_and_prediction():
    from app.main import app

    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    row = pd.read_csv(ROOT / "data/test_unlabelled.csv").iloc[0].to_dict()
    # Convert NaN values to None for JSON.
    row = {k: (None if pd.isna(v) else v) for k, v in row.items()}
    row.pop("last_service_event_type", None)
    row.pop("pickup_scheduled_at", None)
    resp = client.post("/predict", json=row)
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["return_risk_score"] <= 1
    assert body["risk_band"] in {"standard", "call", "high"}
    assert 1 <= len(body["reasons"]) <= 4
