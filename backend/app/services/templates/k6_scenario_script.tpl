{% raw %}import http from 'k6/http';
import {% endraw %}{{ '{ check, sleep }' }}{% raw %} from 'k6';

const PLACEHOLDER_VU = {% endraw %}{{ placeholder_js }}{% raw %};
{% endraw %}
{% if multipart_open_literals %}
const MULTIPART_FILES = [
{% for lit in multipart_open_literals %}
  open({{ lit }}, 'b'){% if not loop.last %},{% endif %}
{% endfor %}
];
{% endif %}
{% raw %}
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

function pollSuccess(res, stepPoll, vu, vars) {
  if (res == null || stepPoll == null) return false;
  const st = res.status;
  const sn = typeof st === 'number' ? st : parseInt(st, 10);
  if (isNaN(sn)) return false;
  const sl = stepPoll.untilStatusIn;
  if (sl != null && sl.length > 0) {
    for (let i = 0; i < sl.length; i++) {
      if (sn === sl[i]) return true;
    }
  }
  const up = stepPoll.untilJsonPath == null ? '' : String(stepPoll.untilJsonPath).trim();
  if (!up) return false;
  if (stepPoll.untilEquals === undefined || stepPoll.untilEquals === null) return false;
  if (sn < 200 || sn >= 300) return false;
  try {
    const j = res.json();
    const val = jsonPath(j, up);
    const got = val == null ? '' : String(val);
    const want = replacePlaceholders(String(stepPoll.untilEquals), vu, vars);
    return got === want;
  } catch (e) {
    return false;
  }
}

/** whileJsonPath+whileEquals 가 있으면: 2xx에서만 비교, 일치하면 재시도 허용. 비2xx는 계속. 2xx인데 불일치면 false(즉시 실패). while 없으면 true. */
function pollWhileContinue(res, stepPoll, vu, vars) {
  const wp = stepPoll.whileJsonPath == null ? '' : String(stepPoll.whileJsonPath).trim();
  if (!wp) return true;
  if (res == null) return true;
  const st = res.status;
  const sn = typeof st === 'number' ? st : parseInt(st, 10);
  if (isNaN(sn) || sn < 200 || sn >= 300) return true;
  if (stepPoll.whileEquals === undefined || stepPoll.whileEquals === null) return false;
  try {
    const j = res.json();
    const val = jsonPath(j, wp);
    const got = val == null ? '' : String(val);
    const want = replacePlaceholders(String(stepPoll.whileEquals), vu, vars);
    return got === want;
  } catch (e) {
    return false;
  }
}

/** 백엔드 _parse_scenario_poll 과 동일 조건. 불완전한 poll 객체는 null → 단일 요청만 수행. */
function resolveStepPoll(raw) {
  if (raw == null || typeof raw !== 'object' || Array.isArray(raw)) return null;
  var iv = Number(raw.intervalSeconds);
  var md = Number(raw.maxDurationSeconds);
  if (!(isFinite(iv) && isFinite(md) && iv >= 0.1 && iv <= 60 && md >= 0.5 && md <= 600)) return null;
  var out = { intervalSeconds: iv, maxDurationSeconds: md };
  var ujp = raw.untilJsonPath == null ? '' : String(raw.untilJsonPath).trim();
  if (ujp) out.untilJsonPath = ujp;
  if (raw.untilEquals !== undefined && raw.untilEquals !== null) out.untilEquals = String(raw.untilEquals);
  var usi = raw.untilStatusIn;
  if (usi != null && usi.length > 0) {
    var arr = [];
    for (var ui = 0; ui < usi.length; ui++) {
      var sn = parseInt(usi[ui], 10);
      if (isNaN(sn)) return null;
      arr.push(sn);
    }
    out.untilStatusIn = arr;
  }
  var wjp = raw.whileJsonPath == null ? '' : String(raw.whileJsonPath).trim();
  if (wjp) out.whileJsonPath = wjp;
  if (raw.whileEquals !== undefined && raw.whileEquals !== null) out.whileEquals = String(raw.whileEquals);
  if (out.whileJsonPath && out.whileEquals === undefined) return null;
  if (out.whileEquals !== undefined && out.whileEquals !== null && !out.whileJsonPath) return null;
  var hasJ = !!(out.untilJsonPath && String(out.untilJsonPath).trim()) && out.untilEquals !== undefined;
  var hasS = out.untilStatusIn && out.untilStatusIn.length > 0;
  if (!hasJ && !hasS) return null;
  if (out.untilJsonPath && String(out.untilJsonPath).trim() && out.untilEquals === undefined) return null;
  return out;
}

function applyStepCapture(cap, res, vu, vars) {
  if (!cap || !cap.var || !res || res.status < 200 || res.status >= 300) return;
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
const DEFAULT_ERROR_PAGE_RULES = {{ error_rules_js }};
{% raw %}

function headersWithoutContentType(headersObj) {
  const h2 = {};
  for (const k of Object.keys(headersObj || {})) {
    if (k.toLowerCase() === 'content-type') continue;
    h2[k] = headersObj[k];
  }
  return h2;
}

function doStepRequest(method, url, bodyStr, headersObj, tags, multipartFd) {
  const m = (method || 'GET').toUpperCase();
  if (multipartFd != null) {
    const h2 = headersWithoutContentType(headersObj);
    const params = { headers: h2, tags: tags };
    if (m === 'POST') return http.post(url, multipartFd, params);
    if (m === 'PUT') return http.put(url, multipartFd, params);
    if (m === 'PATCH') return http.patch(url, multipartFd, params);
    return http.request(m, url, multipartFd, params);
  }
  const params = { headers: headersObj, tags: tags };
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
  function runScenarioStep(step, si) {
    const stepErrRules = (step.errorPageRules && step.errorPageRules.length) ? step.errorPageRules : DEFAULT_ERROR_PAGE_RULES;
    const stepName = step.name || ('step_' + (si + 1));
    const rawUrl = step.urlTemplate;
    const url = replacePlaceholders(buildUrl(rawUrl, step.queryParams || []), vu, vars);
    const headersObj = {};
    const srcH = step.headers || {};
    for (const k of Object.keys(srcH)) {
      headersObj[k] = replacePlaceholders(String(srcH[k]), vu, vars);
    }
    const method = step.method || 'GET';
    const mup = (method || '').toUpperCase();
    let bodyStr = '';
    let requestArgsBody = null;
    let multipartFd = null;
    if (step.bodyMode === 'multipart') {
      const mpIdx = step.multipartOpenIndex;
      const fileField = step.multipartFileField;
      const fnT = step.multipartFilenameTemplate == null ? '' : String(step.multipartFilenameTemplate);
      const fn = replacePlaceholders(fnT, vu, vars) || 'upload.bin';
      const ctRaw = step.multipartContentType == null ? '' : String(step.multipartContentType).trim();
      const ctUse = ctRaw || 'application/octet-stream';
      const fd = {};
      const mfields = step.multipartFields || [];
      for (let fi = 0; fi < mfields.length; fi++) {
        const fk = mfields[fi].key;
        if (fk == null || !String(fk).trim()) continue;
        fd[String(fk).trim()] = replacePlaceholders(mfields[fi].value == null ? '' : String(mfields[fi].value), vu, vars);
      }
      fd[fileField] = http.file(MULTIPART_FILES[mpIdx], fn, ctUse);
      multipartFd = fd;
      requestArgsBody = {
        mode: 'multipart',
        filePath: '(k6 host path)',
        fileField: fileField,
        filename: fn,
        contentType: ctUse,
        fieldKeys: Object.keys(fd).filter(function (x) { return x !== fileField; }),
      };
    } else {
      bodyStr = replacePlaceholders(step.bodyTemplate == null ? '' : String(step.bodyTemplate), vu, vars);
      if (['POST', 'PUT', 'PATCH'].indexOf(mup) !== -1 && bodyStr && !Object.keys(headersObj).some(function (hk) { return hk.toLowerCase() === 'content-type'; })) {
        headersObj['Content-Type'] = 'application/json';
      }
      requestArgsBody = bodyStr;
    }
    const tags = { name: stepName };
    const stepPoll = resolveStepPoll(step.poll);
    let res = null;
    if (stepPoll != null) {
      let pollOk = false;
      let pollAttempt = 0;
      let pollWallStart = null;
      let anyRuleFailed = false;
      let sumK6DurMs = 0;
      let firstRequestedAt = null;
      let lastRespondedAt = null;
      let lastBodyFull = '';
      let lastStatus = null;
      const deadline = Date.now() + Number(stepPoll.maxDurationSeconds) * 1000;
      const intervalSec = Number(stepPoll.intervalSeconds);
      while (true) {
        pollAttempt += 1;
        if (pollWallStart === null) pollWallStart = Date.now();
        const reqStartMs = Date.now();
        const requestedAt = new Date(reqStartMs).toISOString().replace(/(\.\d+)Z$/i, (_, frac) => (frac + '000000').slice(0, 7) + 'Z');
        if (firstRequestedAt === null) firstRequestedAt = requestedAt;
        res = doStepRequest(method, url, bodyStr, headersObj, tags, multipartFd);
        const reqEndMs = Date.now();
        const respondedAt = new Date(reqEndMs).toISOString().replace(/(\.\d+)Z$/i, (_, frac) => (frac + '000000').slice(0, 7) + 'Z');
        lastRespondedAt = respondedAt;
        const k6Dur = res && res.timings && typeof res.timings.duration === 'number' ? res.timings.duration : null;
        if (k6Dur != null && typeof k6Dur === 'number') sumK6DurMs += k6Dur;
        const bodyFull = (res && res.body != null) ? String(res.body) : '';
        lastBodyFull = bodyFull;
        const status = (res != null && res.status != null) ? (typeof res.status === 'number' ? res.status : parseInt(res.status, 10)) : null;
        lastStatus = status;
        const _urlStrPoll = res && res.url != null ? String(res.url) : String(url);
        const _bodyStrPoll = res && res.body != null ? String(res.body) : '';
        var errorPageFailed = __errorPageRuleFailedSc(_urlStrPoll, _bodyStrPoll, stepErrRules);
        if (errorPageFailed) anyRuleFailed = true;
        if (pollSuccess(res, stepPoll, vu, vars)) {
          pollOk = true;
          break;
        }
        if (!pollWhileContinue(res, stepPoll, vu, vars)) {
          break;
        }
        if (Date.now() >= deadline) break;
        if (intervalSec > 0) sleep(intervalSec);
      }
      const totalPollMs = pollWallStart != null ? (Date.now() - pollWallStart) : 0;
      if (pollOk) {
        applyStepCapture(step.capture, res, vu, vars);
      }
      check(res, { ['no error page (' + stepName + ')']: () => !anyRuleFailed });
      check(res, { ['poll (' + stepName + ')']: () => pollOk });
      const requestArgsPoll = { url: url, method: method, headers: headersObj, body: requestArgsBody, step: stepName, stepIndex: si, poll: true, pollTotalAttempts: pollAttempt };
      const failedPoll = !pollOk || anyRuleFailed;
      console.log('__REQ__' + JSON.stringify({ vu: vu, scenarioIter: __ITER, status: lastStatus, duration: totalPollMs, k6TimingsDurationMs: sumK6DurMs > 0 ? sumK6DurMs : null, body: lastBodyFull, requestedAt: firstRequestedAt, respondedAt: lastRespondedAt, requestArgs: requestArgsPoll, failed: failedPoll }) + '__REQEND__');
    } else {
    const reqStartMs = Date.now();
    const requestedAt = new Date(reqStartMs).toISOString().replace(/(\.\d+)Z$/i, (_, frac) => (frac + '000000').slice(0, 7) + 'Z');
    res = doStepRequest(method, url, bodyStr, headersObj, tags, multipartFd);
    const reqEndMs = Date.now();
    const respondedAt = new Date(reqEndMs).toISOString().replace(/(\.\d+)Z$/i, (_, frac) => (frac + '000000').slice(0, 7) + 'Z');
    const wallMs = reqEndMs - reqStartMs;
    const k6Dur = res && res.timings && typeof res.timings.duration === 'number' ? res.timings.duration : null;
    const duration = wallMs;
    applyStepCapture(step.capture, res, vu, vars);
{% endraw %}
    const _urlStr = res && res.url != null ? String(res.url) : String(url);
    const _bodyStr = res && res.body != null ? String(res.body) : '';
    var errorPageFailed = __errorPageRuleFailedSc(_urlStr, _bodyStr, stepErrRules);
    check(res, { ['no error page (' + stepName + ')']: () => !__errorPageRuleFailedSc(_urlStr, _bodyStr, stepErrRules) });
{% raw %}    check(res, { ['status 2xx (' + stepName + ')']: (r) => r != null && r.status >= 200 && r.status < 300 });
    const bodyFull = (res && res.body != null) ? String(res.body) : '';
    const status = (res != null && res.status != null) ? (typeof res.status === 'number' ? res.status : parseInt(res.status, 10)) : null;
    const requestArgs = { url: url, method: method, headers: headersObj, body: requestArgsBody, step: stepName, stepIndex: si };
    console.log('__REQ__' + JSON.stringify({ vu: vu, scenarioIter: __ITER, status: status, duration: duration, k6TimingsDurationMs: k6Dur, body: bodyFull, requestedAt: requestedAt, respondedAt: respondedAt, requestArgs: requestArgs, failed: errorPageFailed }) + '__REQEND__');
    }
    const pauseAfter = step.sleepAfterSeconds;
    if (pauseAfter != null && Number(pauseAfter) > 0) sleep(Number(pauseAfter));
  }
  for (var si = 0; si < STEPS.length; si++) {
    runScenarioStep(STEPS[si], si);
  }
  sleep({% endraw %}{{ sleep_s }}{% raw %});
}

const SUMMARY_MARKER = '__K6_SUMMARY_JSON__';
const SUMMARY_END = '__K6_SUMMARY_END__';
export function handleSummary(data) {
  return { stdout: SUMMARY_MARKER + JSON.stringify(data) + SUMMARY_END };
}
{% endraw %}
