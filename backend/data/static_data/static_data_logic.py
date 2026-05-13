import pandas as pd
import random
import math
import config


def generate_hospital_static_data():
    data = []
    idx = 0

    for info in config.Hospital_Info:
        rating = info["rating"]
        mandatory_list = info["mandatory_equipments"]

        for _ in range(info["count"]):
            name = config.Hospital_Name[idx]

            radius = random.randint(*info["radius_range"])
            angle = random.uniform(0, 2 * math.pi)

            x = int(config.CENTER_X + radius * math.cos(angle))
            y = int(config.CENTER_Y + radius * math.sin(angle))

            x = max(0, min(config.MAP_SIZE, x))
            y = max(0, min(config.MAP_SIZE, y))

            sickbed = random.randint(*info["sickbed_range"])
            operating_room = random.randint(*info["operating_room_range"])

            hospital_dict = {
                "name": name,
                "rating": rating,
                "x": x,
                "y": y,
                "sickbed": sickbed,
                "operating_room": operating_room,
            }

            current_equipments = set(mandatory_list)
            other_candidates = [
                e for e in config.Equipments if e not in current_equipments
            ]

            add_count = random.randint(0, 2)
            if add_count > 0 and other_candidates:
                to_add = random.sample(
                    other_candidates, min(len(other_candidates), add_count)
                )
                current_equipments.update(to_add)

            for equipment in config.Equipments:
                hospital_dict[equipment] = 1 if equipment in current_equipments else 0

            data.append(hospital_dict)
            idx += 1

    return pd.DataFrame(data)
