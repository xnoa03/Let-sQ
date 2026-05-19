import csv
import os
from flask import Flask, render_template, jsonify, request

app = Flask(__name__, template_folder='.')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))           # frontend/
PROJECT_ROOT = os.path.dirname(BASE_DIR)                        # LET-SQ/
DATA_DIR = os.path.join(PROJECT_ROOT, 'backend', 'data', 'raw')

EQUIPMENT_COLS = [
    '인공호흡기_일반', '인공호흡기_조산아', '인큐베이터', 'CRRT', 'ECMO',
    '중심체온조절유도기', '고압산소치료기', 'CT', 'MRI', '혈관촬영기'
]



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
    """hospital_symptom_mapping_matrix.csv 를 읽어 dict 리스트로 반환."""
    path = os.path.join(DATA_DIR, 'hospital_symptom_mapping_matrix.csv')
    symptoms = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        meta_cols = {'symptom_name', 'ui_symptom_name', 'ktas_level'}
        hospital_cols = [c for c in reader.fieldnames if c not in meta_cols]
        for row in reader:
            symptoms.append({
                'symptom_name': row['symptom_name'],
                'ui_symptom_name': row['ui_symptom_name'],
                'ktas_level': int(row['ktas_level']),
                'hospitals': {h: int(row[h]) for h in hospital_cols},
            })
    return symptoms



HOSPITALS = load_hospitals()
SYMPTOMS = load_symptoms()
print(f"[OK] Loaded {len(HOSPITALS)} hospitals, {len(SYMPTOMS)} symptoms")


# ─────────────────────────────────────────────
# 라우트
# ─────────────────────────────────────────────
@app.route('/')
def index():
    """대시보드 페이지."""
    return render_template('dashboard.html')


@app.route('/api/hospitals')
def api_hospitals():
    """병원 정적 데이터."""
    return jsonify(HOSPITALS)


@app.route('/api/symptoms')
def api_symptoms():
    """증상 + 병원별 처치 가능 매트릭스."""
    return jsonify(SYMPTOMS)


@app.route('/api/dispatch', methods=['POST'])
def api_dispatch():
    """

    Request JSON:
      { "x": 500, "y": 500, "age": 55, "sex": "M",
        "symptoms": ["신경학적_급성 의식장애", ...] }

    Response JSON:
      { "patient": {...}, "candidates": [{"name": ..., "score": ...}, ...] }
    """
    patient = request.get_json() or {}
    p_symptoms = patient.get('symptoms', [])

    # 임시 로직: 선택된 증상을 모두 처치 가능한 병원만 필터 + 거리 정렬
    candidates = []
    for h in HOSPITALS:
        # 증상별 처치 가능 여부 체크
        can_handle_all = True
        for sym_id in p_symptoms:
            sym = next((s for s in SYMPTOMS if s['symptom_name'] == sym_id), None)
            if sym and sym['hospitals'].get(h['name'], 0) == 0:
                can_handle_all = False
                break
        if not can_handle_all:
            continue
        # 유클리드 거리 (가상 좌표계 기준)
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
    # debug=True 로 코드 수정 시 자동 리로드
    app.run(debug=True, host='0.0.0.0', port=5000)