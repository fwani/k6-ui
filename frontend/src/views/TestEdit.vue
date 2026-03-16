<template>
  <div>
    <h1 class="text-h5 mb-2">테스트 수정</h1>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
    <v-alert v-else-if="loadError" type="error" density="compact" class="mb-2">{{ loadError }}</v-alert>
    <v-form v-else @submit.prevent="onSubmit" class="test-form compact-form">
      <v-row dense>
        <v-col cols="12" sm="8" md="6">
          <v-text-field
            v-model="form.name"
            required
            density="compact"
            hide-details="auto"
            :error-messages="errors.name ? [errors.name] : []"
          >
            <template #label>
              <span class="label-with-tip">테스트 이름
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>나중에 구분하기 위한 이름입니다.</span>
              </v-tooltip>
              </span>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="12" sm="4" md="2">
          <v-select
            v-model="form.httpMethod"
            :items="['GET', 'POST', 'PUT', 'DELETE']"
            density="compact"
            hide-details
          >
            <template #label>
              <span class="label-with-tip">HTTP 메서드
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>요청 방식입니다. 보통 조회는 GET, 데이터 전송은 POST를 씁니다.</span>
              </v-tooltip>
              </span>
            </template>
          </v-select>
        </v-col>
        <v-col cols="12" md="4">
          <v-text-field
            :model-value="urlDisplay"
            placeholder="https://example.com?a=b"
            density="compact"
            hide-details="auto"
            :error-messages="errors.baseUrl ? [errors.baseUrl] : []"
            @update:model-value="urlDisplay = $event"
            @blur="parseUrlAndSyncToParams"
          >
            <template #label>
              <span class="label-with-tip">대상 URL
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>부하를 줄 웹 주소입니다. (예: https://example.com/api)</span>
              </v-tooltip>
              </span>
            </template>
          </v-text-field>
        </v-col>
      </v-row>
      <v-tabs v-model="requestTab" density="compact" class="request-tabs mb-2">
        <v-tab value="params">
          Params
          <v-tooltip location="top">
            <template #activator="{ props }">
              <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
            </template>
            <span>URL 뒤에 붙는 검색 조건(쿼리)입니다. (예: ?page=1)</span>
          </v-tooltip>
        </v-tab>
        <v-tab value="headers">
          Headers
          <v-tooltip location="top">
            <template #activator="{ props }">
              <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
            </template>
            <span>요청에 넣는 부가 정보입니다. (인증 토큰, Content-Type 등)</span>
          </v-tooltip>
        </v-tab>
        <v-tab value="body">
          Body
          <v-tooltip location="top">
            <template #activator="{ props }">
              <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
            </template>
            <span>POST/PUT 등으로 보낼 본문 내용(JSON 등)입니다.</span>
          </v-tooltip>
        </v-tab>
      </v-tabs>
      <v-window v-model="requestTab" class="request-window">
        <v-window-item value="params">
          <div class="kv-section">
            <div v-for="(row, i) in form.paramsList" :key="i" class="kv-row">
              <v-checkbox
                v-model="row.enabled"
                hide-details
                density="compact"
                class="param-check flex-shrink-0"
                @update:model-value="syncUrlFromParams"
              />
              <v-text-field v-model="row.key" placeholder="Key" density="compact" hide-details class="kv-key" @update:model-value="syncUrlFromParams" />
              <v-text-field v-model="row.value" placeholder="Value" density="compact" hide-details class="kv-value" @update:model-value="syncUrlFromParams" />
              <v-btn icon variant="text" size="small" color="error" :disabled="form.paramsList.length <= 1" @click="removeParam(i)">
                <v-icon size="small">mdi-delete-outline</v-icon>
              </v-btn>
            </div>
            <v-btn size="small" variant="tonal" class="mt-1" @click="addParam">추가</v-btn>
          </div>
        </v-window-item>
        <v-window-item value="headers">
          <div class="kv-section">
            <div v-for="(row, i) in form.headersList" :key="i" class="kv-row">
              <v-checkbox
                v-model="row.enabled"
                hide-details
                density="compact"
                class="param-check flex-shrink-0"
              />
              <v-text-field v-model="row.key" placeholder="Key" density="compact" hide-details class="kv-key" />
              <v-text-field v-model="row.value" placeholder="Value" density="compact" hide-details class="kv-value" />
              <v-btn icon variant="text" size="small" color="error" :disabled="form.headersList.length <= 1" @click="removeHeader(i)">
                <v-icon size="small">mdi-delete-outline</v-icon>
              </v-btn>
            </div>
            <v-btn size="small" variant="tonal" class="mt-1" @click="addHeader">추가</v-btn>
          </div>
        </v-window-item>
        <v-window-item value="body">
          <div class="textarea-col">
            <v-textarea
              v-model="form.requestBody"
              placeholder="요청 본문 입력"
              rows="4"
              density="compact"
              hide-details
              auto-grow
            />
          </div>
        </v-window-item>
      </v-window>
      <v-row dense>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.vus"
            type="number"
            min="1"
            density="compact"
            hide-details="auto"
            :error-messages="errors.vus ? [errors.vus] : []"
          >
            <template #label>
              <span class="label-with-tip">VUs
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>동시에 요청을 보내는 '가상 사용자' 수입니다. 10이면 10명이 동시에 접속한 것처럼 테스트합니다.</span>
              </v-tooltip>
              </span>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.duration"
            type="number"
            min="1"
            density="compact"
            hide-details="auto"
            :error-messages="errors.duration ? [errors.duration] : []"
          >
            <template #label>
              <span class="label-with-tip">지속(초)
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>테스트를 몇 초 동안 진행할지 정합니다.</span>
              </v-tooltip>
              </span>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.requestDelay"
            type="number"
            min="0"
            step="0.1"
            density="compact"
            hide-details
          >
            <template #label>
              <span class="label-with-tip">대기(초)
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>한 번 요청을 보낸 뒤, 다음 요청 전에 기다리는 시간(초)입니다. 0이면 쉬지 않고 연속 요청합니다.</span>
              </v-tooltip>
              </span>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.rampUp"
            type="number"
            min="0"
            density="compact"
            hide-details
          >
            <template #label>
              <span class="label-with-tip">Ramp-up(초)
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>테스트 시작 시 가상 사용자를 0에서 설정한 수까지 서서히 늘리는 시간입니다. 서버에 부담을 줄일 수 있습니다.</span>
              </v-tooltip>
              </span>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.iterations"
            type="number"
            min="1"
            placeholder="선택"
            density="compact"
            hide-details="auto"
            :error-messages="errors.iterations ? [errors.iterations] : []"
          >
            <template #label>
              <span class="label-with-tip">반복 횟수
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>각 가상 사용자가 요청을 몇 번 보낼지입니다. 비워두면 '지속(초)' 동안만 반복합니다.</span>
              </v-tooltip>
              </span>
            </template>
          </v-text-field>
        </v-col>
      </v-row>
      <div class="d-flex align-center flex-wrap mt-2">
        <v-btn type="submit" color="primary" :loading="saving" size="small" class="mr-2">저장</v-btn>
        <v-btn :to="`/tests/${id}/run`" variant="text" color="primary" size="small" class="mr-2">실행</v-btn>
        <v-btn to="/tests" variant="text" size="small">목록으로</v-btn>
      </div>
      <v-alert v-if="apiError" type="error" density="compact" class="mt-2">{{ apiError }}</v-alert>
    </v-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { get, put, getApiErrorMessage } from '../services/api'

const route = useRoute()
const router = useRouter()
const id = computed(() => String(route.params.id))
const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const apiError = ref('')
const errors = reactive({})
const requestTab = ref('params')

const urlDisplay = ref('')

const form = reactive({
  name: '',
  baseUrl: '',
  paramsList: [{ key: '', value: '', enabled: false }],
  httpMethod: 'GET',
  requestBody: '',
  headersList: [{ key: '', value: '', enabled: false }],
  vus: 1,
  duration: 10,
  requestDelay: null,
  rampUp: 0,
  iterations: null,
})

function buildEffectiveUrl() {
  const base = (form.baseUrl || '').trim()
  const pairs = form.paramsList
    .filter((r) => r.enabled !== false && r.key != null && String(r.key).trim())
    .map((r) => encodeURIComponent(String(r.key).trim()) + '=' + encodeURIComponent(r.value != null ? String(r.value).trim() : ''))
  return pairs.length ? base + (base.includes('?') ? '&' : '?') + pairs.join('&') : base
}

function parseUrlAndSyncToParams() {
  const s = (urlDisplay.value || '').trim()
  if (!s) {
    form.baseUrl = ''
    form.paramsList = [{ key: '', value: '', enabled: false }]
    return
  }
  const q = s.indexOf('?')
  const base = q >= 0 ? s.slice(0, q) : s
  form.baseUrl = base
  if (q >= 0 && q < s.length - 1) {
    const query = s.slice(q + 1)
    const list = []
    query.split('&').forEach((pair) => {
      const eq = pair.indexOf('=')
      const k = eq >= 0 ? decodeURIComponent(pair.slice(0, eq).replace(/\+/g, ' ')) : decodeURIComponent(pair.replace(/\+/g, ' '))
      const v = eq >= 0 ? decodeURIComponent(pair.slice(eq + 1).replace(/\+/g, ' ')) : ''
      if (k) list.push({ key: k, value: v, enabled: true })
    })
    form.paramsList = list.length ? list : [{ key: '', value: '', enabled: false }]
  } else {
    form.paramsList = [{ key: '', value: '', enabled: false }]
  }
  urlDisplay.value = buildEffectiveUrl()
}

function syncUrlFromParams() {
  urlDisplay.value = buildEffectiveUrl()
}

function parseQueryParamsToList(str) {
  if (!str || !String(str).trim()) return [{ key: '', value: '', enabled: true }]
  try {
    const arr = JSON.parse(str)
    if (!Array.isArray(arr) || !arr.length) return [{ key: '', value: '', enabled: true }]
    const list = arr.map((item) => {
      const k = item && typeof item === 'object' && 'key' in item ? String(item.key ?? '') : ''
      const v = item && typeof item === 'object' && 'value' in item ? String(item.value ?? '') : ''
      return { key: k, value: v, enabled: true }
    })
    return list.length ? list : [{ key: '', value: '', enabled: true }]
  } catch {
    return [{ key: '', value: '', enabled: true }]
  }
}

function parseHeadersToList(str) {
  if (!str || !String(str).trim()) return [{ key: '', value: '', enabled: true }]
  try {
    const obj = JSON.parse(str)
    if (!obj || typeof obj !== 'object') return [{ key: '', value: '', enabled: true }]
    const entries = Object.entries(obj).map(([k, v]) => ({ key: k, value: String(v ?? ''), enabled: true }))
    return entries.length ? entries : [{ key: '', value: '', enabled: true }]
  } catch {
    return [{ key: '', value: '', enabled: true }]
  }
}

function buildQueryParamsJson() {
  const list = form.paramsList
    .filter((r) => r.enabled !== false && r.key != null && String(r.key).trim())
    .map((r) => ({ key: String(r.key).trim(), value: r.value != null ? String(r.value).trim() : '' }))
  return list.length ? JSON.stringify(list) : undefined
}

watch(
  () => [form.baseUrl, form.paramsList],
  () => { syncUrlFromParams() },
  { deep: true }
)

function addParam() {
  form.paramsList.push({ key: '', value: '', enabled: false })
}

function removeParam(i) {
  if (form.paramsList.length <= 1) return
  form.paramsList.splice(i, 1)
  syncUrlFromParams()
}

function addHeader() {
  form.headersList.push({ key: '', value: '', enabled: false })
}

function removeHeader(i) {
  if (form.headersList.length <= 1) return
  form.headersList.splice(i, 1)
}

function buildHeadersJson() {
  const obj = {}
  form.headersList
    .filter((r) => r.enabled !== false && r.key != null && String(r.key).trim())
    .forEach((r) => {
      obj[String(r.key).trim()] = r.value != null ? String(r.value).trim() : ''
    })
  return Object.keys(obj).length ? JSON.stringify(obj) : undefined
}

const urlPattern = /^https?:\/\/[^\s]+$/

function validate() {
  parseUrlAndSyncToParams()
  const e = {}
  if (!(form.name && form.name.trim())) e.name = '테스트 이름을 입력하세요.'
  const base = (form.baseUrl || '').trim()
  if (!base) e.baseUrl = '대상 URL을 입력하세요.'
  else if (!urlPattern.test(base)) e.baseUrl = '유효한 URL 형식이 아닙니다.'
  if (form.vus != null && (form.vus < 1 || !Number.isInteger(form.vus))) e.vus = '1 이상의 정수를 입력하세요.'
  if (form.duration != null && (form.duration < 1 || !Number.isInteger(form.duration))) e.duration = '1 이상의 정수를 입력하세요.'
  if (form.rampUp != null && (form.rampUp < 0 || !Number.isInteger(form.rampUp))) e.rampUp = '0 이상의 정수를 입력하세요.'
  if (form.iterations != null && form.iterations !== '' && (form.iterations < 1 || !Number.isInteger(form.iterations))) e.iterations = '1 이상의 정수를 입력하세요.'
  Object.assign(errors, e)
  return Object.keys(e).length === 0
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const t = await get(`tests/${id.value}`)
    form.name = t.name ?? ''
    form.baseUrl = t.targetUrl ?? ''
    form.paramsList = parseQueryParamsToList(t.queryParams ?? '')
    form.httpMethod = t.httpMethod ?? 'GET'
    form.requestBody = t.requestBody ?? ''
    form.headersList = parseHeadersToList(t.headers ?? '')
    form.vus = t.vus ?? 1
    form.duration = t.duration ?? 10
    form.requestDelay = t.requestDelay ?? null
    form.rampUp = t.rampUp ?? 0
    form.iterations = t.iterations ?? null
    syncUrlFromParams()
  } catch (err) {
    loadError.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  apiError.value = ''
  if (!validate()) return
  saving.value = true
  try {
    const body = {
      name: form.name.trim(),
      targetUrl: (form.baseUrl || '').trim(),
      queryParams: buildQueryParamsJson(),
      httpMethod: form.httpMethod,
      requestBody: form.requestBody?.trim() || undefined,
      headers: buildHeadersJson(),
      vus: Number(form.vus),
      duration: Number(form.duration),
      requestDelay: form.requestDelay != null && form.requestDelay !== '' ? Number(form.requestDelay) : undefined,
      rampUp: Number(form.rampUp) >= 0 ? Number(form.rampUp) : 0,
      iterations: form.iterations != null && form.iterations !== '' && Number(form.iterations) >= 1 ? Number(form.iterations) : undefined,
    }
    await put(`tests/${id.value}`, body)
    router.push('/tests')
  } catch (err) {
    apiError.value = getApiErrorMessage(err)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.test-form { max-width: 720px; }
.label-tip-icon { vertical-align: middle; }
.label-tip-icon:hover { background-color: #e0e0e0 !important; color: #1a1a1a !important; border-radius: 50%; }
.label-with-tip { user-select: none; -webkit-user-select: none; }
.label-with-tip:hover { color: #1a1a1a; background-color: rgba(255, 255, 255, 0.95); border-radius: 4px; }
.compact-form :deep(.v-field),
.compact-form :deep(.v-field__input),
.compact-form :deep(input),
.compact-form :deep(textarea) { font-size: 1rem; }
.compact-form :deep(.v-field .v-label),
.compact-form :deep(.v-field__outline .v-label) { transition: none !important; }

.textarea-row { align-items: stretch; }
.textarea-col {
  display: block;
  margin-bottom: 8px;
}
.textarea-col:last-of-type { margin-bottom: 0; }
.textarea-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  opacity: 0.8;
  margin-bottom: 4px;
  line-height: 1.2;
}
.request-tabs { min-height: 36px; }
/* 마우스 올렸을 때만: 밝은 배경 + 진한 글씨 */
.request-tabs :deep(.v-tab:hover),
.request-tabs :deep(.v-tab:hover::before),
.request-tabs :deep(.v-tab .v-btn:hover),
.request-tabs :deep(.v-tab .v-btn:hover::before),
.request-tabs :deep(.v-tab .v-btn__overlay),
.request-tabs :deep(.v-tab:hover .v-btn__overlay) { background-color: #e8e8e8 !important; background: #e8e8e8 !important; color: #1a1a1a !important; opacity: 1 !important; }
.request-tabs :deep(.v-tab:hover .v-icon),
.request-tabs :deep(.v-tab .v-btn:hover .v-icon) { color: #1a1a1a !important; }
.request-window { min-height: 120px; }
.kv-section { margin-bottom: 8px; }
.kv-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.kv-row:hover { background-color: rgba(0, 0, 0, 0.04); border-radius: 4px; }
.kv-row:hover :deep(.v-field),
.kv-row:hover :deep(.v-field__input),
.kv-row:hover :deep(input),
.kv-row :deep(.v-checkbox:hover .v-label),
.kv-row :deep(.v-checkbox .v-label) { color: #1a1a1a !important; }
.kv-row .param-check { flex: 0 0 40px; }
.kv-row .kv-key { flex: 0 0 160px; max-width: 180px; }
.kv-row .kv-value { flex: 1; min-width: 0; }
.textarea-col { padding: 0; }
.textarea-col :deep(.v-field) { align-items: flex-start; }
</style>
