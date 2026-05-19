import simpy
import random


class Hospital:
    def __init__(self, env, name, info):
        self.env = env
        self.name = name
        self.rating = info["rating"]
        self.beds = simpy.Resource(env, capacity=max(1, info["total_beds"]))
        self.equipments = info.get("equipments", {})
        self.specialists = info.get("specialists", [])

        if info["total_operating_rooms"] > 0:
            self.operating_rooms = simpy.Resource(
                env, capacity=info["total_operating_rooms"]
            )
        else:
            self.operating_rooms = None


def get_arrival_weight(env_now):
    total_minutes = int(env_now)
    current_day = (total_minutes // 1440) % 7
    current_hour = (total_minutes // 60) % 24

    day_weights = {0: 1.5, 6: 1.5, 1: 1.1, 2: 1.1, 5: 1.0, 3: 0.9, 4: 0.8}
    d_weight = day_weights.get(current_day, 1.0)

    if 9 <= current_hour < 24:
        h_weight = 1.4
    elif (0 <= current_hour < 3) or (6 <= current_hour < 9):
        h_weight = 0.8
    else:
        h_weight = 0.4

    return d_weight * h_weight


def patient_outbreak(env, hospital, log):
    if hospital.rating == 1:
        weights = [0.05, 0.15, 0.45, 0.25, 0.10]
    elif hospital.rating == 2:
        weights = [0.02, 0.10, 0.50, 0.28, 0.10]
    else:
        weights = [0.00, 0.02, 0.20, 0.50, 0.28]

    ktas = random.choices([1, 2, 3, 4, 5], weights=weights)[0]

    log.append(
        {
            "time": int(env.now),
            "ktas": ktas,
            "beds_available": hospital.beds.capacity - hospital.beds.count,
            "op_rooms_available": (
                (hospital.operating_rooms.capacity - hospital.operating_rooms.count)
                if hospital.operating_rooms
                else 0
            ),
            "hospital_name": hospital.name,
        }
    )

    if ktas <= 2 and hospital.operating_rooms:
        with hospital.operating_rooms.request() as req:
            yield req
            yield env.timeout(random.randint(60, 180))

    if ktas <= 3:
        with hospital.beds.request() as req:
            yield req
            stay_time = (
                random.randint(300, 1440) if ktas <= 2 else random.randint(180, 480)
            )
            yield env.timeout(stay_time)
    else:
        yield env.timeout(random.randint(30, 60))


def patient_generation(env, hospital, log):
    while True:
        if hospital.rating == 1:
            base_interval = 15
        elif hospital.rating == 2:
            base_interval = 30
        else:
            base_interval = 100

        weight = get_arrival_weight(env.now)
        actual_interval = base_interval / weight

        yield env.timeout(random.expovariate(1.0 / actual_interval))
        env.process(patient_outbreak(env, hospital, log))
