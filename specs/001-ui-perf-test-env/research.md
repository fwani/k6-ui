# Research: UI 기반 성능 테스트 환경

**Feature**: 001-ui-perf-test-env  
**Date**: 2025-03-16

## 1. 부하 테스트 실행 엔진 (k6)

**Decision**: k6 사용

**Rationale**: PRD에서 k6 기반으로 명시. 스크립트 기반이지만 UI에서 파라미터(URL, method, VUs, duration 등)를 받아 동적으로 스크립트 생성 또는 k6 REST/API 모드로 실행하는 패턴이 일반적. 커뮤니티·문서·Grafana 연동 예제가 풍부함.

**Alternatives considered**:
- JMeter: GUI/무거운 편, Docker/자동화 시 무헤드 모드 필요.
- Gatling: Scala 기반, 학습 비용.
- Locust: Python, 분산 시 설정 복잡.  
→ MVP·Docker 단일 명령·코드 없이 UI로 실행 요구에 k6가 적합.

---

## 2. 메트릭 저장소

**Decision**: InfluxDB 1.x 또는 2.x (k6 공식 출력 지원)

**Rationale**: k6가 InfluxDB로 메트릭 전송하는 공식 옵션이 있으며, Grafana에서 InfluxDB 데이터 소스 연결이 표준적으로 지원됨. Docker 이미지 제공.

**Alternatives considered**:
- Prometheus: pull 모델; k6는 단기 실행 후 종료되므로 push가 나음. k6는 Prometheus 리모트 쓰기 지원하나 설정이 상대적으로 무거움.
- TimescaleDB / PostgreSQL: 시계열 가능하나 k6 기본 출력이 아님.  
→ InfluxDB로 단순화.

---

## 3. 대시보드 (Grafana)

**Decision**: Grafana 사용

**Rationale**: PRD 명시. InfluxDB 데이터 소스 연동, 요청 수/초·응답 시간·에러율·VU·처리량 등 대시보드 템플릿/예제가 많음.

**Alternatives considered**: 자체 차트 UI(개발 부담), Kibana(ELK 스택·무거움). → Grafana 유지.

---

## 4. 전체 기동 방식 (Docker Compose)

**Decision**: 단일 `docker compose up`(또는 `docker-compose up`)으로 UI·API·k6 실행 환경·Grafana·InfluxDB 기동

**Rationale**: PRD에서 "docker compose up으로 전체 환경 실행 가능" 요구. Compose로 서비스 의존성·네트워크·볼륨을 한 번에 정의.

**Alternatives considered**: Kubernetes(과한 복잡도), 수동 다중 터미널(편의성 낮음). → Docker Compose.

---

## 5. API 서버·UI 스택

**Decision**: **Backend: Python + FastAPI**, **Frontend: Vue.js** (SPA). API는 REST(테스트 CRUD·실행·상태·결과 조회), UI는 Vue로 API 호출.

**Rationale**: FastAPI는 비동기 지원·자동 OpenAPI·검증이 강해 API 서버에 적합. Vue.js는 학습 곡선이 완만하고 단순 관리 페이지 4화면 구성에 충분. Python으로 k6 스크립트 생성·subprocess 실행 등 백엔드 로직 구현이 자연스러움.

**Alternatives considered**: Node.js+Fastify(팀이 Python 선호 시 FastAPI가 유리); React(선택 가능하나 Vue로 정리). → **Python FastAPI + Vue.js**로 기술 정리.

---

## 6. k6 실행 방식 (UI 파라미터 → 실행)

**Decision**: API 서버가 UI에서 받은 파라미터로 k6 스크립트를 동적 생성하거나, k6의 환경 변수/JSON 설정을 사용해 실행. 한 번에 하나의 테스트만 실행(MVP).

**Rationale**: "코드 작성 없이 UI로 실행"을 위해 URL·method·VUs·duration·headers·body 등을 k6 스크립트 또는 실행 옵션으로 변환해야 함. k6는 CLI + JS 스크립트 또는 `k6 run`에 전달 가능한 옵션으로 동작.

**Alternatives considered**: 미리 정의된 스크립트만 실행(유연성 부족); UI 파라미터를 스크립트 템플릿에 주입하는 방식이 일반적. → 동적 스크립트/설정 생성.

---

## 7. 테스트·실행 이력 저장

**Decision**: 테스트 정의·실행 이력·결과 요약은 API 서버가 관리하는 저장소에 보관(파일·SQLite·PostgreSQL 등). 상세 메트릭은 InfluxDB에 k6가 직접 전송.

**Rationale**: FR-006(이전 실행 목록 조회), FR-004(결과 요약 표시)를 위해 테스트 메타데이터와 요약이 필요. 시계열 메트릭은 InfluxDB에 두고, 요약만 API 저장소에 저장해도 됨.

**Alternatives considered**: 모든 것을 InfluxDB에만 저장 — 메타데이터 쿼리·목록 조회가 불편. → 메타·요약은 앱 저장소, 시계열은 InfluxDB.
