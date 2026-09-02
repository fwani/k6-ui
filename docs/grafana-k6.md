# Grafana에서 k6 결과 보기

## 기본 대시보드 URL

- 앱에서 **Grafana 대시보드 열기** 버튼이 이 URL로 연결됩니다.
- 백엔드 `.env`에 다음처럼 설정하면 됩니다.

```env
GRAFANA_DASHBOARD_URL=http://localhost:3001/d/k6-load-testing/k6-load-testing-results
```

- Docker Compose 사용 시 Grafana 포트가 3001이면 위 주소 그대로 사용 가능합니다.
- `uid`가 `k6-load-testing`으로 고정되어 있어, 프로비저닝된 k6 대시보드 주소가 바뀌지 않습니다.

## k6 결과를 어떻게 보나요?

1. **테스트 실행**  
   테스트 실행 시 k6가 InfluxDB로 메트릭을 보냅니다 (`INFLUXDB_URL` 설정 시).

2. **결과 페이지**  
   실행이 끝난 뒤 **테스트 결과** 페이지에서 요약(평균/최대 응답 시간, 실패율, TPS 등)을 볼 수 있습니다.

3. **Grafana에서 상세 보기**  
   같은 결과 페이지의 **Grafana 대시보드 열기**를 누르면 Grafana의 k6 대시보드가 열립니다.  
   여기서 볼 수 있는 것:
   - **Virtual Users** – 가상 사용자 수
   - **Requests per second** – 초당 요청 수
   - **HTTP 요청 지속 시간** – 응답 시간 분포
   - **Errors per second** – 초당 실패 수
   - **Checks** – 체크 통과/실패

4. **시간 범위**  
   Grafana 우측 상단에서 해당 실행 구간으로 시간 범위를 잡으면, 그 실행만 필터해서 볼 수 있습니다.

## Browser Web Vitals 대시보드

- **브라우저(Chromium) 엔진**으로 실행한 Run은 Web Vitals(LCP, FCP, TTFB, CLS)를 InfluxDB `browser_vitals` measurement에 기록합니다.
- Grafana에 **Browser Web Vitals** 대시보드가 프로비저닝되어 있으며, 같은 InfluxDB(k6 DB)를 사용합니다.
- 결과 페이지에서 렌더링 메트릭이 있을 때 **Grafana (Browser Web Vitals)** 버튼이 보이며, 클릭 시 해당 대시보드로 이동합니다.
- 브라우저 대시보드 URL은 `GRAFANA_DASHBOARD_URL`과 같은 호스트/포트에 `/d/browser-web-vitals/browser-web-vitals` 경로로 자동 유도됩니다. 별도로 쓰려면 `GRAFANA_BROWSER_VITALS_URL`을 설정하면 됩니다.

### Browser Web Vitals에 데이터가 안 나올 때

1. **API 환경 변수**: 브라우저 Run을 실행하는 API 서버에 `INFLUXDB_URL`이 설정되어 있어야 합니다 (예: Docker 시 `INFLUXDB_URL=http://influxdb:8086`).
2. **API 로그**: 브라우저 Run이 끝난 뒤 로그에 `influxdb write browser_vitals ok run_id=...`가 있으면 전송 성공입니다. 실패 시 `influxdb write browser_vitals status=...` 또는 exception 로그가 남습니다.
3. **InfluxDB에 measurement 확인**: `influx -database k6 -execute "SHOW MEASUREMENTS"` 또는 curl로 `browser_vitals`가 있는지 확인합니다. 있으면 Grafana 시간 범위(우측 상단)를 **Last 6 hours** 등으로 넓혀 보세요.

## k6 → InfluxDB 저장 확인 방법

k6가 InfluxDB에 잘 쓰고 있는지 확인하려면 아래를 순서대로 해보면 됩니다.

### 1. HTTP API로 확인 (curl)

InfluxDB가 떠 있는 상태에서 (Docker: `localhost:8086`, 로컬 InfluxDB면 해당 호스트/포트로):

**DB 목록·측정 항목 보기**

```bash
# k6 DB에 measurement(테이블) 목록
curl -s -G 'http://localhost:8086/query?pretty=true' \
  --data-urlencode "db=k6" \
  --data-urlencode "q=SHOW MEASUREMENTS"
```

k6가 한 번이라도 데이터를 보냈다면 `vus`, `http_req_duration`, `http_reqs` 등이 나옵니다. 결과가 비어 있으면 아직 k6에서 한 건도 안 보낸 상태입니다.

**최근 데이터 개수 확인 (예: vus)**

```bash
# vus measurement 최근 1시간 포인트 수
curl -s -G 'http://localhost:8086/query?pretty=true' \
  --data-urlencode "db=k6" \
  --data-urlencode "q=SELECT count(value) FROM vus WHERE time > now() - 1h"
```

### 2. Docker 안에서 InfluxDB CLI로 확인

InfluxDB가 Docker로 떠 있을 때:

```bash
# 컨테이너 이름은 docker compose 기준 (예: docker_influxdb_1 또는 compose 프로젝트명에 따라 다름)
docker compose -f docker/compose.yaml exec influxdb influx -database k6 -execute "SHOW MEASUREMENTS"
```

`vus`, `http_req_duration` 등이 보이면 k6가 InfluxDB에 저장하고 있는 것입니다.

### 3. 확인 순서 요약

1. 앱에서 테스트 한 번 실행 (InfluxDB URL이 설정된 환경에서).
2. 위 curl 또는 `influx -execute "SHOW MEASUREMENTS"`로 `k6` DB에 measurement가 생겼는지 확인.
3. 있으면 Grafana 대시보드에서 시간 범위를 **Last 1 hour** 등으로 두고 새로고침.

### curl에는 나오는데 대시보드에는 No data일 때

1. **Grafana 버전**  
   이 프로젝트는 Grafana 이미지를 **10.2.2**로 고정해 두었습니다. (최신 `latest`는 InfluxDB 데이터 소스를 Flux로 둘 수 있어 1.x DB에서 No data가 납니다.)

2. **데이터 소스가 InfluxQL이어야 함**  
   - **Connections** → **Data sources** → **InfluxDB** → **Save & test**  
   - 성공 시 문구: **"datasource is working. X measurements found"** (InfluxQL)  
   - **"X buckets found"**라면 Flux 모드입니다. 같은 화면에서 **Query language**를 **InfluxQL**로 바꾼 뒤 **Save & test** 하세요.

3. **프로비저닝이 적용되도록**  
   - 한 번도 쓰지 않은 상태라면: `docker compose -f docker/compose.yaml up -d grafana` 후 위 2번 확인.  
   - 예전에 `grafana:latest`로 켜 둔 적이 있다면, 이미 Flux로 저장된 데이터 소스가 있을 수 있습니다.  
     - **방법 A**: Grafana UI에서 InfluxDB 데이터 소스 열기 → **Query language** → **InfluxQL** 선택 → **Save & test**  
     - **방법 B**: Grafana 볼륨을 비우고 다시 올리기 (대시보드/사용자 설정 초기화됨):
       ```bash
       docker compose -f docker/compose.yaml down
       docker volume rm <grafana_volume_name>  # 이름 확인: docker volume ls | grep grafana
       docker compose -f docker/compose.yaml up -d influxdb grafana
       ```

## "No data"가 나올 때

1. **시간 범위**  
   대시보드 기본값은 **Last 1 hour**입니다. 우측 상단에서 **Last 1 hour** / **Last 6 hours** 등으로 넓혀 보세요. 테스트를 방금 돌렸다면 **Last 15 minutes**로도 확인할 수 있습니다.

2. **InfluxDB에 데이터가 들어가야 함**  
   - 테스트 실행 시 백엔드에 `INFLUXDB_URL`이 설정되어 있어야 k6가 InfluxDB로 메트릭을 보냅니다.  
   - **Docker Compose로 전체 실행**: `api` 서비스에 `INFLUXDB_URL: http://influxdb:8086` 있으면 k6가 InfluxDB에 기록합니다.  
   - **백엔드만 로컬에서 실행**: `INFLUXDB_URL=http://localhost:8086` 로 두고, InfluxDB는 Docker로 띄워 포트 8086을 열어 두세요. (같은 PC에서 `influxdb` 호스트명은 Docker 안에서만 통하므로 로컬에서는 `localhost` 사용.)

3. **InfluxDB·Grafana 상태**  
   - InfluxDB 1.x 사용 중인지 확인 (compose에서는 `influxdb:1.8-alpine`).  
   - Grafana 데이터 소스가 **InfluxDB**, **database: k6**, **URL: http://influxdb:8086** (Docker 내부)인지 확인.

4. **한 번 테스트 실행**  
   앱에서 테스트를 한 번 실행한 뒤, Grafana에서 시간 범위를 **Last 1 hour**로 두고 새로고침해 보세요.

## 요약

- `GRAFANA_DASHBOARD_URL`에 **k6 기본 대시보드 URL**을 넣으면, 앱에서 한 번에 그 대시보드로 이동할 수 있습니다.
- k6 결과는 **앱 결과 페이지(요약)** + **Grafana(시계열/상세)** 조합으로 보면 됩니다.
- 대시보드 기본 시간은 **Last 1 hour**로 바꿔 두었으므로, 최근에 실행한 테스트는 바로 보이도록 되어 있습니다.
