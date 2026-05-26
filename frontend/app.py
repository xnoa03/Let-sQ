import csv
import os
import joblib
import pandas as pd
from flask import Flask, render_template, jsonify, request

app = Flask(__name__, template_folder='.')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'backend', 'data', 'raw')

MODEL_DIR = os.path.join(PROJECT_ROOT, 'backend', 'ai', 'models')

try:
    model_10 = joblib.load(os.path.join(MODEL_DIR, "after_10_minute_prediction_model.pkl"))
    model_60 = joblib.load(os.path.join(MODEL_DIR, "after_60_minute_prediction_model.pkl"))
    hospital_mapping = joblib.load(os.path.join(MODEL_DIR, "hospital_mapping.pkl"))
    print("[OK] AI 모델 로딩 완료!")
except Exception as e:
    print(f"[WARN] AI 모델을 불러오지 못했습니다. (경로나 파일 확인 필요): {e}")
    model_10, model_60, hospital_mapping = None, None, None

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
print(f"[OK] Loaded {len(HOSPITALS)} hospitals, {len(SYMPTOMS)} symptoms")

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

# ====================================================
# [Step 2] AI 모델 적용된 병원 추천 API
# ====================================================
# ====================================================
# [교체 적용 구간] 자료형 직렬화 오류를 해결한 API 엔드포인트
# ====================================================
@app.route('/api/dispatch', methods=['POST'])
def api_dispatch():
    data = request.get_json() or {}
    patient = data.get('patient', {})
    sim_time = data.get('simTime', 0) # 프론트에서 넘겨준 시뮬레이션 현재 시간
    
    # 프론트에서 보낸 환자 증상 리스트 (symptom_name만 추출)
    p_symptoms = [s['symptom_name'] for s in patient.get('symptoms', [])]
    ktas_level = patient.get('ktas', 3)
    
    # 시뮬레이션 시간을 요일, 시, 분으로 변환 (가상 시간)
    current_day = int((sim_time // 1440) % 7)
    current_hour = int((sim_time // 60) % 24)
    current_minute = int(sim_time % 60)

    candidates = []
    
    for h in HOSPITALS:
        # 1. 1차 필터링: 해당 병원이 환자의 모든 증상을 수용 가능한가?
        can_handle_all = True
        for sym_id in p_symptoms:
            sym = next((s for s in SYMPTOMS if s['symptom_name'] == sym_id), None)
            if sym and sym['hospitals'].get(h['name'], 0) == 0:
                can_handle_all = False
                break
        
        if not can_handle_all:
            continue
            
        # 2. 이동 시간(거리) 계산 (맵 크기 1000 기준, 1거리 = 0.1분으로 임의 설정)
        dx = h['x'] - patient.get('x', 500)
        dy = h['y'] - patient.get('y', 500)
        dist = (dx * dx + dy * dy) ** 0.5
        arrival_minutes = min(60, int(dist * 0.1)) # 최대 60분으로 제한
        
        # 3. 현재 병상 및 수술실 수 확인 (DYNAMIC 데이터 기준)
        events = DYNAMIC.get(h['name'], [])
        lag_beds = h['sickbed']
        lag_op = h['operating_room']
        
        # sim_time보다 이전의 가장 최근 이벤트를 찾아 현재 상태로 설정
        for ev in reversed(events):
            if ev['t'] <= sim_time:
                lag_beds = ev['beds']
                lag_op = ev['or']
                break

        ai_score = 0.0
        pred_beds = float(lag_beds)
        
        # 4. XGBoost AI 모델 추론
        if model_10 is not None and model_60 is not None and hospital_mapping is not None:
            try:
                # 병원 코드 매핑
                h_code = hospital_mapping[hospital_mapping["hospital_name"] == h['name']]["hospital_code"].values[0]
                
                input_data = pd.DataFrame(
                    [[h_code, current_day, current_hour, current_minute, ktas_level, lag_beds, lag_op]],
                    columns=["hospital_code", "day_of_week", "hour", "minute", "ktas", "beds_lag", "op_lag"]
                )
                
                # float32 자료형 에러를 방지하기 위해 파이썬 표준 float형으로 명시적 변환
                pred_10 = float(model_10.predict(input_data)[0][0])
                pred_60 = float(model_60.predict(input_data)[0][0])
                
                # 도착 시간에 따른 가중치 보간법
                w = max(0.0, min(1.0, (60.0 - arrival_minutes) / (60.0 - 10.0)))
                pred_beds = (pred_10 * w) + (pred_60 * (1.0 - w))
                
                # 수용 가능 확률(Score) 계산: 예측 잔여 병상 / 전체 병상 (최대 100%)
                if h['sickbed'] > 0:
                    ai_score = round(max(0.0, min(100.0, (pred_beds / h['sickbed']) * 100.0)), 1)
                else:
                    ai_score = 0.0
            except Exception as e:
                if h['sickbed'] > 0:
                    ai_score = round((float(lag_beds) / h['sickbed']) * 100.0, 1)
        else:
            if h['sickbed'] > 0:
                ai_score = round((float(lag_beds) / h['sickbed']) * 100.0, 1)
        
        candidates.append({
            'name': h['name'],
            'rating': int(h['rating']),
            'x': int(h['x']),
            'y': int(h['y']),
            'distance': round(float(dist), 1),
            'eta': int(arrival_minutes),
            'sickbed': int(h['sickbed']),
            'ai_score': float(ai_score), # JSON 변환이 가능한 타입으로 서빙
            'pred_beds': round(float(pred_beds), 1)
        })

    # AI 수용 확률(ai_score)이 높은 순으로 내림차순 정렬, 점수가 같으면 거리순
    candidates.sort(key=lambda c: (c['ai_score'], -c['distance']), reverse=True)
    
    return jsonify({
        'patient': patient,
        'candidates': candidates[:5] # 상위 5개 병원 리턴
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)