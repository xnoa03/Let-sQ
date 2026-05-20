import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from xgboost import plot_importance

model_path = os.path.join("models", "hospital_congestion_prediction.pkl")
mapping_path = os.path.join("models", "hospital_mapping.pkl")
model = joblib.load(model_path)
mapping = joblib.load(mapping_path)


def test_scenario(hospital_name, day, hour, minute, ktas, lag_beds, lag_op):
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

    pred = model.predict(input_data)
    return round(pred[0][0]), round(pred[0][1])


print("--- [시나리오 1] 병상 여유 (30개) ---")
print(test_scenario("대학병원 1", 0, 14, 30, 3, 30, 15))

print("\n--- [시나리오 2] 병상 부족 (0개) ---")
print(test_scenario("대학병원 1", 0, 14, 30, 3, 0, 15))


plt.figure(figsize=(10, 6))
plot_importance(model, importance_type="weight")
plt.title("Feature Importance")
plt.show()
#
