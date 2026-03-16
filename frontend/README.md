# 성능 테스트 UI (Frontend)

Vue 3 + Vite 기반 웹 UI. 테스트 생성·실행·결과 조회 화면을 제공합니다.

## 요구 사항

- Node.js 18+
- npm, pnpm 또는 yarn

## 설치 및 실행

```bash
cd frontend
npm install
npm run dev
```

개발 서버가 기동되면 브라우저에서 표시된 주소(예: http://localhost:5173)로 접속합니다.

## 환경 변수

| 변수 | 설명 |
|------|------|
| `VITE_API_URL` | 백엔드 API base URL (예: `http://localhost:8080`) |

`.env` 또는 `.env.local`에 설정 (Vite가 자동 로드):

```bash
# 예: cp .env.example .env 후 수정
VITE_API_URL=http://localhost:8080
```

Docker UI 컨테이너는 빌드 시 API를 `http://localhost:8080`으로 가정합니다. 브라우저에서 API에 접근하려면 동일 호스트에서 API가 8080으로 떠 있어야 합니다.

## Docker로 실행

저장소 루트에서 전체 스택 기동 (API + UI + InfluxDB + Grafana):

```bash
docker compose -f docker/compose.yaml up --build
```

UI: `http://localhost:3000`. API는 `http://localhost:8080`에서 접근합니다.

## 스크립트

- `npm run dev` — 개발 서버
- `npm run build` — 프로덕션 빌드
- `npm run preview` — 빌드 결과 미리보기
- `npm run lint` / `npm run lint:fix` — ESLint
- `npm run format` — Prettier
