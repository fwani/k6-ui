<template>
  <div class="run-result">
    <h1 class="text-h5 mb-2">테스트 결과</h1>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
    <v-alert v-else-if="error" type="error" density="compact" class="mb-2">{{ error }}</v-alert>
    <template v-else-if="result">
      <v-sheet class="pa-3 mb-2" rounded>
        <p class="text-caption text-medium-emphasis mb-2">HTTP 요청 기준 요약 (k6) 또는 브라우저 페이지 로드 요약</p>
        <v-list density="compact" class="py-0">
          <v-list-item>
            <v-list-item-title>평균 응답 시간</v-list-item-title>
            <v-list-item-subtitle>요청별 응답 시간의 평균</v-list-item-subtitle>
            <template #append>{{ formatMs(result.avgResponseTime) }}</template>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>최대 응답 시간</v-list-item-title>
            <v-list-item-subtitle>가장 오래 걸린 요청의 응답 시간</v-list-item-subtitle>
            <template #append>{{ formatMs(result.maxResponseTime) }}</template>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>실패율</v-list-item-title>
            <v-list-item-subtitle>실패한 요청 비율 (0~1, 1 = 100%)</v-list-item-subtitle>
            <template #append>{{ formatPercent(result.failureRate) }}</template>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>요청 수</v-list-item-title>
            <v-list-item-subtitle>총 요청(또는 페이지 로드) 횟수</v-list-item-subtitle>
            <template #append>{{ result.requestCount }}</template>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>TPS/RPS</v-list-item-title>
            <v-list-item-subtitle>초당 요청 수 (Transactions / Requests per second)</v-list-item-subtitle>
            <template #append>{{ result.tpsOrRps?.toFixed(2) ?? '-' }}</template>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>실행 시간</v-list-item-title>
            <v-list-item-subtitle>테스트가 돌아간 총 시간</v-list-item-subtitle>
            <template #append>{{ result.executionTime?.toFixed(1) ?? '-' }}초</template>
          </v-list-item>
        </v-list>
      </v-sheet>
      <v-sheet v-if="hasBrowserMetrics" class="pa-3 mb-2" rounded>
        <h3 class="text-subtitle-1 mb-1">렌더링 메트릭</h3>
        <p class="text-caption text-medium-emphasis mb-2">브라우저(Chromium) 엔진으로 수집한 Web Vitals. 사용자 체감 로딩·안정성 지표입니다.</p>
        <v-list density="compact" class="py-0">
          <v-list-item v-if="result.lcpMs != null">
            <v-list-item-title>LCP (Largest Contentful Paint)</v-list-item-title>
            <v-list-item-subtitle>가장 큰 콘텐츠가 화면에 그려지기까지 걸린 시간. 로딩 체감의 핵심 지표. 낮을수록 좋음.</v-list-item-subtitle>
            <template #append>{{ formatMs(result.lcpMs) }}</template>
          </v-list-item>
          <v-list-item v-if="result.fcpMs != null">
            <v-list-item-title>FCP (First Contentful Paint)</v-list-item-title>
            <v-list-item-subtitle>첫 픽셀(텍스트·이미지 등)이 화면에 나타난 시점. 처음 반응이 보이는 속도. 낮을수록 좋음.</v-list-item-subtitle>
            <template #append>{{ formatMs(result.fcpMs) }}</template>
          </v-list-item>
          <v-list-item v-if="result.ttfbMs != null">
            <v-list-item-title>TTFB (Time to First Byte)</v-list-item-title>
            <v-list-item-subtitle>서버가 첫 바이트를 보내기까지 걸린 시간. 네트워크·서버 응답 지연. 낮을수록 좋음.</v-list-item-subtitle>
            <template #append>{{ formatMs(result.ttfbMs) }}</template>
          </v-list-item>
          <v-list-item v-if="result.cls != null">
            <v-list-item-title>CLS (Cumulative Layout Shift)</v-list-item-title>
            <v-list-item-subtitle>레이아웃이 밀리는 정도의 누적 값. 0에 가까울수록 시각적 안정성이 좋음. 0.1 이하 권장.</v-list-item-subtitle>
            <template #append>{{ result.cls?.toFixed(4) ?? '—' }}</template>
          </v-list-item>
        </v-list>
      </v-sheet>
      <v-alert v-if="result.errorMessage" type="error" variant="tonal" density="compact" class="mb-2">
        <template #title>실패 사유</template>
        <pre class="text-caption overflow-auto" style="max-height: 20em; white-space: pre-wrap; word-break: break-all;">{{ result.errorMessage }}</pre>
      </v-alert>
      <p class="d-flex flex-wrap align-center gap-2">
        <template v-if="grafanaUrl">
          <v-btn :href="grafanaUrl" target="_blank" rel="noopener" color="primary" variant="text">Grafana (k6) 대시보드</v-btn>
          <v-btn
            v-if="hasBrowserMetrics && grafanaBrowserVitalsUrl"
            :href="grafanaBrowserVitalsUrl"
            target="_blank"
            rel="noopener"
            color="primary"
            variant="text"
          >
            Grafana (Browser Web Vitals)
          </v-btn>
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
            <v-select
              v-model="requestPageSize"
              :items="[10, 20, 50, 100]"
              density="compact"
              hide-details
              label="표시 수"
              class="page-size-select"
              style="width: 110px"
              @update:model-value="onPageSizeChange"
            />
            <v-pagination
              v-model="requestPage"
              :length="requestPageCount"
              :total-visible="7"
              density="compact"
              show-first-last-page
              @update:model-value="loadRequests"
            />
          </div>
          <div class="request-table-wrap">
            <table class="request-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th v-if="showScreenshotColumn">스크린샷</th>
                  <th>요청 시각</th>
                  <th>상태</th>
                  <th>실패</th>
                  <th>응답 시간</th>
                  <th>본문 미리보기</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in requestItems" :key="row.seq" :class="{ 'row-failed': row.failed }">
                  <td>{{ row.seq }}</td>
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
                    <v-chip v-if="row.failed" color="error" size="x-small" density="compact">실패</v-chip>
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
              </tbody>
            </table>
          </div>
          <div class="d-flex align-center flex-wrap gap-2 mt-2 mb-2">
            <p class="text-caption text-medium-emphasis mb-0">
              총 {{ requestsTotal }}건
              <span v-if="requestsTotal > 0"> ({{ requestStart }}–{{ requestEnd }} 표시)</span>
            </p>
            <v-select
              v-model="requestPageSize"
              :items="[10, 20, 50, 100]"
              density="compact"
              hide-details
              label="표시 수"
              class="page-size-select"
              style="width: 110px"
              @update:model-value="onPageSizeChange"
            />
            <v-pagination
              v-model="requestPage"
              :length="requestPageCount"
              :total-visible="7"
              density="compact"
              show-first-last-page
              @update:model-value="loadRequests"
            />
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

const route = useRoute()
const runId = route.params.id

const result = ref(null)
const grafanaUrl = ref('')
const grafanaBrowserVitalsUrl = ref('')
const requestItems = ref([])
const requestsTotal = ref(null)
const requestPage = ref(1)
const requestPageSize = ref(20)
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

const PREVIEW_MAX = 500
function bodyPreviewShort(text) {
  if (!text) return ''
  if (text.length <= PREVIEW_MAX) return text
  return text.slice(0, PREVIEW_MAX) + '...'
}

async function loadRequests() {
  if (requestsTotal.value === 0) return
  const limit = requestPageSize.value
  const offset = (requestPage.value - 1) * limit
  try {
    const res = await get(`runs/${runId}/requests?limit=${limit}&offset=${offset}`)
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
      get(`runs/${runId}/requests?limit=${requestPageSize.value}&offset=0`).catch((e) => {
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
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
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
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
.request-table th { font-weight: 600; }
.request-table tr.row-failed { background: rgba(var(--v-theme-error), 0.08); }
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
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 0 0 1px rgba(var(--v-border-color), var(--v-border-opacity));
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
</style>
