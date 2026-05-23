import csv
import os
from flask import Flask, render_template, jsonify, request

app = Flask(__name__, template_folder='.')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'backend', 'data', 'raw')

EQUIPMENT_COLS = [
    '인공호흡기_일반', '인공호흡기_조산아', '인큐베이터', 'CRRT', 'ECMO',
    '중심체온조절유도기', '고압산소치료기', 'CT', 'MRI', '혈관촬영기'
]

DYNAMIC_DIR = os.path.join(DATA_DIR, 'hospital_dynamic_data')
DYNAMIC_REQUIRED_COLS = {
    'time', 'ktas', 'beds_available', 'op_rooms_available',
    'hospital_name', 'day', 'hour'
}


def load_hospitals():
    path = os.path.join(DATA_DIR, 'hospital_static_data.csv')
    hospitals = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hospitals.append({
                'name': row['name'],
                'rating': int(row['rating']),
                'x': int(row['x']),
                'y': int(row['y']),
                'sickbed': int(row['sickbed']),
                'operating_room': int(row['operating_room']),
                'equipment': {col: int(row[col]) for col in EQUIPMENT_COLS},
            })
    return hospitals


def load_symptoms():
    path = os.path.join(DATA_DIR, 'hospital_symptom_mapping_matrix.csv')
    symptoms = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        meta_cols = {'symptom_name', 'ui_symptom_name', 'ktas_level'}
        hospital_cols = [c for c in (reader.fieldnames or []) if c not in meta_cols]
        for row in reader:
            symptoms.append({
                'symptom_name': row['symptom_name'],
                'ui_symptom_name': row['ui_symptom_name'],
                'ktas_level': int(row['ktas_level']),
                'hospitals': {h: int(row[h]) for h in hospital_cols},
            })
    return symptoms


def load_dynamic():
    result = {}
    if not os.path.isdir(DYNAMIC_DIR):
        print(f"[WARN] {DYNAMIC_DIR} 없음 - 동적 데이터 없이 진행")
        return result

    for fname in sorted(os.listdir(DYNAMIC_DIR)):
        if not fname.endswith('_dynamic_data.csv'):
            continue
        path = os.path.join(DYNAMIC_DIR, fname)
        with open(path, encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
            if not DYNAMIC_REQUIRED_COLS.issubset(cols):
                continue
            rows = list(reader)
        if not rows:
            continue

        by_day = {}
        for r in rows:
            by_day.setdefault(int(r['day']), []).append(r)
        pick_day = max(
            by_day.keys(),
            key=lambda d: max(int(r['beds_available']) for r in by_day[d])
                          - min(int(r['beds_available']) for r in by_day[d])
        )

        day_start = (pick_day - 1) * 1440
        day_rows = sorted(by_day[pick_day], key=lambda x: int(x['time']))
        events = [{
            't': int(r['time']) - day_start,
            'beds': int(r['beds_available']),
            'or': int(r['op_rooms_available']),
            'ktas': int(r['ktas']),
        } for r in day_rows]

        result[rows[0]['hospital_name']] = events

    return result


HOSPITALS = load_hospitals()
SYMPTOMS = load_symptoms()
DYNAMIC = load_dynamic()
print(f"[OK] Loaded {len(HOSPITALS)} hospitals, {len(SYMPTOMS)} symptoms, "
      f"{len(DYNAMIC)} dynamic timelines")


@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/hospitals')
def api_hospitals():
    return jsonify(HOSPITALS)


@app.route('/api/symptoms')
def api_symptoms():
    return jsonify(SYMPTOMS)


@app.route('/api/dynamic')
def api_dynamic():
    return jsonify(DYNAMIC)


@app.route('/api/dispatch', methods=['POST'])
def api_dispatch():
    patient = request.get_json() or {}
    p_symptoms = patient.get('symptoms', [])

    candidates = []
    for h in HOSPITALS:
        can_handle_all = True
        for sym_id in p_symptoms:
            sym = next((s for s in SYMPTOMS if s['symptom_name'] == sym_id), None)
            if sym and sym['hospitals'].get(h['name'], 0) == 0:
                can_handle_all = False
                break
        if not can_handle_all:
            continue
        dx = h['x'] - patient.get('x', 500)
        dy = h['y'] - patient.get('y', 500)
        dist = (dx * dx + dy * dy) ** 0.5
        candidates.append({
            'name': h['name'],
            'rating': h['rating'],
            'x': h['x'],
            'y': h['y'],
            'distance': round(dist, 1),
            'sickbed': h['sickbed'],
        })

    candidates.sort(key=lambda c: c['distance'])
    return jsonify({'patient': patient, 'candidates': candidates[:5]})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)