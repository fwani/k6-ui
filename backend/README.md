# 성능 테스트 API (Backend)

FastAPI 기반 백엔드. 테스트 정의·실행·결과 조회 API를 제공합니다.

## 요구 사항

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (패키지/가상환경 관리)

## 설치 및 실행

```bash
cd backend
uv sync
uv run alembic upgrade head   # 최초 1회 또는 스키마 변경 후
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

DB 스키마는 Alembic으로 관리됩니다. 새 DB이거나 스키마 변경 후에는 `uv run alembic upgrade head`를 실행하세요.

개발 의존성(pytest, ruff) 포함 설치:

```bash
uv sync --extra dev
```

## 환경 변수

로컬 실행 시 **`.env` 파일**로 설정 (backend/.env 또는 프로젝트 루트 .env).

| 변수 | 설명 |
|------|------|
| `DATABASE_URL` | DB 연결 문자열 (예: `sqlite:///./app.db` 또는 PostgreSQL URL) |
| `GRAFANA_DASHBOARD_URL` | Grafana 대시보드 URL (결과 화면 링크용) |
| `INFLUXDB_URL` | InfluxDB URL (메트릭 저장소) |

예시: `cp .env.example .env` 후 값 수정.

## Docker로 실행

저장소 루트에서 전체 스택(API + UI + InfluxDB + Grafana) 기동:

```bash
docker compose -f docker/compose.yaml up --build
```

API만 사용 시: `http://localhost:8080`, UI: `http://localhost:3000`, Grafana: `http://localhost:3001`.

## 마이그레이션 (Alembic)

- 적용: `uv run alembic upgrade head`
- 새 리비전 생성: `uv run alembic revision -m "설명" --autogenerate`

## 린트

```bash
uv run ruff check .
```
