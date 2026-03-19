<template>
  <div>
    <h1 class="text-h5 mb-2">{{ isEdit ? '테스트 수정' : '테스트 생성' }}</h1>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
    <v-alert v-else-if="loadError" type="error" density="compact" class="mb-2">{{ loadError }}</v-alert>
    <v-form v-else @submit.prevent="onSubmit" class="test-form compact-form">
      <v-row dense>
        <v-col cols="12" sm="5" md="3">
          <v-text-field
            v-model="form.name"
            required
            density="compact"
            hide-details="auto"
            :error-messages="errors.name ? [errors.name] : []"
            label="테스트 이름"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>나중에 구분하기 위한 이름입니다.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="12" sm="4" md="2">
          <v-radio-group
            v-model="form.engine"
            inline
            density="compact"
            hide-details
            label="실행 방식"
            class="engine-radio"
          >
            <v-radio label="k6 (HTTP)" value="http" />
            <v-radio label="브라우저 (렌더링)" value="browser" />
          </v-radio-group>
        </v-col>
        <v-col cols="12" sm="3" md="2">
          <v-select
            v-model="form.httpMethod"
            :items="['GET', 'POST', 'PUT', 'DELETE']"
            density="compact"
            hide-details
            label="HTTP 메서드"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>요청 방식입니다. 보통 조회는 GET, 데이터 전송은 POST를 씁니다.</span>
              </v-tooltip>
            </template>
          </v-select>
        </v-col>
        <v-col cols="12" sm="4" md="5">
          <v-text-field
            :model-value="urlDisplay"
            placeholder="https://example.com?a=b"
            density="compact"
            hide-details="auto"
            :error-messages="errors.baseUrl ? [errors.baseUrl] : []"
            label="대상 URL"
            @update:model-value="urlDisplay = $event"
            @blur="parseUrlAndSyncToParams"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>부하를 줄 웹 주소입니다. VU마다 다른 URL을 쓰려면 경로에 <code>{{ vuPlaceholder }}</code>를 넣거나, 아래 "경로 끝에 VU 번호 붙이기"를 사용하세요.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="12" class="d-flex align-center">
          <v-checkbox
            v-model="form.vuUrlSuffix"
            label="경로 끝에 VU 번호 붙이기"
            density="compact"
            hide-details
          />
          <span class="text-caption text-medium-emphasis ml-1">(예: /a/b/ccc → /a/b/ccc1, ccc2)</span>
        </v-col>
      </v-row>
      <v-row dense>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.vus"
            type="number"
            min="1"
            density="compact"
            hide-details="auto"
            :error-messages="errors.vus ? [errors.vus] : []"
            label="VUs"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>동시에 요청을 보내는 '가상 사용자' 수입니다. 10이면 10명이 동시에 접속한 것처럼 테스트합니다.</span>
              </v-tooltip>
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
            label="제한 시간(초)"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>테스트가 실행될 수 있는 최대 시간(초)입니다.</span>
              </v-tooltip>
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
            label="대기(초)"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>한 번 요청을 보낸 뒤, 다음 요청 전에 기다리는 시간(초)입니다. 0이면 쉬지 않고 연속 요청합니다.</span>
              </v-tooltip>
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
            label="Ramp-up(초)"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>테스트 시작 시 가상 사용자를 0에서 설정한 수까지 서서히 늘리는 시간입니다. 서버에 부담을 줄일 수 있습니다.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.iterations"
            type="number"
            min="1"
            placeholder="비우면 제한 시간만큼"
            density="compact"
            hide-details="auto"
            :error-messages="errors.iterations ? [errors.iterations] : []"
            label="반복 횟수 (선택)"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>각 가상 사용자가 요청을 보낼 횟수입니다. 비워두면 제한 시간(초) 동안만 반복합니다. 입력 시 1 이상의 정수.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.bodyPreviewSize"
            type="number"
            min="0"
            max="10000"
            density="compact"
            hide-details
            label="응답 본문 미리보기(자)"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>각 요청 응답 본문을 저장할 때 잘라낼 글자 수입니다. 0이면 저장하지 않습니다.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
      </v-row>
      <br/>
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
              <v-text-field v-model="row.value" :placeholder="`Value (VU별: value-${vuPlaceholder})`" density="compact" hide-details class="kv-value" @update:model-value="syncUrlFromParams" />
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
              <v-text-field v-model="row.value" :placeholder="`Value (VU별: value-${vuPlaceholder})`" density="compact" hide-details class="kv-value" />
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
              :placeholder="`요청 본문 입력. VU마다 다르게 하려면 본문에 ${vuPlaceholder}를 넣으세요.`"
              rows="4"
              density="compact"
              hide-details
              auto-grow
            />
          </div>
        </v-window-item>
      </v-window>
      <div class="mt-2">
        <v-text-field
          v-model="form.errorPagePattern"
          label="에러 페이지 판별 문자열"
          placeholder="요청 URL 또는 응답 본문 검사 (비우면 미사용)"
          density="compact"
          hide-details
        />
        <v-select
          v-model="form.errorPageMatchMode"
          label="판별 방식"
          :items="[
            { title: '포함 시 실패', value: 'contains' },
            { title: '미포함 시 실패', value: 'not_contains' },
          ]"
          item-title="title"
          item-value="value"
          density="compact"
          hide-details
          class="mt-1"
        />
      </div>
      <div class="d-flex align-center flex-wrap mt-2">
        <v-btn type="submit" color="primary" :loading="saving" size="small" class="mr-2">저장</v-btn>
        <v-btn v-if="isEdit" :to="`/tests/${testId}/run`" variant="text" color="primary" size="small" class="mr-2">실행</v-btn>
        <v-btn to="/tests" variant="text" size="small">목록으로</v-btn>
      </div>
      <v-alert v-if="apiError" type="error" density="compact" class="mt-2">{{ apiError }}</v-alert>
    </v-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { get, post, put, getApiErrorMessage } from '../services/api'

const vuPlaceholder = '{{VU}}'
const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.name === 'test-edit')
const testId = computed(() => (isEdit.value ? String(route.params.id) : ''))
const cloneFromId = computed(() => (route.query.cloneFrom ? String(route.query.cloneFrom) : ''))
const loading = ref(false)
const loadError = ref('')
const saving = ref(false)
const apiError = ref('')
const errors = reactive({})
const requestTab = ref('params')
const urlDisplay = ref('')

const form = reactive({
  name: '',
  engine: 'http',
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
  bodyPreviewSize: 500,
  vuUrlSuffix: false,
  errorPagePattern: '',
  errorPageMatchMode: 'contains',
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

function buildQueryParamsJson() {
  const list = form.paramsList
    .filter((r) => r.enabled !== false && r.key != null && String(r.key).trim())
    .map((r) => ({ key: String(r.key).trim(), value: r.value != null ? String(r.value).trim() : '' }))
  return list.length ? JSON.stringify(list) : undefined
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

function parseQueryParamsToList(str) {
  if (!str || !String(str).trim()) return [{ key: '', value: '', enabled: false }]
  try {
    const arr = JSON.parse(str)
    if (!Array.isArray(arr) || !arr.length) return [{ key: '', value: '', enabled: false }]
    const list = arr.map((item) => {
      const k = item && typeof item === 'object' && 'key' in item ? String(item.key ?? '') : ''
      const v = item && typeof item === 'object' && 'value' in item ? String(item.value ?? '') : ''
      return { key: k, value: v, enabled: true }
    })
    return list.length ? list : [{ key: '', value: '', enabled: false }]
  } catch {
    return [{ key: '', value: '', enabled: false }]
  }
}

function parseHeadersToList(str) {
  if (!str || !String(str).trim()) return [{ key: '', value: '', enabled: false }]
  try {
    const obj = JSON.parse(str)
    if (!obj || typeof obj !== 'object') return [{ key: '', value: '', enabled: false }]
    const entries = Object.entries(obj).map(([k, v]) => ({ key: k, value: String(v ?? ''), enabled: true }))
    return entries.length ? entries : [{ key: '', value: '', enabled: false }]
  } catch {
    return [{ key: '', value: '', enabled: false }]
  }
}

function fillFormFromTest(t, clone = false) {
  form.name = clone ? `복사 - ${t.name ?? ''}` : (t.name ?? '')
  form.engine = (t.engine === 'browser' ? 'browser' : 'http')
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
  form.bodyPreviewSize = t.bodyPreviewSize ?? 500
  form.vuUrlSuffix = t.vuUrlSuffix ?? false
  form.errorPagePattern = t.errorPagePattern ?? ''
  form.errorPageMatchMode = (t.errorPageMatchMode === 'not_contains' ? 'not_contains' : 'contains')
  syncUrlFromParams()
}

async function load() {
  if (!testId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const t = await get(`tests/${testId.value}`)
    fillFormFromTest(t, false)
  } catch (err) {
    loadError.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function loadForClone() {
  if (!cloneFromId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const t = await get(`tests/${cloneFromId.value}`)
    fillFormFromTest(t, true)
  } catch (err) {
    loadError.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
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
  const iter = form.iterations
  const iterEmpty = (iter === null || iter === '' || (typeof iter === 'number' && Number.isNaN(iter)))
  if (!iterEmpty && (Number(iter) < 1 || !Number.isInteger(Number(iter)))) e.iterations = '1 이상의 정수를 입력하세요.'
  Object.assign(errors, e)
  return Object.keys(e).length === 0
}

async function onSubmit() {
  apiError.value = ''
  if (!validate()) return
  saving.value = true
  try {
    const body = {
      name: form.name.trim(),
      engine: (form.engine === 'browser' ? 'browser' : 'http'),
      targetUrl: (form.baseUrl || '').trim(),
      queryParams: buildQueryParamsJson(),
      httpMethod: form.httpMethod,
      requestBody: form.requestBody?.trim() || undefined,
      headers: buildHeadersJson(),
      vus: Number(form.vus),
      duration: Number(form.duration),
      requestDelay: form.requestDelay != null && form.requestDelay !== '' ? Number(form.requestDelay) : undefined,
      rampUp: Number(form.rampUp) >= 0 ? Number(form.rampUp) : 0,
      iterations: (() => {
        const i = form.iterations
        if (i === null || i === '' || (typeof i === 'number' && Number.isNaN(i))) return null
        const n = Number(i)
        return n >= 1 && Number.isInteger(n) ? n : null
      })(),
      bodyPreviewSize: Math.min(10000, Math.max(0, Number(form.bodyPreviewSize) || 500)),
      vuUrlSuffix: Boolean(form.vuUrlSuffix),
      errorPagePattern: (form.errorPagePattern || '').trim() || undefined,
      errorPageMatchMode: (form.errorPageMatchMode === 'not_contains' ? 'not_contains' : 'contains'),
    }
    if (isEdit.value) {
      await put(`tests/${testId.value}`, body)
    } else {
      await post('tests', body)
    }
    router.push('/tests')
  } catch (err) {
    apiError.value = getApiErrorMessage(err)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (isEdit.value) load()
  else if (cloneFromId.value) loadForClone()
  else syncUrlFromParams()
})
</script>

<style scoped>
.test-form { width: 100%; max-width: 1200px; }
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
.kv-row .kv-key { flex: 0 0 200px; min-width: 120px; }
.kv-row .kv-value { flex: 1; min-width: 120px; }
.textarea-col { padding: 0; }
.textarea-col :deep(.v-field) { align-items: flex-start; }
</style>
