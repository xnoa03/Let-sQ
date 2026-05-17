import os
import sys
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.abspath(os.path.join(data_dir, ".."))

for path in [data_dir, backend_dir]:
    if path not in sys.path:
        sys.path.append(path)

from dynamic_data import load_static_data
from emergency_rules import EMERGENCY_RULES


def generate_matrix():
    hospitals = load_static_data.load_all_hospital()
    matrix_rows = []

    for symptom_key, symptom_info in EMERGENCY_RULES.items():
        row_data = {
            "symptom_name": symptom_key,
            "ui_symptom_name": symptom_info["ui_label"],
            "ktas_level": symptom_info["ktas"],
        }

        # 병원별 진료 가능 여부 (전공의, 장비 고려)
        for h_name, h_info in hospitals.items():
            # 최소 병원 등급 조건 검사
            if h_info["rating"] > symptom_info["min_rating"]:
                row_data[h_name] = 0
                continue

            # 필수 전문의 조건 검사
            has_specialist = any(
                spec in h_info["specialists"] for spec in symptom_info["specialists"]
            )
            if not has_specialist:
                row_data[h_name] = 0
                continue

            # 수술 필요 및 가용 수술실 조건 검사
            if symptom_info["need_operating"] and h_info["total_operating_rooms"] <= 0:
                row_data[h_name] = 0
                continue

            # 필수 의료 장비 조건 검사
            has_all_equip = True
            for eq in symptom_info["equipments"]:
                if h_info["equipments"].get(eq, 0) == 0:
                    has_all_equip = False
                    break

            row_data[h_name] = 1 if has_all_equip else 0

        matrix_rows.append(row_data)

    df_matrix = pd.DataFrame(matrix_rows)

    hospital_names = list(hospitals.keys())
    cols = ["symptom_name", "ui_symptom_name", "ktas_level"] + hospital_names
    df_matrix = df_matrix[cols]

    output_dir = "../raw"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "hospital_symptom_mapping_matrix.csv")
    df_matrix.to_csv(output_path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    generate_matrix()
