# graphio-performance-tester

웹 UI에서 성능 테스트를 정의·실행하고, HTTP 부하는 [k6](https://k6.io/), 브라우저 측정은 Playwright로 수행합니다. 시계열 메트릭은 InfluxDB에 저장되고 Grafana에서 확인할 수 있습니다.

## 주요 기능

- 테스트 생성·수정·삭제 및 목록·상세 조회
- 실행 시작·중지, 로그·요청별 기록·결과 요약·스크린샷(브라우저 시나리오)
- **HTTP(k6)** / **브라우저(Playwright, Web Vitals 등)** 엔진 선택
- 앱 메타데이터는 SQLite(기본) 또는 PostgreSQL, 부하 메트릭은 InfluxDB, 대시보드는 Grafana

## 기술 스택

| 구분 | 기술 |
|------|------|
| 프론트엔드 | Vue 3, Vite |
| API | FastAPI, Python 3.14+ |
| HTTP 부하 | k6 |
| 브라우저 | Playwright |
| 앱 DB | SQLite 또는 PostgreSQL |
| 메트릭 | InfluxDB 1.x |
| 대시보드 | Grafana |
| 배포 | Docker Compose |

## 빠른 시작 (Docker)

저장소 루트에서 전체 스택(API · UI · InfluxDB · Grafana)을 기동합니다.

```bash
docker compose -f docker/compose.yaml up --build
```

기동 후 브라우저에서 아래 주소로 접속할 수 있습니다.

| 서비스 | URL | 비고 |
|--------|-----|------|
| 웹 UI | http://localhost:3000 | |
| API | http://localhost:8080 | 헬스: `GET /health` |
| Grafana | http://localhost:3001 | 기본 계정 `admin` / `admin` (Compose 기준) |
| InfluxDB | http://localhost:8086 | DB 이름 `k6` (Compose 환경 변수) |

## 로컬 개발

전체 스택 없이 API만, UI만 띄울 때는 각 디렉터리 README를 따릅니다.

- **백엔드**: [backend/README.md](backend/README.md) — `uv sync`, Alembic 마이그레이션, `uvicorn`
- **프론트엔드**: [frontend/README.md](frontend/README.md) — `npm install`, `npm run dev`, `VITE_API_URL`로 API 주소 지정

## 문서

- [아키텍처·포트·구성 요소](docs/architecture.md)
- [HTTP API](docs/api.md)
- [데이터베이스 스키마](docs/database.md)
