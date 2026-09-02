<template>
  <div class="run-result page-section">
    <h1 class="page-title">테스트 결과</h1>
    <UiProgress v-if="loading" indeterminate class="mb-2" />
    <UiAlert v-else-if="error" type="error" class="mb-2">{{ error }}</UiAlert>
    <template v-else-if="result">
      <div class="panel mb-2">
        <p class="text-caption text-medium-emphasis mb-2">
          HTTP(k6): 아래 평균·최대·요청 수·TPS·실행 시간은 저장된 요청 로그(__REQ__)와 동일 기준이며, 실행 시간은 시작~종료 벽시계입니다.
          「HTTP 실패율」만 k6 원시(http_req_failed)입니다. 브라우저 실행은 Web Vitals·렌더링 요약이 별도 패널입니다.
        </p>
        <div class="result-kv">
          <div class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">평균 응답 시간</span>
              <span class="result-kv-append">{{ formatMs(result.avgResponseTime) }}</span>
            </div>
            <p class="result-kv-sub">저장된 요청 행 기준 응답 시간 평균</p>
          </div>
          <div class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">최대 응답 시간</span>
              <span class="result-kv-append">{{ formatMs(result.maxResponseTime) }}</span>
            </div>
            <p class="result-kv-sub">저장된 요청 행 중 최대 응답 시간</p>
          </div>
          <div class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">종합 실패율</span>
              <span class="result-kv-append">{{ formatPercent(result.overallFailureRate ?? 0) }}</span>
            </div>
            <p class="result-kv-sub">
              저장된 요청 행 기준: 2xx가 아니거나 에러 페이지 판별(failed) 비율
            </p>
          </div>
          <div class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">HTTP 실패율 (k6)</span>
              <span class="result-kv-append">{{ formatPercent(result.failureRate) }}</span>
            </div>
            <p class="result-kv-sub">k6 http_req_failed. 실제 HTTP 시도마다 집계라 폴링·리다이렉트 등이 많으면 종합 실패율과 다를 수 있음</p>
          </div>
          <div class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">요청 수</span>
              <span class="result-kv-append">{{ result.requestCount }}</span>
            </div>
            <p class="result-kv-sub">저장된 요청 로그 행 수(폴링 스텝은 스텝당 1행)</p>
          </div>
          <div class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">TPS/RPS</span>
              <span class="result-kv-append">{{ result.tpsOrRps?.toFixed(2) ?? '-' }}</span>
            </div>
            <p class="result-kv-sub">요청 수 ÷ 실행 시간(벽시계)</p>
          </div>
          <div class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">실행 시간</span>
              <span class="result-kv-append">{{ result.executionTime?.toFixed(1) ?? '-' }}초</span>
            </div>
            <p class="result-kv-sub">Run 시작~종료(벽시계)</p>
          </div>
        </div>
      </div>
      <div v-if="result.stepSummaries?.length > 0" class="panel mb-2">
        <h3 class="text-subtitle-1 mb-1">스텝별 요약</h3>
        <p class="text-caption text-medium-emphasis mb-2">
          시나리오 스텝(저장된 요청 행 기준 집계). 단일 요청 테스트는 표가 비어 있을 수 있음.
          스텝 TPS/RPS는 해당 스텝 요청 수를 전체 실행 시간(초)으로 나눈 값으로, 상단 요약과 같은 시간 기준입니다.
        </p>
        <div class="request-table-wrap">
          <table class="request-table">
            <thead>
              <tr>
                <th>스텝</th>
                <th>인덱스</th>
                <th>건수</th>
                <th>평균 응답</th>
                <th>최대 응답</th>
                <th>실패율</th>
                <th>TPS/RPS</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in result.stepSummaries" :key="s.stepIndex">
                <td>{{ s.stepName || '—' }}</td>
                <td>{{ s.stepIndex }}</td>
                <td>{{ s.requestCount }}</td>
                <td>{{ formatMs(s.avgResponseTime) }}</td>
                <td>{{ formatMs(s.maxResponseTime) }}</td>
                <td>{{ formatPercent(s.failureRate) }}</td>
                <td>{{ s.tpsOrRps != null ? Number(s.tpsOrRps).toFixed(2) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-if="hasBrowserMetrics" class="panel mb-2">
        <h3 class="text-subtitle-1 mb-1">렌더링 메트릭</h3>
        <p class="text-caption text-medium-emphasis mb-2">브라우저(Chromium) 엔진으로 수집한 Web Vitals. 사용자 체감 로딩·안정성 지표입니다.</p>
        <div class="result-kv">
          <div v-if="result.lcpMs != null" class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">LCP (Largest Contentful Paint)</span>
              <span class="result-kv-append">{{ formatMs(result.lcpMs) }}</span>
            </div>
            <p class="result-kv-sub">가장 큰 콘텐츠가 화면에 그려지기까지 걸린 시간. 로딩 체감의 핵심 지표. 낮을수록 좋음.</p>
          </div>
          <div v-if="result.fcpMs != null" class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">FCP (First Contentful Paint)</span>
              <span class="result-kv-append">{{ formatMs(result.fcpMs) }}</span>
            </div>
            <p class="result-kv-sub">첫 픽셀(텍스트·이미지 등)이 화면에 나타난 시점. 처음 반응이 보이는 속도. 낮을수록 좋음.</p>
          </div>
          <div v-if="result.ttfbMs != null" class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">TTFB (Time to First Byte)</span>
              <span class="result-kv-append">{{ formatMs(result.ttfbMs) }}</span>
            </div>
            <p class="result-kv-sub">서버가 첫 바이트를 보내기까지 걸린 시간. 네트워크·서버 응답 지연. 낮을수록 좋음.</p>
          </div>
          <div v-if="result.cls != null" class="result-kv-item">
            <div class="result-kv-head">
              <span class="result-kv-title">CLS (Cumulative Layout Shift)</span>
              <span class="result-kv-append">{{ result.cls?.toFixed(4) ?? '—' }}</span>
            </div>
            <p class="result-kv-sub">레이아웃이 밀리는 정도의 누적 값. 0에 가까울수록 시각적 안정성이 좋음. 0.1 이하 권장.</p>
          </div>
        </div>
      </div>
      <UiAlert v-if="result.errorMessage" type="error" class="mb-2">
        <strong>실패 사유</strong>
        <pre class="text-caption overflow-auto result-err-pre">{{ result.errorMessage }}</pre>
      </UiAlert>
      <p class="d-flex flex-wrap align-center gap-2">
        <template v-if="grafanaUrl">
          <UiBtn :href="grafanaUrl" target="_blank" rel="noopener" color="primary" variant="text">
            Grafana (k6) 대시보드
          </UiBtn>
          <UiBtn
            v-if="hasBrowserMetrics && grafanaBrowserVitalsUrl"
            :href="grafanaBrowserVitalsUrl"
            target="_blank"
            rel="noopener"
            color="primary"
            variant="text"
          >
            Grafana (Browser Web Vitals)
          </UiBtn>
        </template>
        <span v-else class="text-body-2 text-medium-emphasis">Grafana URL이 설정되지 않았습니다.</span>
      </p>

      <section class="mt-4">
        <h2 class="text-subtitle-1 mb-2">요청별 응답</h2>
        <p v-if="requestsTotal == null || requestsTotal === 0" class="text-body-2 text-medium-emphasis">저장된 요청 응답이 없습니다.</p>
        <template v-else>
          <div class="d-flex align-center flex-wrap gap-2 mb-2">
            <p class="text-caption text-medium-emphasis mb-0">
              총 {{ requestsTotal }}건
              <span v-if="requestsTotal > 0"> ({{ requestStart }}–{{ requestEnd }} 표시)</span>
            </p>
            <UiSelect
              v-model="requestPageSize"
              :items="[10, 20, 50, 100]"
              hide-details
              label="표시 수"
              class="page-size-select"
              style="width: 110px"
              @update:model-value="onPageSizeChange"
            />
            <UiPagination v-model="requestPage" :length="requestPageCount" @update:model-value="loadRequests" />
          </div>
          <div class="d-flex align-center flex-wrap gap-2 mb-2">
            <UiSelect
              v-model="requestSort"
              :items="requestSortItems"
              item-title="title"
              item-value="value"
              label="요청 목록 정렬"
              hide-details
              class="request-sort-select"
              style="min-width: 200px"
              @update:model-value="onRequestSortChange"
            />
          </div>
          <div class="request-table-wrap">
            <table class="request-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>VU</th>
                  <th>반복</th>
                  <th>단계</th>
                  <th v-if="showScreenshotColumn">스크린샷</th>
                  <th>요청 시각</th>
                  <th>상태</th>
                  <th>실패</th>
                  <th>응답 시간</th>
                  <th>응답 본문</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="(row, rIdx) in requestItems" :key="row.seq">
                  <tr v-if="showTaskGroupHeader(rIdx)" class="task-group-sep">
                    <td :colspan="requestTableColspan" class="task-group-sep-cell">
                      {{ taskGroupHeaderLabel(rIdx) }}
                    </td>
                  </tr>
                  <tr :class="requestRowClasses(row, rIdx)">
                  <td>{{ row.seq }}</td>
                  <td>{{ traceCell(row.requestArgs).vu }}</td>
                  <td>{{ traceCell(row.requestArgs).iter }}</td>
                  <td class="step-cell">{{ traceCell(row.requestArgs).stepLabel }}</td>
                  <td v-if="showScreenshotColumn" class="screenshot-cell">
                    <div
                      v-if="hasScreenshotForRow(row) && !screenshotErrorSeqs.has(row.seq)"
                      class="screenshot-wrap"
                      @mouseenter="onScreenshotHover($event, row.seq)"
                      @mouseleave="onScreenshotLeave"
                    >
                      <img
                        :src="screenshotUrl(row.seq - 1)"
                        :alt="`#${row.seq} 스크린샷`"
                        class="screenshot-thumb"
                        loading="lazy"
                        @error="onScreenshotError(row.seq)"
                      />
                    </div>
                    <span v-else class="text-medium-emphasis">—</span>
                  </td>
                  <td>{{ formatRequestedAt(row.requestedAt) }}</td>
                  <td>{{ row.statusCode ?? '—' }}</td>
                  <td>
                    <UiChip v-if="row.failed" color="error" size="x-small">실패</UiChip>
                    <span v-else class="text-medium-emphasis">—</span>
                  </td>
                  <td>{{ formatMs(row.responseTimeMs) }}</td>
                  <td class="body-preview-cell">
                    <div v-if="row.bodyPreview" class="body-preview-wrap">
                      <pre class="body-preview">{{ bodyPreviewShort(row.bodyPreview) }}</pre>
                      <div class="body-preview-overlay">
                        <pre class="body-preview-overlay-content">{{ row.bodyPreview }}</pre>
                      </div>
                    </div>
                    <span v-else class="text-medium-emphasis">—</span>
                  </td>
                </tr>
                </template>
              </tbody>
            </table>
          </div>
          <div class="d-flex align-center flex-wrap gap-2 mt-2 mb-2">
            <p class="text-caption text-medium-emphasis mb-0">
              총 {{ requestsTotal }}건
              <span v-if="requestsTotal > 0"> ({{ requestStart }}–{{ requestEnd }} 표시)</span>
            </p>
            <UiSelect
              v-model="requestPageSize"
              :items="[10, 20, 50, 100]"
              hide-details
              label="표시 수"
              class="page-size-select"
              style="width: 110px"
              @update:model-value="onPageSizeChange"
            />
            <UiPagination v-model="requestPage" :length="requestPageCount" @update:model-value="loadRequests" />
          </div>
        </template>
      </section>
      <!-- 스크린샷 호버 시 테이블 위에 고정 위치로 확대 표시 -->
      <Teleport to="body">
        <div
          v-if="screenshotHover.url"
          class="screenshot-hover-fixed"
          :style="screenshotHover.style"
          @mouseleave="onScreenshotLeave"
        >
          <img :src="screenshotHover.url" :alt="`#${screenshotHover.seq} 스크린샷 확대`" class="screenshot-hover-img" />
        </div>
      </Teleport>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { baseURL, get, getApiErrorMessage } from '../services/api'
import UiProgress from '../components/UiProgress.vue'
import UiAlert from '../components/UiAlert.vue'
import UiBtn from '../components/UiBtn.vue'
import UiSelect from '../components/UiSelect.vue'
import UiPagination from '../components/UiPagination.vue'
import UiChip from '../components/UiChip.vue'

const route = useRoute()
const runId = route.params.id

const result = ref(null)
const grafanaUrl = ref('')
const grafanaBrowserVitalsUrl = ref('')
const requestItems = ref([])
const requestsTotal = ref(null)
const requestPage = ref(1)
const requestPageSize = ref(20)
const requestSort = ref('vuTrace')
const requestSortItems = [
  { title: 'VU·반복·스텝 순', value: 'vuTrace' },
  { title: '저장 순 (seq)', value: 'seq' },
]
const screenshotErrorSeqs = ref(new Set())
const screenshotHover = ref({ url: '', seq: null, style: {} })
const loading = ref(true)
const error = ref('')

const hasBrowserMetrics = computed(
  () =>
    result.value &&
    (result.value.lcpMs != null ||
      result.value.fcpMs != null ||
      result.value.ttfbMs != null ||
      result.value.cls != null)
)

const bodyPreviewDisplayMax = computed(() => {
  const n = result.value?.bodyPreviewSize
  if (n == null || Number.isNaN(Number(n))) return 500
  return Number(n)
})

const showScreenshotColumn = computed(
  () => hasBrowserMetrics.value && result.value && result.value.requestCount > 0
)

function hasScreenshotForRow(row) {
  if (!result.value || !row?.seq) return false
  return row.seq <= result.value.requestCount
}

const requestPageCount = computed(() =>
  requestsTotal.value != null && requestsTotal.value > 0
    ? Math.max(1, Math.ceil(requestsTotal.value / requestPageSize.value))
    : 1
)
const requestStart = computed(() =>
  requestsTotal.value === 0 ? 0 : (requestPage.value - 1) * requestPageSize.value + 1
)
const requestEnd = computed(() =>
  Math.min(requestPage.value * requestPageSize.value, requestsTotal.value ?? 0)
)

const requestTableColspan = computed(() => 9 + (showScreenshotColumn.value ? 1 : 0))

function taskGroupKeyFromRow(row) {
  return requestTraceDisplay(row.requestArgs).groupKey
}

function showTaskGroupHeader(idx) {
  if (requestSort.value !== 'vuTrace') return false
  const items = requestItems.value
  const row = items[idx]
  if (!row) return false
  const key = taskGroupKeyFromRow(row)
  if (!key) return false
  if (idx === 0) return true
  return key !== taskGroupKeyFromRow(items[idx - 1])
}

function taskGroupHeaderLabel(idx) {
  const row = requestItems.value[idx]
  if (!row) return ''
  const t = traceCell(row.requestArgs)
  return `시나리오 실행 · VU ${t.vu} · 반복 ${t.iter}`
}

function formatMs(ms) {
  if (ms == null) return '-'
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`
  return `${Number(ms).toFixed(2)}ms`
}

function formatRequestedAt(iso) {
  if (!iso) return '—'
  try {
    const utcStr = typeof iso === 'string' && !/Z|[+-]\d{2}:?\d{2}$/.test(iso.trim()) ? iso.trim() + 'Z' : iso
    const d = new Date(utcStr)
    if (Number.isNaN(d.getTime())) return '—'
    const yy = String(d.getFullYear() % 100).padStart(2, '0')
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    const sec = String(d.getSeconds()).padStart(2, '0')
    const fracMatch = typeof iso === 'string' && iso.match(/\.(\d+)/)
    const frac = fracMatch ? fracMatch[1].padEnd(6, '0').slice(0, 6) : '000000'
    return `${yy}.${mm}.${dd} ${h}:${min}:${sec}.${frac}`
  } catch {
    return '—'
  }
}

function formatPercent(rate) {
  if (rate == null) return '-'
  return `${(rate * 100).toFixed(2)}%`
}

function parseRequestArgsJson(raw) {
  if (raw == null) return null
  if (typeof raw === 'object') return raw
  if (typeof raw !== 'string' || !raw.trim()) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

/** request_args(JSON)에서 VU·반복·단계 표시용 */
function requestTraceDisplay(requestArgsRaw) {
  const o = parseRequestArgsJson(requestArgsRaw)
  if (!o) return { vu: '—', iter: '—', stepLabel: '—', groupKey: '' }
  const vu = o.vu != null && o.vu !== '' ? String(o.vu) : '—'
  const iter = o.scenarioIter != null && o.scenarioIter !== '' ? String(o.scenarioIter) : '—'
  let stepLabel = '—'
  if (o.step != null && String(o.step).trim()) {
    const si = o.stepIndex
    const base =
      si != null && si !== '' ? `${o.step} (#${si})` : String(o.step)
    const pt = o.pollTotalAttempts
    if (o.poll === true && pt != null && pt !== '' && !Number.isNaN(Number(pt))) {
      stepLabel = `${base} · 폴링 ${pt}회`
    } else {
      stepLabel = base
    }
  }
  const groupKey = vu !== '—' && iter !== '—' ? `${vu}-${iter}` : ''
  return { vu, iter, stepLabel, groupKey }
}

function traceCell(requestArgsRaw) {
  return requestTraceDisplay(requestArgsRaw)
}

function traceStripeClass(row) {
  const { groupKey } = requestTraceDisplay(row.requestArgs)
  if (!groupKey) return ''
  let h = 0
  for (let i = 0; i < groupKey.length; i++) h = ((h << 5) - h + groupKey.charCodeAt(i)) | 0
  return Math.abs(h) % 2 === 0 ? 'trace-stripe-a' : 'trace-stripe-b'
}

function requestRowClasses(row, idx) {
  const cls = {}
  if (row.failed) cls['row-failed'] = true
  const st = traceStripeClass(row)
  if (st) cls[st] = true
  if (requestSort.value === 'vuTrace' && taskGroupKeyFromRow(row)) {
    cls['task-in-group'] = true
    const items = requestItems.value
    const key = taskGroupKeyFromRow(row)
    const nextK = idx < items.length - 1 ? taskGroupKeyFromRow(items[idx + 1]) : ''
    if (key !== nextK) cls['task-group-last'] = true
  }
  return cls
}

function bodyPreviewShort(text, maxLen) {
  if (!text) return ''
  const n = maxLen == null || Number.isNaN(Number(maxLen)) ? 500 : Number(maxLen)
  if (n <= 0) return '…'
  if (text.length <= n) return text
  return text.slice(0, n) + '...'
}

function onRequestSortChange() {
  requestPage.value = 1
  loadRequests()
}

async function loadRequests() {
  if (requestsTotal.value === 0) return
  const limit = requestPageSize.value
  const offset = (requestPage.value - 1) * limit
  try {
    const sortQ = encodeURIComponent(requestSort.value || 'vuTrace')
    const res = await get(`runs/${runId}/requests?limit=${limit}&offset=${offset}&sort=${sortQ}`)
    requestItems.value = res.items || []
    if (requestsTotal.value == null) requestsTotal.value = res.total ?? 0
  } catch (err) {
    error.value = getApiErrorMessage(err)
  }
}

function onPageSizeChange() {
  requestPage.value = 1
  loadRequests()
}

function screenshotUrl(vuIndex) {
  const base = (baseURL || '').replace(/\/$/, '')
  return `${base}/runs/${runId}/screenshots/${vuIndex}`
}

function onScreenshotError(seq) {
  screenshotErrorSeqs.value = new Set([...screenshotErrorSeqs.value, seq])
}
const HOVER_IMG_MAX_W = 480
const HOVER_IMG_MAX_H = 360
const HOVER_OFFSET = 8
function onScreenshotHover(ev, seq) {
  const el = ev.currentTarget
  if (!el) return
  const rect = el.getBoundingClientRect()
  const left = Math.max(HOVER_OFFSET, Math.min(rect.left + rect.width / 2 - HOVER_IMG_MAX_W / 2, window.innerWidth - HOVER_IMG_MAX_W - HOVER_OFFSET))
  // 해당 셀 바로 위에 오도록: 팝업 하단이 셀 상단보다 HOVER_OFFSET 위
  const top = rect.top - HOVER_IMG_MAX_H - HOVER_OFFSET
  screenshotHover.value = {
    url: screenshotUrl(seq - 1),
    seq,
    style: { left: `${left}px`, top: `${top}px` },
  }
}
function onScreenshotLeave() {
  screenshotHover.value = { url: '', seq: null, style: {} }
}

async function load() {
  loading.value = true
  error.value = ''
  screenshotErrorSeqs.value = new Set()
  try {
    const [resResult, resConfig, resRequests] = await Promise.all([
      get(`runs/${runId}/result`),
      get('config').catch(() => ({})),
      get(
        `runs/${runId}/requests?limit=${requestPageSize.value}&offset=0&sort=${encodeURIComponent(requestSort.value || 'vuTrace')}`,
      ).catch((e) => {
        console.warn('요청별 응답 로드 실패:', e)
        return { items: [], total: 0 }
      }),
    ])
    result.value = resResult
    grafanaUrl.value = resConfig.grafanaDashboardUrl || ''
    grafanaBrowserVitalsUrl.value = resConfig.grafanaBrowserVitalsUrl || ''
    requestItems.value = Array.isArray(resRequests?.items) ? resRequests.items : []
    const total = resRequests?.total
    requestsTotal.value = typeof total === 'number' ? total : (total != null ? Number(total) : 0)
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.run-result { max-width: 960px; }
.screenshot-cell { vertical-align: middle; }
.screenshot-wrap {
  position: relative;
  display: inline-block;
}
.screenshot-thumb {
  display: block;
  max-width: 120px;
  height: auto;
  border-radius: 4px;
  object-fit: contain;
  cursor: pointer;
}
.screenshot-hover-fixed {
  position: fixed;
  z-index: 9999;
  padding: 8px;
  background: var(--bg-elevated);
  border-radius: 8px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
  border: 0.5px solid var(--border-default);
}
.screenshot-hover-img {
  display: block;
  max-width: 600px;
  width: auto;
  height: auto;
  border-radius: 4px;
  object-fit: contain;
}
.request-table-wrap { overflow-x: auto; margin-bottom: 1rem; }
.request-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.request-table th,
.request-table td {
  padding: 6px 8px;
  text-align: left;
  border-bottom: 0.5px solid var(--border-default);
}
.request-table th { font-weight: 600; }
.request-table tr.task-group-sep td {
  border-bottom: none;
  padding: 0;
}
.request-table td.task-group-sep-cell {
  padding: 8px 10px 4px;
  background: color-mix(in srgb, var(--accent-success) 10%, transparent);
  font-weight: 600;
  font-size: 0.75rem;
  color: var(--accent-success);
  border-top: 0.5px solid color-mix(in srgb, var(--accent-success) 35%, transparent);
}
.request-table tr.task-in-group td:first-child {
  box-shadow: inset 3px 0 0 var(--accent-success);
}
.request-table tr.task-group-last td {
  border-bottom: 0.5px solid color-mix(in srgb, var(--accent-success) 25%, transparent);
}
.request-table tr.trace-stripe-a:not(.row-failed) {
  background: color-mix(in srgb, var(--text-primary) 4%, transparent);
}
.request-table tr.trace-stripe-b:not(.row-failed) {
  background: color-mix(in srgb, var(--text-primary) 8%, transparent);
}
.request-table tr.row-failed {
  background: color-mix(in srgb, var(--accent-danger) 10%, transparent);
}
.step-cell { max-width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.body-preview-cell { max-width: 320px; position: relative; }
.body-preview-wrap {
  position: relative;
  max-height: 8em;
  min-height: 2em;
}
.body-preview {
  margin: 0;
  font-size: 0.75rem;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 8em;
  overflow: hidden;
  cursor: help;
}
.body-preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
  background: var(--bg-surface);
  box-shadow: 0 0 0 0.5px var(--border-default);
  border-radius: 4px;
  overflow: auto;
  padding: 6px 8px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
}
.body-preview-wrap:hover .body-preview-overlay {
  opacity: 1;
  pointer-events: auto;
}
.body-preview-overlay-content {
  margin: 0;
  font-size: 0.75rem;
  white-space: pre-wrap;
  word-break: break-all;
}
.result-kv {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px 16px;
}
@media (min-width: 640px) {
  .result-kv {
    grid-template-columns: 1fr 1fr;
  }
}
.result-kv-item {
  padding-bottom: 8px;
  border-bottom: 0.5px solid var(--border-default);
}
.result-kv-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.result-kv-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}
.result-kv-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}
.result-kv-append {
  font-size: 0.875rem;
  color: var(--text-primary);
  flex-shrink: 0;
}
.result-kv-sub {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.45;
}
.result-err-pre {
  max-height: 20em;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 8px 0 0;
}
</style>
