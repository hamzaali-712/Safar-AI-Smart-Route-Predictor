"""
Safar AI — Blockage Prediction Inference
Loads trained XGBoost model and predicts congestion probability.
"""

import numpy as np
import joblib
from pathlib import Path
from utils.helpers import is_rush_hour, is_weekend, get_weather_risk

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "blockage_model.joblib"
ENCODER_PATH = MODEL_DIR / "label_encoders.joblib"

_model = None
_encoders = None


def _load_model():
    """Load model and encoders, train if not exists."""
    global _model, _encoders
    
    if _model is not None:
        return
    
    if not MODEL_PATH.exists():
        from ml.train_blockage import train_model
        train_model()
    
    _model = joblib.load(MODEL_PATH)
    _encoders = joblib.load(ENCODER_PATH)


def predict_blockage(hour, day_of_week, month, distance_km, zone="urban", road_type="urban"):
    """
    Predict blockage/congestion probability for given conditions.
    Returns float 0.0 - 1.0 (probability of blockage).
    """
    _load_model()
    
    # Encode categoricals
    try:
        zone_encoded = _encoders["zone"].transform([zone])[0]
    except (ValueError, KeyError):
        zone_encoded = 0
    
    try:
        road_encoded = _encoders["road_type"].transform([road_type])[0]
    except (ValueError, KeyError):
        road_encoded = 0
    
    features = np.array([[
        hour, day_of_week, month,
        int(is_weekend(day_of_week)),
        int(is_rush_hour(hour)),
        zone_encoded, road_encoded,
        distance_km,
        get_weather_risk(month)
    ]])
    
    # Get probability of blockage (class 1)
    proba = _model.predict_proba(features)[0]
    blockage_prob = proba[1] if len(proba) > 1 else proba[0]
    
    return round(float(blockage_prob), 3)
