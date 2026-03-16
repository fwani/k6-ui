# Quickstart: UI 기반 성능 테스트 환경

**Feature**: 001-ui-perf-test-env  
**Date**: 2025-03-16

구현 완료 후 개발자가 로컬에서 전체 환경을 기동하고 첫 테스트를 실행하는 최소 절차.

---

## 사전 요구사항

- Docker, Docker Compose 설치
- (로컬에서 API/UI만 실행할 경우) Python 3.14+, Node.js (frontend), pip 또는 uv (backend)

---

## 1. 전체 환경 한 번에 기동 (권장)

저장소 루트에서:

```bash
docker compose up
```

또는

```bash
docker-compose up
```

다음 서비스가 기동해야 한다 (구현 시 compose 파일에 정의).

- **UI**: 웹 UI (예: http://localhost:3000)
- **API**: 백엔드 API (예: http://localhost:8080)
- **Grafana**: 대시보드 (예: http://localhost:3001)
- **메트릭 저장소**: InfluxDB 등 (내부 전용 포트)
- **k6**: 테스트 실행 시 API가 호출하는 러너(작업자/사이드카 등)

실제 포트·서비스명은 구현된 `compose.yaml`(또는 `docker-compose.yml`)을 따른다.

---

## 2. 첫 테스트 실행

1. 브라우저에서 **UI** 주소 접속.
2. **테스트 생성** 화면에서 다음만 입력해도 됨:
   - 테스트 이름
   - 대상 URL (예: `https://httpbin.org/get`)
   - HTTP 메서드 (GET)
   - 동시 사용자 수(VUs), 테스트 지속 시간
3. 저장 후 **테스트 실행** 화면에서 **시작**.
4. **상태**가 Running → Finished로 바뀌면 **테스트 결과** 화면에서 평균 응답 시간·실패율·요청 수 등 확인.
5. **Grafana 링크**로 이동해 요청 수/초·응답 시간·에러율 등 시각화 확인.
6. **테스트 목록** 화면에서 방금 실행한 항목(이름·실행 시간·상태·요약) 확인.

---

## 3. (선택) 로컬에서 API/UI만 실행

백엔드·프론트를 Docker 없이 실행하려면:

- **백엔드 (Python FastAPI)**: `backend/`에서 `uv sync` 후 `uv run uvicorn app.main:app --reload`.
- **프론트 (Vue.js)**: `frontend/`에서 `npm install` 또는 `pnpm install` 후 `npm run dev` 또는 `pnpm dev`.
- 메트릭·Grafana·k6 실행 환경은 Docker Compose로만 띄우거나, 로컬에 InfluxDB·Grafana를 별도 설치해 연결.

구체 명령은 구현된 `backend/README.md`, `frontend/README.md`를 참고.

---

## 4. 볼륨 초기화

DB·InfluxDB·Grafana 데이터를 모두 지우고 처음부터 쓰려면:

```bash
docker compose -f docker/compose.yaml down -v
docker compose -f docker/compose.yaml up --build
```

`-v`는 이 compose에 정의된 볼륨(api_data, influxdb_data, grafana_data)을 삭제합니다.

---

## 5. 문제 해결

- **대시보드에 데이터가 안 보임**: k6가 메트릭 저장소로 전송하는지, Grafana 데이터 소스가 해당 저장소를 가리키는지 확인.
- **테스트가 Failed로 끝남**: API 로그·k6 로그에서 대상 URL 접근 실패·타임아웃 등 원인 확인.
- **동시에 두 테스트 실행 불가**: MVP에서는 한 번에 하나만 실행 가능. 이미 Running인 Run이 있으면 새 실행 요청은 400 등으로 거부된다.
- **스키마/볼륨 꼬임**: `docker compose -f docker/compose.yaml down -v` 후 다시 `up --build`.
