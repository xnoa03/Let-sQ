import sys, os
import pandas as pd
import simpy

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import load_static_data
import hospital_simulation


def generate_dynamic_data():
    all_hospitals_info = load_static_data.load_all_hospital()
    output_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../raw/hospital_dynamic_data")
    )

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    for name, info in all_hospitals_info.items():
        env = simpy.Environment()
        hospital_log = []
        hospital = hospital_simulation.Hospital(env, name, info)

        env.process(hospital_simulation.patient_generation(env, hospital, hospital_log))
        env.run(until=144000)

        result = pd.DataFrame(hospital_log)
        result["hospital_name"] = name
        result = result.sort_values(by="time")
        result["day_of_week"] = ((result["time"] // 1440) % 7).astype(int)
        result["day"] = (result["time"] // 1440).astype(int) + 1
        result["hour"] = ((result["time"] // 60) % 24).astype(int)

        file_path = os.path.join(output_dir, f"{name}_dynamic_data.csv")
        result.to_csv(file_path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    generate_dynamic_data()
