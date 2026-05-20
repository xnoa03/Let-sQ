import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from xgboost import plot_importance

model_path_10 = os.path.join("models", "after_10_minute_prediction_model.pkl")
model_path_60 = os.path.join("models", "after_60_minute_prediction_model.pkl")
mapping_path = os.path.join("models", "hospital_mapping.pkl")

after_10_minute_prediction_model = joblib.load(model_path_10)
after_60_minute_prediction_model = joblib.load(model_path_60)
mapping = joblib.load(mapping_path)


def test_scenario(
    hospital_name, day, hour, minute, ktas, lag_beds, lag_op, arrival_minutes
):
    try:
        h_code = mapping[mapping["hospital_name"] == hospital_name][
            "hospital_code"
        ].values[0]
    except:
        return "병원 없음"

    input_data = pd.DataFrame(
        [[h_code, day, hour, minute, ktas, lag_beds, lag_op]],
        columns=[
            "hospital_code",
            "day_of_week",
            "hour",
            "minute",
            "ktas",
            "beds_lag",
            "op_lag",
        ],
    )

    pred_10 = after_10_minute_prediction_model.predict(input_data)
    pred_60 = after_60_minute_prediction_model.predict(input_data)

    w = max(0, min(1, (60 - arrival_minutes) / (60 - 10)))

    final_pred = (pred_10 * w) + (pred_60 * (1 - w))

    return round(final_pred[0][0]), round(final_pred[0][1])


print("--- [시나리오 1] 10분 뒤 예측 ---")
print(test_scenario("대학병원 1", 1, 0, 0, 3, 30, 15, 10))

print("\n--- [시나리오 2] 60분 뒤 예측 ---")
print(test_scenario("대학병원 1", 0, 14, 30, 3, 30, 15, 60))
