# HTTP API

FastAPI 백엔드 REST API. **경로에 버전 prefix는 없습니다.** 로컬·Compose 예: `http://localhost:8080`.

JSON 응답 필드는 Pydantic `alias` 기준 **camelCase**입니다. 직렬화 시 `by_alias=True`를 사용합니다.

관련: [architecture.md](./architecture.md) (포트·Compose), [database.md](./database.md) (저장 필드).

## 초기 계약 문서와의 관계

[specs/001-ui-perf-test-env/contracts/api.md](../specs/001-ui-perf-test-env/contracts/api.md)는 초기 스펙입니다. **실제 동작은 본 문서와 소스 코드를 우선**합니다. 이후 추가된 엔드포인트(로그·요청 목록·스크린샷·업로드·실행 삭제 등)가 있습니다.

## 공통

- **Content-Type**: 요청 본문은 `application/json`(파일 업로드 제외).
- **검증 오류 (422)**: `message`, `code`(`VALIDATION_ERROR`), `details`(FastAPI 오류 목록).
- **기타 4xx/5xx**: 본문에 `message`, `code` 필드가 오는 경우가 많습니다 ([`backend/app/main.py`](../backend/app/main.py) 예외 핸들러).

## 엔드포인트 요약

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 상태 확인. 본문에 status 필드 |
| GET | `/config` | Grafana URL 등 |
| POST | `/tests` | 테스트 생성 → 201 + Test 객체 |
| GET | `/tests` | 목록. 본문은 `items` 배열(Test 객체들) |
| GET | `/tests/{id}` | 단건 |
| PUT | `/tests/{id}` | 수정 |
| DELETE | `/tests/{id}` | 삭제 → 204 |
| POST | `/tests/{test_id}/runs` | 실행 시작 → 201 + Run. 본문 선택 |
| POST | `/runs/{run_id}/stop` | 중지 → Run |
| GET | `/runs` | 실행 목록(페이지네이션) |
| GET | `/runs/{run_id}` | 실행 단건 |
| DELETE | `/runs/{run_id}` | 삭제 → 204 (Running이면 400) |
| GET | `/runs/{run_id}/logs` | 텍스트 로그. JSON 키 `log` |
| GET | `/runs/{run_id}/requests` | 요청별 행 목록 + `total` |
| GET | `/runs/{run_id}/result` | 결과 요약 + `stepSummaries` 등 |
| GET | `/runs/{run_id}/screenshots/{vu_index}` | 이미지 바이너리. 응답 헤더 Content-Type은 image/jpeg |
| POST | `/uploads/k6-fixture` | multipart 파일 업로드 |

구현 참고: [`tests.py`](../backend/app/api/tests.py), [`runs.py`](../backend/app/api/runs.py), [`config.py`](../backend/app/api/config.py), [`uploads.py`](../backend/app/api/uploads.py).

## GET /config

응답 예:

```json
{
  "grafanaDashboardUrl": "http://localhost:3001/d/k6-load-testing/k6-load-testing-results",
  "grafanaBrowserVitalsUrl": "http://localhost:3001/d/browser-web-vitals/browser-web-vitals"
}
```

## 테스트 리소스

경로 prefix: `/tests`. 스키마 정의는 [`TestCreate`](../backend/app/api/schemas/test.py), [`TestUpdate`](../backend/app/api/schemas/test.py), 응답은 [`TestResponse`](../backend/app/api/schemas/test.py)와 동일한 필드(camelCase)입니다.

### POST /tests

테스트 생성. **201** + Test 객체.

| 구분 | 필드 (camelCase) | 비고 |
|------|------------------|------|
| 필수 | `name`, `targetUrl`, `httpMethod`, `vus`, `duration` | URL은 `https?://` 형식 |
| 자주 씀 | `engine` | `http`(기본) 또는 `browser` |
| 자주 씀 | `queryParams` | JSON **문자열**. 예: 키·값 배열 직렬화 |
| 자주 씀 | `requestBody`, `headers` | 문자열(JSON 텍스트 등) |
| 부하 옵션 | `requestDelay`, `rampUp`, `iterations` | |
| UI·실행 | `bodyPreviewSize`, `vuUrlSuffix`, `vuStart` | |
| 실패 판별 | `errorPageRules` 또는 레거시 `errorPagePattern` + `errorPageMatchMode` | |
| 고급 | `httpScenario` | k6 다단계. 있으면 1단계 URL·메서드가 `targetUrl` 등과 동기화 |
| 고급 | `browserActions` | `engine=browser`일 때만 유지, 아니면 무시 |

### PUT /tests/{id}

부분 수정. 요청에 **포함한 필드만** 갱신됩니다.

- `httpScenario` 키를 **보내지 않으면** 기존 시나리오를 그대로 둡니다. 단, 결과 `engine`이 `browser`이면 시나리오는 저장소에서 비워집니다.
- `browserActions` 키를 **보내지 않으면** 기존 액션을 그대로 둡니다. 단, 결과 `engine`이 `http`이면 액션은 비워집니다.
- 구현: [`backend/app/api/tests.py`](../backend/app/api/tests.py), [`test_repository.py`](../backend/app/services/test_repository.py).

### GET /tests, GET /tests/{id}

- 목록: 객체 하나에 `items` 배열.
- 단건: 404 시 테스트 없음.

### DELETE /tests/{id}

**204**, 본문 없음.

### 응답 Test 객체 필드

`id`, `name`, `engine`, `targetUrl`, `queryParams`, `httpMethod`, `requestBody`, `headers`, `vus`, `duration`, `requestDelay`, `rampUp`, `iterations`, `bodyPreviewSize`, `vuUrlSuffix`, `vuStart`, `errorPageRules`, `errorPagePattern`, `errorPageMatchMode`, `httpScenario`, `browserActions`, `createdAt`, `updatedAt`.

---

## 실행·결과·로그

### POST /tests/{test_id}/runs

실행 시작. **201** + Run 객체.

- 사용 엔진은 **항상 해당 테스트에 저장된 `engine`**입니다. 요청 본문으로 엔진을 바꾸지 않습니다.
- 본문은 생략 가능. 넣을 때:
  - `requestHeaderOverrides`: 객체. 실행 중 나가는 요청 헤더에 합치며, 테스트에 저장된 헤더보다 우선합니다.
  - `showBrowser`: `true`이면 브라우저 모드에서 헤드리스를 끄고 창 표시를 시도합니다(로컬·DISPLAY 등 필요).

동시에 **Running**인 실행은 하나만 허용됩니다. 이미 있으면 **400**.

### POST /runs/{run_id}/stop

Running이면 k6 또는 브라우저 프로세스를 중지하고 Run 상태를 갱신합니다.

### GET /runs

쿼리: `page`(기본 1), `limit`(기본 20), `test_id`(선택).

응답: `items` 배열. 원소 필드: `id`, `testId`, `testName`, `engine`, `status`, `startedAt`, `finishedAt`, `createdAt`, `resultSummary`(선택). `resultSummary`가 있으면 `avgResponseTime`, `failureRate`, `overallFailureRate`.

### GET /runs/{run_id}

Run 한 건. 가능하면 `testName` 포함.

### DELETE /runs/{run_id}

**204**. 실행 중이면 **400**.

### GET /runs/{run_id}/logs

JSON 한 개 객체, 키 `log`에 러너 로그 전체 문자열.

### GET /runs/{run_id}/requests

쿼리: `limit`(기본 1000), `offset`(기본 0), `sort`(기본 `vuTrace`).

응답: `items`, `total`. 각 `items` 원소: `seq`, `statusCode`, `responseTimeMs`, `bodyPreview`, `requestedAt`(UTC ISO 8601), `requestArgs`(JSON 문자열), `failed`.

### GET /runs/{run_id}/result

[`ResultResponse`](../backend/app/api/schemas/result.py) 형태. 결과 없으면 **404**.

- 루트: `runId`, `avgResponseTime`, `maxResponseTime`, `failureRate`, `overallFailureRate`, `requestCount`, `tpsOrRps`, `executionTime`, `errorMessage`, `lcpMs`, `fcpMs`, `cls`, `ttfbMs`, `bodyPreviewSize`, `stepSummaries`.
- `stepSummaries` 항목: `stepIndex`, `stepName`, `requestCount`, `avgResponseTime`, `maxResponseTime`, `failureRate`, `tpsOrRps`.

### GET /runs/{run_id}/screenshots/{vu_index}

- `vu_index`: 0부터.
- 저장 행은 `seq = vu_index + 1`에 대응.
- 응답 본문: 이미지 바이너리. 헤더 **Content-Type: image/jpeg**.

---

## POST /uploads/k6-fixture

| 항목 | 내용 |
|------|------|
| 형식 | `multipart/form-data`, 파트 이름 `file` |
| 크기 | 최대 50MB, 초과 시 **413** |
| 성공 | **200**, JSON: `filePath`(서버 절대 경로), `fileName`, `contentType` |

k6 스크립트에서 업로드된 파일을 읽을 때는 API와 같은 호스트에서 접근 가능한 경로여야 합니다.

---

## HTTP 상태 코드

| 코드 | 용도 |
|------|------|
| 200 | 조회·중지·업로드 성공 |
| 201 | 테스트·실행 생성 |
| 204 | 삭제 성공 |
| 400 | 정책 위반(예: 다른 실행이 이미 Running, Running 삭제) |
| 404 | 리소스 없음 |
| 413 | 업로드 용량 초과 |
| 422 | 요청 검증 실패 |
| 503 | k6 또는 브라우저 러너 사용 불가 |

Compose 포트·서비스 구성은 [architecture.md](./architecture.md)를 참고하세요.
</think>


<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
StrReplace