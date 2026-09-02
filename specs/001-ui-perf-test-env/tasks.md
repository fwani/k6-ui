# Tasks: UI 기반 성능 테스트 환경 구축

**Input**: Design documents from `/specs/001-ui-perf-test-env/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story. Tests are not requested in spec; no test-only phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[USn]**: User story (US1=테스트 생성, US2=테스트 실행, US3=결과 조회, US4=히스토리)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/app/`, `backend/tests/` (Python FastAPI)
- **Frontend**: `frontend/src/` (Vue.js)
- **Docker**: `docker/compose.yaml` or repo root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 프로젝트 초기화 및 디렉터리 구조

- [X] T001 Create backend directory structure: backend/app/models, backend/app/services, backend/app/api, backend/tests
- [X] T002 Create frontend directory structure: frontend/src/components, frontend/src/views, frontend/src/services, frontend/tests
- [X] T003 Initialize Python backend: add requirements.txt (fastapi, uvicorn, pydantic, sqlalchemy, httpx) and backend/app/__init__.py
- [X] T004 Initialize Vue.js frontend: add package.json with vue, vue-router, build tool (Vite), and frontend/src/main.js
- [X] T005 [P] Add backend dev deps and lint: backend/requirements-dev.txt or pyproject.toml with pytest, ruff (or black)
- [X] T006 [P] Add frontend lint/format: frontend/.eslintrc.cjs or eslint.config.js and frontend/package.json scripts
- [X] T007 Add backend run instructions and env notes in backend/README.md
- [X] T008 Add frontend run instructions and env notes in frontend/README.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 모든 유저 스토리에 필요한 DB·API·UI·Docker 기반. 이 단계 완료 전에는 유저 스토리 작업 불가.

- [X] T009 Define DB (SQLite or PostgreSQL) and create schema: performance_test, test_run, test_result tables in backend (e.g. backend/app/models/db.py or Alembic migration)
- [X] T010 Create FastAPI app entry: backend/app/main.py with FastAPI(), CORS middleware, router include placeholder
- [X] T011 Add global exception handler for 400/404 and validation errors in backend/app/main.py (or backend/app/api/errors.py)
- [X] T012 Create Vue app shell: frontend/src/App.vue, frontend/src/main.js, Vue Router with routes (/, /tests, /tests/new, /tests/:id/edit, /tests/:id/run, /runs, /runs/:id, /runs/:id/result) and layout with nav links
- [X] T013 Create frontend API client: frontend/src/services/api.js (or api.ts) with base URL from env and get/post/put/delete helpers
- [X] T014 Add backend Dockerfile: backend/Dockerfile (Python base, install deps, run uvicorn)
- [X] T015 Add frontend Dockerfile: frontend/Dockerfile (build stage + nginx or serve static)
- [X] T016 Add docker/compose.yaml (or docker-compose.yml at root): services api, ui, influxdb, grafana; env and ports; api depends on influxdb
- [X] T017 [P] Add backend config module: backend/app/config.py load DATABASE_URL, GRAFANA_DASHBOARD_URL, INFLUXDB_URL from env

**Checkpoint**: Foundation ready — user story implementation can start

---

## Phase 3: User Story 1 - 테스트 생성 (Priority: P1) — MVP

**Goal**: 웹 UI에서 성능 테스트(대상 URL, 메서드, VUs, 지속 시간 등)를 생성·수정·삭제·목록 조회.

**Independent Test**: 테스트 생성 화면에서 필수 항목 입력 후 저장하면 목록에 표시되고, 이후 실행 가능.

### Implementation for User Story 1

- [X] T018 [P] [US1] Create Performance Test model with fields (id, name, targetUrl, httpMethod, requestBody, headers, vus, duration, requestDelay, createdAt, updatedAt) in backend/app/models/performance_test.py (or backend/app/models.py)
- [X] T019 [US1] Add Performance Test repository/CRUD layer in backend/app/services/test_repository.py (create, get, list, update, delete)
- [X] T020 [US1] Add Pydantic schemas for Test (create, update, response) in backend/app/api/schemas/test.py (or backend/app/api/schemas.py)
- [X] T021 [US1] Implement POST /tests with validation (targetUrl format, required name/vus/duration) and 400 error body in backend/app/api/tests.py
- [X] T022 [US1] Implement GET /tests and GET /tests/:id in backend/app/api/tests.py
- [X] T023 [US1] Implement PUT /tests/:id and DELETE /tests/:id in backend/app/api/tests.py
- [X] T024 [US1] Create Vue view 테스트 생성: frontend/src/views/TestCreate.vue with form fields name, targetUrl, httpMethod, requestBody, headers, vus, duration, requestDelay
- [X] T025 [US1] Add client-side validation (URL format, required) and submit to POST /tests in frontend/src/views/TestCreate.vue
- [X] T026 [US1] Create Vue view 테스트 목록: frontend/src/views/TestList.vue fetch GET /tests, table with name, targetUrl, httpMethod, vus, duration and link to run
- [X] T027 [US1] Wire router and nav: routes /tests (list), /tests/new (create), /tests/:id/edit (edit); link from list to create and to run

**Checkpoint**: User Story 1 complete — create/list/edit test from UI

---

## Phase 4: User Story 2 - 테스트 실행 (Priority: P2)

**Goal**: 생성한 테스트를 UI에서 시작·중지하고, 상태(Ready/Running/Finished/Failed)를 표시.

**Independent Test**: 테스트 실행 화면에서 시작 → 중지까지 동작하고, 상태가 Running → Finished 또는 Failed로 전환됨.

### Implementation for User Story 2

- [X] T028 [P] [US2] Create Test Run model (id, testId, status, startedAt, finishedAt, createdAt) in backend/app/models/test_run.py
- [X] T029 [US2] Implement k6 runner service: generate k6 script from Test params, run k6 (subprocess), MVP one run at a time in backend/app/services/k6_runner.py
- [X] T030 [US2] Implement POST /tests/:testId/runs: create Run (Ready→Running), start k6 in background, return Run; 400 if another run already Running in backend/app/api/runs.py
- [X] T031 [US2] Implement POST /runs/:runId/stop: set Run status Failed/Finished and stop k6 in backend/app/api/runs.py
- [X] T032 [US2] Implement GET /runs/:runId: return Run (id, testId, status, startedAt, finishedAt, createdAt) in backend/app/api/runs.py
- [X] T033 [US2] Create Vue view 테스트 실행: frontend/src/views/RunTest.vue with test name, Start/Stop buttons, status display, poll GET /runs/:runId
- [X] T034 [US2] Wire route /tests/:testId/run and navigation from TestList to RunTest

**Checkpoint**: User Story 2 complete — start/stop test and see status

---

## Phase 5: User Story 3 - 테스트 결과 조회 (Priority: P3)

**Goal**: 테스트 결과 요약(평균/최대 응답 시간, 실패율, 요청 수, TPS/RPS, 실행 시간) 표시 및 Grafana 대시보드 링크 제공.

**Independent Test**: Finished 테스트의 결과 화면에서 요약 지표와 Grafana 링크 확인.

### Implementation for User Story 3

- [X] T035 [P] [US3] Create Test Result model (runId, avgResponseTime, maxResponseTime, failureRate, requestCount, tpsOrRps, executionTime) in backend/app/models/test_result.py
- [X] T036 [US3] Persist Test Result when k6 finishes: parse k6 output or query InfluxDB for summary and save in backend/app/services/k6_runner.py or backend/app/services/result_service.py
- [X] T037 [US3] Implement GET /runs/:runId/result: return Result for runId in backend/app/api/runs.py or backend/app/api/results.py
- [X] T038 [US3] Implement GET /config or GET /settings returning { grafanaDashboardUrl } in backend/app/api/config.py
- [X] T039 [US3] Create Vue view 테스트 결과: frontend/src/views/RunResult.vue fetch GET /runs/:runId/result and GET /config; display avgResponseTime, maxResponseTime, failureRate, requestCount, tpsOrRps, executionTime and Grafana link
- [X] T040 [US3] Wire route /runs/:id/result and navigation from RunTest (when Finished/Failed) to RunResult

**Checkpoint**: User Story 3 complete — view result summary and open Grafana

---

## Phase 6: User Story 4 - 테스트 히스토리 조회 (Priority: P4)

**Goal**: 이전 실행 목록을 테스트 이름, 실행 시간, 상태, 주요 결과 요약과 함께 조회.

**Independent Test**: 테스트 목록(히스토리) 화면에서 과거 실행 목록과 요약 표시.

### Implementation for User Story 4

- [X] T041 [US4] Implement GET /runs with query page, limit, testId; return { items: RunSummary[] } with testName, id, status, startedAt, finishedAt, resultSummary in backend/app/api/runs.py
- [X] T042 [US4] Create Vue view 테스트 히스토리: frontend/src/views/RunList.vue fetch GET /runs, table with testName, status, startedAt, finishedAt, resultSummary; link row to /runs/:id/result
- [X] T043 [US4] Wire route /runs (RunList) and add nav link in layout (frontend/src/App.vue or layout component)

**Checkpoint**: User Story 4 complete — run history list with summary

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 문서·에러 표시·로깅·환경 검증

- [X] T044 [P] Update backend/README.md with env vars (DATABASE_URL, GRAFANA_DASHBOARD_URL, INFLUXDB_URL) and docker run instructions
- [X] T045 [P] Update frontend/README.md with env (VITE_API_URL or equivalent) and docker run instructions
- [X] T046 Configure Grafana data source for InfluxDB and optional dashboard JSON in docker/ or docs (for FR-005)
- [X] T047 Run quickstart.md validation: docker compose up, create test, run, check result and history
- [X] T048 Display API error messages (400/404) in Vue: toast or inline in frontend/src/services/api.js and views
- [X] T049 [P] Add backend logging for test create, run start/stop, result read in backend/app/main.py or per-router

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — blocks all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — no other story dependency
- **Phase 4 (US2)**: Depends on Phase 2, uses US1 (tests list) — can start after US1 list exists
- **Phase 5 (US3)**: Depends on Phase 2 and US2 (Run, Result) — after US2
- **Phase 6 (US4)**: Depends on Phase 2 and US3 (Result summary) — after US3
- **Phase 7 (Polish)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: After Foundational only — independently testable (create/list test)
- **US2 (P2)**: After Foundational + US1 (need tests to run) — independently testable (start/stop/status)
- **US3 (P3)**: After US2 (need Run and Result) — independently testable (result view + Grafana link)
- **US4 (P4)**: After US3 (need Result for summary in list) — independently testable (run history list)

### Within Each User Story

- Models before services/repository
- Repository/schemas before API endpoints
- API endpoints before Vue views
- Views and router last

### Parallel Opportunities

- Phase 1: T005, T006 [P]; T007, T008 can follow T001–T004
- Phase 2: T017 [P]; T014, T015 [P] (backend/frontend Dockerfiles)
- US1: T018 [P]; T024, T026 can be done in parallel after API tasks
- US2: T028 [P]
- US3: T035 [P]
- Polish: T044, T045, T049 [P]

---

## Parallel Example: User Story 1

```text
# After T019–T020, API and Vue can proceed in parallel:
Backend: T021, T022, T023 (tests API)
Frontend: T024, T025 (TestCreate), T026 (TestList), T027 (router)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup  
2. Complete Phase 2: Foundational  
3. Complete Phase 3: User Story 1  
4. **STOP and VALIDATE**: Create/list test from UI  
5. Demo/deploy if ready  

### Incremental Delivery

1. Setup + Foundational → foundation ready  
2. + US1 → create/list test (MVP)  
3. + US2 → run/stop/status  
4. + US3 → result + Grafana link  
5. + US4 → run history list  
6. + Polish → docs, errors, quickstart validation  

### Task Count Summary

| Phase            | Task count |
|------------------|------------|
| Phase 1 Setup    | 8          |
| Phase 2 Foundational | 9      |
| Phase 3 US1      | 10         |
| Phase 4 US2      | 7          |
| Phase 5 US3      | 6          |
| Phase 6 US4      | 3          |
| Phase 7 Polish   | 6          |
| **Total**        | **49**     |

---

## Notes

- [P] tasks = different files or no ordering dependency
- [USn] maps task to user story for traceability
- Each user story is independently testable at its checkpoint
- Commit after each task or logical group
- Stop at any checkpoint to validate that story
