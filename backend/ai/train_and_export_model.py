import os
import pandas as pd
import numpy as np
import glob
import joblib
from xgboost import XGBRegressor

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

    df = df.sort_values(by=["hospital_name", "time"])

    df["beds_lag"] = df.groupby("hospital_name")["beds_available"].shift(1).fillna(0)
    df["op_lag"] = df.groupby("hospital_name")["op_rooms_available"].shift(1).fillna(0)

    df["beds_t10"] = df.groupby("hospital_name")["beds_available"].shift(-1).fillna(0)
    df["beds_t60"] = df.groupby("hospital_name")["beds_available"].shift(-6).fillna(0)
    df["op_t10"] = df.groupby("hospital_name")["op_rooms_available"].shift(-1).fillna(0)
    df["op_t60"] = df.groupby("hospital_name")["op_rooms_available"].shift(-6).fillna(0)

    df["hospital_code"] = df["hospital_name"].astype("category").cat.codes
    df["minute"] = df["time"] % 60

    df = df[df["beds_t60"] != 0]

    features = [
        "hospital_code",
        "day_of_week",
        "hour",
        "minute",
        "ktas",
        "beds_lag",
        "op_lag",
    ]

    os.makedirs(model_dir, exist_ok=True)

    model_10 = XGBRegressor(
        n_estimators=500, learning_rate=0.05, max_depth=6, n_jobs=-1, random_state=42
    )
    model_10.fit(df[features], df[["beds_t10", "op_t10"]])
    joblib.dump(
        model_10, os.path.join(model_dir, "after_10_minute_prediction_model.pkl")
    )

    model_60 = XGBRegressor(
        n_estimators=500, learning_rate=0.05, max_depth=6, n_jobs=-1, random_state=42
    )
    model_60.fit(df[features], df[["beds_t60", "op_t60"]])
    joblib.dump(
        model_60, os.path.join(model_dir, "after_60_minute_prediction_model.pkl")
    )

    joblib.dump(
        df[["hospital_name", "hospital_code"]].drop_duplicates(),
        os.path.join(model_dir, "hospital_mapping.pkl"),
    )


if __name__ == "__main__":
    train_and_export()
