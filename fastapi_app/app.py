import joblib, uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
from pathlib import Path

model_path = Path(__file__).resolve().parent / "model.pkl"
PKL = joblib.load(model_path)
SCALER = PKL["scaler"]
MODEL  = PKL["model"]
THR    = PKL["threshold"]
VER    = PKL.get("version", "if_v1")



class FeatureItem(BaseModel):
    event_id: int
    hour_of_day: int
    minutes_since_prev: Optional[float] = None
    geo_km_from_prev: Optional[float] = None
    failed_15m: Optional[int] = 0
    is_night: int

class Batch(BaseModel):
    items: List[FeatureItem]

app = FastAPI(title="Login Anomaly Scoring")

def row_to_X(item: FeatureItem):
    vals = [
        item.hour_of_day,
        0.0 if item.minutes_since_prev is None else float(item.minutes_since_prev),
        0.0 if item.geo_km_from_prev is None else float(item.geo_km_from_prev),
        0 if item.failed_15m is None else int(item.failed_15m),
        int(item.is_night),
    ]
    return np.array(vals, dtype=float).reshape(1, -1)

@app.post("/predict")
def predict(b: Batch):
    X = np.vstack([row_to_X(it) for it in b.items])
    Xs = SCALER.transform(X)
    scores = -MODEL.score_samples(Xs)  # higher = more anomalous
    out = []
    for it, s in zip(b.items, scores):
        out.append({
            "event_id": it.event_id,
            "model_version": VER,
            "score": float(s),
            "threshold": float(THR),
            "predicted": int(s >= THR)
        })
    return {"results": out}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
