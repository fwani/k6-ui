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
{% if error_page_pattern_js %}
  const ERROR_PATTERN = {{ error_page_pattern_js }};
  const ERROR_MATCH_NOT_CONTAINS = {{ 'true' if error_page_match_mode == 'not_contains' else 'false' }};
  const _urlStr = (res && res.url != null ? String(res.url) : '') || (typeof url !== 'undefined' ? String(url) : '');
  const _bodyStr = res && res.body != null ? String(res.body) : '';
  const _found = ERROR_PATTERN && (_urlStr.indexOf(ERROR_PATTERN) !== -1 || _bodyStr.indexOf(ERROR_PATTERN) !== -1);
  check(res, { 'no error page': () => !ERROR_PATTERN || (ERROR_MATCH_NOT_CONTAINS ? _found : !_found) });
  var errorPageFailed = !!(ERROR_PATTERN && (ERROR_MATCH_NOT_CONTAINS ? !_found : _found));
{% else %}
  var errorPageFailed = false;
{% endif %}{% raw %}  check(res, { 'status 2xx': (r) => r != null && r.status >= 200 && r.status < 300 });
  const bodyPreview = (res && res.body != null) ? String(res.body).substring(0, {% endraw %}{{ body_preview_size }}{% raw %}) : '';
  const duration = (res && res.timings && typeof res.timings.duration === 'number') ? res.timings.duration : null;
  const status = (res != null && res.status != null) ? (typeof res.status === 'number' ? res.status : parseInt(res.status, 10)) : null;
  console.log('__REQ__' + JSON.stringify({ status: status, duration: duration, body: bodyPreview, requestedAt: requestedAt, requestArgs: requestArgs, failed: errorPageFailed }) + '__REQEND__');
  sleep({% endraw %}{{ sleep_s }}{% raw %});
}

const SUMMARY_MARKER = '__K6_SUMMARY_JSON__';
const SUMMARY_END = '__K6_SUMMARY_END__';
export function handleSummary(data) {
  return { stdout: SUMMARY_MARKER + JSON.stringify(data) + SUMMARY_END };
}
{% endraw %}
