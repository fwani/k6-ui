{% raw %}import http from 'k6/http';
import {% endraw %}{{ '{ check, sleep }' }}{% raw %} from 'k6';

const PLACEHOLDER_VU = {% endraw %}{{ placeholder_js }}{% raw %};
const STEPS = {% endraw %}{{ steps_json | safe }}{% raw %};

function buildUrl(base, queryParams) {
  const b = base == null ? '' : String(base);
  if (!queryParams || !queryParams.length) return b;
  const pairs = [];
  for (let i = 0; i < queryParams.length; i++) {
    const item = queryParams[i];
    if (!item || item.key == null) continue;
    const k = String(item.key).trim();
    if (!k) continue;
    const v = item.value == null ? '' : String(item.value);
    pairs.push(encodeURIComponent(k) + '=' + encodeURIComponent(v));
  }
  if (!pairs.length) return b;
  return b + (b.indexOf('?') !== -1 ? '&' : '?') + pairs.join('&');
}

function replacePlaceholders(s, vu, vars) {
  let out = s == null ? '' : String(s);
  out = out.split(PLACEHOLDER_VU).join(String(vu));
  const keys = Object.keys(vars || {});
  for (let i = 0; i < keys.length; i++) {
    const k = keys[i];
    const token = '{{' + k + '}}';
    const val = vars[k] == null ? '' : String(vars[k]);
    out = out.split(token).join(val);
  }
  return out;
}

function jsonPath(obj, path) {
  if (obj == null || !path) return null;
  const parts = String(path).split('.');
  let x = obj;
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i];
    if (x == null || typeof x !== 'object') return null;
    x = x[p];
  }
  return x;
}

/** Set-Cookie 한 덩어리(또는 합쳐진 문자열)에서 name=value 의 value 만. ; 뒤(Path 등)는 제외. */
function cookieValueFromHeaderLine(headerVal, cookieName) {
  if (headerVal == null || cookieName == null) return '';
  const cn = String(cookieName).trim();
  if (!cn) return String(headerVal);
  const s = String(headerVal);
  let esc = '';
  for (let i = 0; i < cn.length; i++) {
    const c = cn[i];
    if ('.*+?^${}()|[]\\'.indexOf(c) >= 0) esc += '\\' + c;
    else esc += c;
  }
  const re = new RegExp('(?:^|[,;]\\s*)' + esc + '=([^;]*)', 'i');
  const m = s.match(re);
  if (!m) return '';
  return (m[1] || '').trim();
}

{% endraw %}
{% if error_rules_js %}
function __errorPageRuleFailedSc(_urlStr, _bodyStr, rules) {
  if (!rules || !rules.length) return false;
  for (let i = 0; i < rules.length; i++) {
    const p = rules[i].pattern;
    if (!p) continue;
    const notContains = rules[i].matchMode === 'not_contains';
    const found = _urlStr.indexOf(p) !== -1 || _bodyStr.indexOf(p) !== -1;
    if (notContains ? !found : found) return true;
  }
  return false;
}
const ERROR_PAGE_RULES = {{ error_rules_js }};
{% endif %}
{% raw %}

function doStepRequest(method, url, bodyStr, headersObj, tags) {
  const params = { headers: headersObj, tags: tags };
  const m = (method || 'GET').toUpperCase();
  if (m === 'GET') return http.get(url, params);
  if (m === 'POST') return http.post(url, bodyStr, params);
  if (m === 'PUT') return http.put(url, bodyStr, params);
  if (m === 'PATCH') return http.patch(url, bodyStr, params);
  if (m === 'DELETE') return http.del(url, params);
  return http.request(m, url, bodyStr, params);
}

export const options = {
{% endraw %}
{{ options_js }}{% raw %}};

export default function () {
{% endraw %}  const vu = __VU + {{ vu_offset }};{% raw %}
  const vars = {};
  for (let si = 0; si < STEPS.length; si++) {
    const step = STEPS[si];
    const stepName = step.name || ('step_' + (si + 1));
    const rawUrl = step.urlTemplate;
    const url = replacePlaceholders(buildUrl(rawUrl, step.queryParams || []), vu, vars);
    const headersObj = {};
    const srcH = step.headers || {};
    for (const k of Object.keys(srcH)) {
      headersObj[k] = replacePlaceholders(String(srcH[k]), vu, vars);
    }
    const bodyStr = replacePlaceholders(step.bodyTemplate == null ? '' : String(step.bodyTemplate), vu, vars);
    const method = step.method || 'GET';
    const mup = (method || '').toUpperCase();
    if (['POST', 'PUT', 'PATCH'].indexOf(mup) !== -1 && bodyStr && !Object.keys(headersObj).some(function (hk) { return hk.toLowerCase() === 'content-type'; })) {
      headersObj['Content-Type'] = 'application/json';
    }
    const tags = { name: stepName };
    const reqStartMs = Date.now();
    const requestedAt = new Date(reqStartMs).toISOString().replace(/(\.\d+)Z$/i, (_, frac) => (frac + '000000').slice(0, 7) + 'Z');
    const res = doStepRequest(method, url, bodyStr, headersObj, tags);
    const reqEndMs = Date.now();
    const respondedAt = new Date(reqEndMs).toISOString().replace(/(\.\d+)Z$/i, (_, frac) => (frac + '000000').slice(0, 7) + 'Z');
    const wallMs = reqEndMs - reqStartMs;
    const k6Dur = res && res.timings && typeof res.timings.duration === 'number' ? res.timings.duration : null;
    const duration = wallMs;
    const cap = step.capture;
    if (cap && cap.var && res && res.status >= 200 && res.status < 300) {
      try {
        const src = (cap.from || 'json').toLowerCase();
        if (src === 'header' && cap.header) {
          const want = String(cap.header).trim().toLowerCase();
          let hv = '';
          if (res.headers) {
            const keys = Object.keys(res.headers);
            for (let hi = 0; hi < keys.length; hi++) {
              if (String(keys[hi]).toLowerCase() === want) {
                hv = res.headers[keys[hi]];
                break;
              }
            }
          }
          let rawH = hv == null ? '' : String(hv);
          if (cap.cookieName && String(cap.cookieName).trim()) {
            rawH = cookieValueFromHeaderLine(rawH, cap.cookieName);
          }
          vars[cap.var] = rawH;
        } else if (cap.path) {
          const j = res.json();
          const val = jsonPath(j, cap.path);
          vars[cap.var] = val == null ? '' : String(val);
        }
      } catch (e) {}
    }
{% endraw %}
{% if error_rules_js %}
    const _urlStr = res && res.url != null ? String(res.url) : String(url);
    const _bodyStr = res && res.body != null ? String(res.body) : '';
    var errorPageFailed = __errorPageRuleFailedSc(_urlStr, _bodyStr, ERROR_PAGE_RULES);
    check(res, { ['no error page (' + stepName + ')']: () => !__errorPageRuleFailedSc(_urlStr, _bodyStr, ERROR_PAGE_RULES) });
{% else %}
    var errorPageFailed = false;
{% endif %}
{% raw %}    check(res, { ['status 2xx (' + stepName + ')']: (r) => r != null && r.status >= 200 && r.status < 300 });
    const bodyFull = (res && res.body != null) ? String(res.body) : '';
    const status = (res != null && res.status != null) ? (typeof res.status === 'number' ? res.status : parseInt(res.status, 10)) : null;
    const requestArgs = { url: url, method: method, headers: headersObj, body: bodyStr, step: stepName, stepIndex: si };
    console.log('__REQ__' + JSON.stringify({ vu: vu, scenarioIter: __ITER, status: status, duration: duration, k6TimingsDurationMs: k6Dur, body: bodyFull, requestedAt: requestedAt, respondedAt: respondedAt, requestArgs: requestArgs, failed: errorPageFailed }) + '__REQEND__');
    const pauseAfter = step.sleepAfterSeconds;
    if (pauseAfter != null && Number(pauseAfter) > 0) sleep(Number(pauseAfter));
  }
  sleep({% endraw %}{{ sleep_s }}{% raw %});
}

const SUMMARY_MARKER = '__K6_SUMMARY_JSON__';
const SUMMARY_END = '__K6_SUMMARY_END__';
export function handleSummary(data) {
  return { stdout: SUMMARY_MARKER + JSON.stringify(data) + SUMMARY_END };
}
{% endraw %}
