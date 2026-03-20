{% raw %}import http from 'k6/http';
import {% endraw %}{{ '{ check, sleep }' }}{% raw %} from 'k6';

{% endraw %}{% if per_vu %}
const URL_TEMPLATE = {{ url_template_js }};
const HEADERS_TEMPLATE = {{ headers_js }};
const BODY_TEMPLATE = {{ body_template_js }};
const method = {{ method_js }};

{% endif %}{% raw %}export const options = {
{% endraw %}
{{ options_js }}{% raw %}};

export default function () {
  const iso = new Date().toISOString();
  const requestedAt = iso.replace(/(\.\d+)Z$/i, (_, frac) => (frac + '000000').slice(0, 7) + 'Z');
{% endraw %}
{{ call_js }}
{% if error_rules_js %}
  const ERROR_PAGE_RULES = {{ error_rules_js }};
  function __errorPageRuleFailed(_urlStr, _bodyStr, rules) {
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
  const _urlStr = (res && res.url != null ? String(res.url) : '') || (typeof url !== 'undefined' ? String(url) : '');
  const _bodyStr = res && res.body != null ? String(res.body) : '';
  var errorPageFailed = __errorPageRuleFailed(_urlStr, _bodyStr, ERROR_PAGE_RULES);
  check(res, { 'no error page': () => !__errorPageRuleFailed(_urlStr, _bodyStr, ERROR_PAGE_RULES) });
{% else %}
  var errorPageFailed = false;
{% endif %}{% raw %}  check(res, { 'status 2xx': (r) => r != null && r.status >= 200 && r.status < 300 });
  const bodyFull = (res && res.body != null) ? String(res.body) : '';
  const duration = (res && res.timings && typeof res.timings.duration === 'number') ? res.timings.duration : null;
  const status = (res != null && res.status != null) ? (typeof res.status === 'number' ? res.status : parseInt(res.status, 10)) : null;
  console.log('__REQ__' + JSON.stringify({ vu: (typeof vu !== 'undefined' ? vu : __VU), scenarioIter: __ITER, status: status, duration: duration, body: bodyFull, requestedAt: requestedAt, requestArgs: requestArgs, failed: errorPageFailed }) + '__REQEND__');
  sleep({% endraw %}{{ sleep_s }}{% raw %});
}

const SUMMARY_MARKER = '__K6_SUMMARY_JSON__';
const SUMMARY_END = '__K6_SUMMARY_END__';
export function handleSummary(data) {
  return { stdout: SUMMARY_MARKER + JSON.stringify(data) + SUMMARY_END };
}
{% endraw %}
