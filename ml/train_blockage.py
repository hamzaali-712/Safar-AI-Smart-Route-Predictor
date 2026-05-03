"""
Safar AI — Synthetic Data Generator & XGBoost Blockage Model Trainer
Generates realistic Pakistan traffic patterns and trains a congestion predictor.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "blockage_model.joblib"
ENCODER_PATH = MODEL_DIR / "label_encoders.joblib"


def generate_synthetic_data(n_samples=5000):
    """Generate synthetic Pakistan traffic data for training."""
    np.random.seed(42)
    
    hours = np.random.randint(0, 24, n_samples)
    days = np.random.randint(0, 7, n_samples)
    months = np.random.randint(1, 13, n_samples)
    
    is_weekend = np.isin(days, [4, 5, 6]).astype(int)
    is_rush = np.isin(hours, [7, 8, 9, 17, 18, 19]).astype(int)
    
    zones = np.random.choice(["urban", "semi_urban", "rural"], n_samples, p=[0.5, 0.3, 0.2])
    road_types = np.random.choice(["highway", "motorway", "urban", "rural"], n_samples, p=[0.3, 0.25, 0.35, 0.1])
    distances = np.random.exponential(100, n_samples).clip(5, 800)
    
    # Weather risk by month
    weather_map = {1:0.5, 2:0.3, 3:0.2, 4:0.2, 5:0.3, 6:0.4, 7:0.8, 8:0.85, 9:0.6, 10:0.2, 11:0.3, 12:0.55}
    weather_risk = np.array([weather_map[m] for m in months])
    
    # Generate blockage labels based on realistic patterns
    blockage_prob = np.zeros(n_samples)
    
    # Rush hour in urban areas = high blockage
    blockage_prob += is_rush * 0.3
    blockage_prob += (zones == "urban").astype(float) * 0.15
    blockage_prob += weather_risk * 0.2
    
    # Friday prayer time boost
    friday_prayer = ((days == 4) & (hours >= 12) & (hours <= 14)).astype(float)
    blockage_prob += friday_prayer * 0.25
    
    # Motorways are safer
    blockage_prob -= (road_types == "motorway").astype(float) * 0.15
    
    # Night time = less blockage
    night = ((hours >= 22) | (hours <= 4)).astype(float)
    blockage_prob -= night * 0.15
    
    # Weekend slightly less traffic
    blockage_prob -= is_weekend * 0.05
    
    # Add noise
    blockage_prob += np.random.normal(0, 0.08, n_samples)
    blockage_prob = np.clip(blockage_prob, 0, 1)
    
    # Convert to binary (blocked / not blocked) with threshold
    labels = (blockage_prob > 0.35).astype(int)
    
    df = pd.DataFrame({
        "hour": hours, "day_of_week": days, "month": months,
        "is_weekend": is_weekend, "is_rush_hour": is_rush,
        "zone": zones, "road_type": road_types,
        "distance_km": np.round(distances, 1),
        "weather_risk": np.round(weather_risk, 2),
        "blockage": labels
    })
    
    return df


def train_model():
    """Train XGBoost blockage predictor and save to disk."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    df = generate_synthetic_data(5000)
    
    # Encode categoricals
    encoders = {}
    for col in ["zone", "road_type"]:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le
    
    X = df.drop("blockage", axis=1)
    y = df["blockage"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = XGBClassifier(
        n_estimators=100, max_depth=5, learning_rate=0.1,
        use_label_encoder=False, eval_metric="logloss",
        random_state=42
    )
    model.fit(X_train, y_train)
    
    accuracy = model.score(X_test, y_test)
    
    joblib.dump(model, MODEL_PATH)
    joblib.dump(encoders, ENCODER_PATH)
    
    return accuracy


if __name__ == "__main__":
    acc = train_model()
    print(f"Model trained with accuracy: {acc:.2%}")
