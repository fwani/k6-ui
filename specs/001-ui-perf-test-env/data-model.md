# Data Model: UI 기반 성능 테스트 환경

**Feature**: 001-ui-perf-test-env  
**Date**: 2025-03-16

스펙의 Key Entities와 FR을 기반으로 한 논리 데이터 모델(구현 저장소·스키마는 구현 시 결정).

---

## 1. 성능 테스트 (Performance Test)

한 번 정의된 테스트 설정. 사용자가 UI에서 생성·수정한다.

| 속성 | 설명 | 제약 |
|------|------|------|
| id | 식별자 | 필수, 유일 |
| name | 테스트 이름 | 필수 (FR-001) |
| targetUrl | 테스트 대상 URL | 필수, URL 형식 (FR-009) |
| httpMethod | GET / POST / PUT / DELETE | 필수 |
| requestBody | 요청 본문 | 선택 |
| headers | HTTP 헤더 (키-값 목록) | 선택 |
| vus | 동시 사용자 수 (VUs) | 필수, 양수 |
| duration | 테스트 지속 시간 | 필수, 양수 |
| requestDelay | 요청 간 대기 시간 | 선택, 비음수 |
| createdAt | 생성 시각 | 자동 |
| updatedAt | 수정 시각 | 자동 |

**검증 규칙 (FR-009)**:
- targetUrl: 비어 있지 않음, URL 형식 검증 실패 시 저장 거부 및 오류 메시지
- name: 비어 있지 않음
- vus, duration: 양수

---

## 2. 테스트 실행 (Test Run)

특정 성능 테스트의 한 번의 실행. 상태 전이만 다룬다.

| 속성 | 설명 | 제약 |
|------|------|------|
| id | 식별자 | 필수, 유일 |
| testId | 성능 테스트 id | 필수, FK |
| status | Ready / Running / Finished / Failed | 필수 (FR-003) |
| startedAt | 실행 시작 시각 | status ≥ Running 일 때 설정 |
| finishedAt | 실행 종료 시각 | status = Finished | Failed 일 때 설정 |
| createdAt | 실행 레코드 생성 시각 | 자동 |

**상태 전이**:
- 생성 시: status = Ready
- 사용자 "시작" → Running, startedAt 설정
- 정상 종료 → Finished, finishedAt 설정
- 오류/중지 → Failed, finishedAt 설정 (FR-010)
- MVP: 동시에 하나의 Run만 Running 허용

---

## 3. 테스트 결과 (Test Result)

한 테스트 실행(Test Run)에 대한 결과 요약. UI 결과 화면·목록에 사용 (FR-004, FR-006).

| 속성 | 설명 | 제약 |
|------|------|------|
| runId | 테스트 실행 id | 필수, FK, 1:1 Run |
| avgResponseTime | 평균 응답 시간 | 숫자, 단위(ms 등)는 구현 시 |
| maxResponseTime | 최대 응답 시간 | 숫자 |
| failureRate | 실패율 (0–1 또는 %) | 숫자 |
| requestCount | 요청 수 | 비음수 정수 |
| tpsOrRps | TPS/RPS | 숫자 |
| executionTime | 테스트 실행 시간 | 양수(초 등) |

**관계**: Test Run 1 : 1 Test Result (Run이 Finished/Failed일 때 결과 생성·저장). 상세 시계열 메트릭은 메트릭 저장소(InfluxDB)에 있으며, 대시보드에서 조회한다.

---

## 4. 관계 요약

```
Performance Test 1 ---- * Test Run
Test Run 1 ---- 1 Test Result
```

- 테스트 정의(Performance Test)는 여러 번 실행(Test Run)될 수 있음.
- 각 Run은 최대 하나의 Result 요약을 가짐.
- Run 목록 조회 시 테스트 이름은 Test의 name으로 표시(FR-006).
