import os
import pandas as pd
import numpy as np
import glob
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, "..", "data", "raw", "hospital_dynamic_data")
model_dir = os.path.join(current_dir, "models")


def train_and_export():
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not files:
        return

    list = [pd.read_csv(f) for f in files]
    df = pd.concat(list, ignore_index=True)
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

    df["hospital_code"] = df["hospital_name"].astype("category").cat.codes
    df["minute"] = df["time"] % 60

    features = ["hospital_code", "day_of_week", "hour", "minute", "ktas"]
    targets = ["beds_available", "op_rooms_available"]

    X = df[features]
    y = df[targets]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(n_estimators=100, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("=== Model Performance Validation ===")
    print(f"MAE : {mean_absolute_error(y_test, y_pred):.2f}")
    print(f"R2 Score : {r2_score(y_test, y_pred):.2f}")

    model.fit(X, y)

    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(model, os.path.join(model_dir, "hospital_congestion_prediction.pkl"))

    mapping = df[["hospital_name", "hospital_code"]].drop_duplicates()
    joblib.dump(mapping, os.path.join(model_dir, "hospital_mapping.pkl"))


if __name__ == "__main__":
    train_and_export()
