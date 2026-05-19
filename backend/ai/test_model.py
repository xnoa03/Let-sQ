import os
import joblib
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "models", "hospital_congestion_prediction.pkl")
mapping_path = os.path.join(current_dir, "models", "hospital_mapping.pkl")


model = joblib.load(model_path)
mapping = joblib.load(mapping_path)


def predict_congestion(hospital_name, day_of_week, hour, minute, ktas):
    try:
        h_code = mapping[mapping["hospital_name"] == hospital_name][
            "hospital_code"
        ].values[0]
    except IndexError:
        return "해당 병원을 찾을 수 없습니다."

    input_data = pd.DataFrame(
        [[h_code, day_of_week, hour, minute, ktas]],
        columns=["hospital_code", "day_of_week", "hour", "minute", "ktas"],
    )

    prediction = model.predict(input_data)

    return {
        "hospital": hospital_name,
        "predicted_beds": round(prediction[0][0]),
        "predicted_op_rooms": round(prediction[0][1]),
    }


result = predict_congestion("의원", 3, 0, 0, 1)
print(f"예측 결과 : {result}")
