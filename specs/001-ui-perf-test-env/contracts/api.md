# API Contract: UI ↔ Backend

**Feature**: 001-ui-perf-test-env  
**Date**: 2025-03-16

웹 UI가 호출하는 백엔드 API의 계약. REST 스타일, JSON 요청/응답. 실제 base URL·버전 prefix는 구현 시 결정.

---

## 1. 테스트 정의 (Performance Test)

### 목록 조회

- **GET** `/tests`
- **Response**: `{ "items": [ Test ] }`  
  - `Test`: id, name, targetUrl, httpMethod, requestBody?, headers?, vus, duration, requestDelay?, rampUp?, iterations?, createdAt, updatedAt

### 단건 조회

- **GET** `/tests/:id`
- **Response**: `Test`
- **404**: 해당 id 없음

### 생성

- **POST** `/tests`
- **Request body**: name, targetUrl, httpMethod, requestBody?, headers?, vus, duration, requestDelay?, rampUp? (기본 0), iterations? (총 반복 횟수; 비우면 지속 시간 기준)
- **Response**: 201, `Test`
- **400**: 검증 실패(예: URL 형식, 필수 누락) — 오류 메시지 본문에 이유

### 수정

- **PUT** `/tests/:id`
- **Request body**: 동일 필드(전부 또는 부분은 구현 정책에 따름)
- **Response**: 200, `Test`
- **400**: 검증 실패  
- **404**: id 없음

### 삭제

- **DELETE** `/tests/:id`
- **Response**: 204
- **404**: id 없음

---

## 2. 테스트 실행 (Test Run)

### 실행 시작

- **POST** `/tests/:testId/runs`
- **Response**: 201, `Run` (status = Running 또는 Ready 후 곧 Running)
- **400**: 이미 다른 Run이 Running인 경우(MVP: 동시 1건) 또는 testId 없음
- **404**: testId에 해당 테스트 없음

### 실행 중지

- **POST** `/runs/:runId/stop`
- **Response**: 200, `Run` (status = Failed 또는 Finished)
- **404**: runId 없음

### 실행 상태 조회

- **GET** `/runs/:runId`
- **Response**: `Run` — id, testId, status (Ready|Running|Finished|Failed), startedAt?, finishedAt?, createdAt

---

## 3. 테스트 결과 (Test Result)

### 결과 요약 조회

- **GET** `/runs/:runId/result`
- **Response**: 200, `Result` — runId, avgResponseTime, maxResponseTime, failureRate, requestCount, tpsOrRps, executionTime  
  또는 Run이 아직 Running이면 200 + 부분 결과 또는 204/404
- **404**: runId 없음 또는 결과 미생성

---

## 4. 테스트 히스토리 (실행 목록)

### 실행 목록 조회

- **GET** `/runs` (또는 `GET` `/tests/:testId/runs` — 테스트별 필터)
- **Query**: page?, limit?, testId? (선택)
- **Response**: `{ "items": [ RunSummary ] }`  
  - `RunSummary`: id, testId, testName, status, startedAt?, finishedAt?, createdAt, resultSummary? (avgResponseTime, failureRate 등 요약 필드 일부)

---

## 5. 대시보드 링크

- UI에 표시할 Grafana 대시보드 URL은 **구성이 아니라 백엔드에서 제공해도 됨** (예: 환경 변수).  
- 또는 **GET** `/config` 또는 `/settings` 에 `{ "grafanaDashboardUrl": "..." }` 포함.  
- 구현 시 정하면 됨.

---

## 6. 공통

- **Content-Type**: `application/json`
- **에러 본문**: `{ "message": "...", "code": "..." }` 형태 권장 (4xx/5xx)
- **검증 오류(400)**: FR-009에 따라 대상 URL 등 필수·형식 오류 시 명확한 메시지
