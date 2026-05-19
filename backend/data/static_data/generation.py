import os
import config
import static_data_logic


def generate_static_data():
    try:
        result = static_data_logic.generate_hospital_static_data()

        result.to_csv(config.STATIC_DATA_PATH, index=False, encoding="utf-8-sig")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    generate_static_data()
