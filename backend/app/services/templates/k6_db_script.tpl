{% raw %}import sql from 'k6/x/sql';
import { Trend, Rate } from 'k6/metrics';
import { sleep } from 'k6';
{% endraw %}
import driver from {{ driver_import_js }};

{% raw %}// DB 쿼리 1회 실행 시간(ms). HTTP의 http_req_duration 대용.
const queryDuration = new Trend('query_duration', true);
// 쿼리 실패율. HTTP의 http_req_failed 대용.
const queryErrors = new Rate('query_errors');
{% endraw %}
const DSN = {{ dsn_js }};
const QUERY = {{ query_js }};
const DRIVER_ID = {{ driver_id_js }};

const db = sql.open(driver, DSN);

{% raw %}export const options = {
{% endraw %}
{{ options_js }}{% raw %}};

export default function () {
  const iso = new Date().toISOString();
  const requestedAt = iso.replace(/(\.\d+)Z$/i, (_, frac) => (frac + '000000').slice(0, 7) + 'Z');
  const t0 = Date.now();
  let failed = false;
  let bodyStr = '';
  try {
    // xk6-sql v1.x: db.query(...), 구버전(v0.x): sql.query(db, ...)
    const rows = (typeof db.query === 'function') ? db.query(QUERY) : sql.query(db, QUERY);
    const rowCount = Array.isArray(rows) ? rows.length : 0;
    let sample = null;
    if (rowCount > 0) {
      try { sample = rows[0]; } catch (_) { sample = null; }
    }
    bodyStr = JSON.stringify({ rowCount: rowCount, sample: sample });
  } catch (e) {
    failed = true;
    bodyStr = String(e && e.message ? e.message : e);
  }
  const dur = Date.now() - t0;
  queryDuration.add(dur);
  queryErrors.add(failed);
{% endraw %}  const requestArgs = { driver: DRIVER_ID, query: QUERY };
{% raw %}  const status = failed ? 0 : 200;
  console.log('__REQ__' + JSON.stringify({ vu: __VU, scenarioIter: __ITER, status: status, duration: dur, body: bodyStr, requestedAt: requestedAt, requestArgs: requestArgs, failed: failed }) + '__REQEND__');
  sleep({% endraw %}{{ sleep_s }}{% raw %});
}

export function teardown() {
  try { db.close(); } catch (_) {}
}

const SUMMARY_MARKER = '__K6_SUMMARY_JSON__';
const SUMMARY_END = '__K6_SUMMARY_END__';
export function handleSummary(data) {
  return { stdout: SUMMARY_MARKER + JSON.stringify(data) + SUMMARY_END };
}
{% endraw %}
