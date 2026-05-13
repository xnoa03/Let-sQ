import pandas as pd
from static_data import config


def load_all_hospital():
    df = pd.read_csv(config.STATIC_DATA_PATH, encoding="utf-8-sig")
    hospitals = {}

    for _, row in df.iterrows():
        name = row["name"]
        rating = row["rating"]

        equipment_info = {eq: row[eq] for eq in config.Equipments if eq in row}

        if rating == 1:
            specs = config.Specialists_1
        elif rating == 2:
            specs = config.Specialists_2
        else:
            specs = config.Specialists_3

        hospitals[name] = {
            "total_beds": row["sickbed"],
            "total_operating_rooms": row["operating_room"],
            "rating": rating,
            "equipments": equipment_info,
            "specialists": specs,
        }

    return hospitals
