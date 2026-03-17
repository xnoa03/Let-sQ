# 🚑 AI를 활용한 환자 맞춤형 최적 응급 이송 시뮬레이션 개발

<div align="left">
  <img src="https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white">
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/MariaDB-003545?style=for-the-badge&logo=mariadb&logoColor=white">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
</div>

<br>

## 📖 목차 (Table of Contents)
1. [프로젝트 개요](#-프로젝트-개요)
2. [주요 기능](#-주요-기능)
3. [시스템 아키텍처 및 기술 스택](#-시스템-아키텍처-및-기술-스택)
4. [팀원 및 역할](#-팀원-및-역할)

<br>

## 📌 프로젝트 개요
[cite_start]최근 의료 현장에서 심각한 문제로 대두되고 있는 **'응급실 뺑뺑이'** 현상을 데이터 처리와 알고리즘 설계의 관점에서 해결하기 위한 프로젝트입니다. [cite: 151, 155] [cite_start]단순 거리 중심의 현행 체계를 벗어나, 환자의 상태와 병원의 실시간 수용 가능 여부를 종합적으로 분석하여 당장 치료 가능한 최적의 병원을 매칭하는 알고리즘 및 시뮬레이션을 개발합니다. [cite: 156]

## ✨ 주요 기능
* [cite_start]**가상 의료 데이터 구축**: 현실적인 개인정보 접근 제약을 극복하기 위해, 공공데이터포털의 데이터를 기반으로 포아송 분포 등 실제 통계 분포를 적용한 정교한 가상 의료 데이터(응급실 포화 지수 등)를 생성합니다. [cite: 164, 165]
* [cite_start]**시계열 혼잡도 예측 AI**: 과거 데이터를 학습하여 환자가 병원에 도착할 시점의 병상 가용 여부를 예측하는 인공지능 모델을 구현합니다. [cite: 161, 285]
* [cite_start]**최적 병원 결정 알고리즘**: 환자의 예측 대기 시간, 이동 시간, 병원 등급에 대한 가중치를 환자의 중증도에 따라 동적으로 조절하여 최적의 병원을 추천하는 알고리즘을 설계합니다. [cite: 178, 179]
* [cite_start]**실시간 이송 시뮬레이션**: 가상 환자 발생부터 이송 성공/실패까지의 과정을 지도 API를 연동하여 시각적으로 시뮬레이션합니다. [cite: 181, 202, 285]

## 🛠 시스템 아키텍처 및 기술 스택
*(추후 여기에 기획서 5페이지의 아키텍처 다이어그램 이미지를 추가해 주세요)*

* [cite_start]**Frontend**: Flutter (시뮬레이션 UI 및 대시보드) [cite: 231, 232]
* [cite_start]**Backend**: Django (메인 서버, API 요청 처리), MariaDB (데이터 저장 및 CRUD) [cite: 234, 236, 237, 239]
* [cite_start]**AI Core**: FastAPI (혼잡도 예측 API), Python/Pandas (가상 데이터 전처리) [cite: 227, 229]
* [cite_start]**Version Control**: Git / GitHub [cite: 220]

## 👥 팀원 및 역할
| 이름 | 담당 업무 | 세부 역할 |
|---|---|---|
| **박종은** | 백엔드 및 시뮬레이션 | [cite_start]가상환자 발생/이송 시뮬레이터 개발, 알고리즘 연산용 API 서버 구축, 로그 분석 [cite: 183] |
| **김병우** | 핵심 알고리즘 | [cite_start]다중 변수 기반 병원 추천 가중치 수식 설계, 최단 경로 및 매칭 알고리즘 구현 [cite: 183] |
| **권오섭** | 기획 및 데이터 | [cite_start]의료 시나리오 데이터 전처리 및 DB화, 전체 프로젝트 일정 관리 [cite: 183] |
| **임준형** | UI/UX 및 시각화 | [cite_start]응급 이송 현황 대시보드 시각화, 지도 API 연동 최적 경로 프로토타입 구현 [cite: 183] |
