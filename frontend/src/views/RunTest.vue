<template>
  <div class="run-test page-section">
    <div class="d-flex align-center justify-space-between mb-3">
      <h1 class="page-title mb-0">{{ isRunDetail ? '실행 상세' : '테스트 실행' }}</h1>
      <UiBtn
        v-if="test && !isRunDetail"
        variant="text"
        color="primary"
        :to="`/tests/${testId}/edit`"
      >
        수정
      </UiBtn>
    </div>
    <UiProgress v-if="testLoading || (isRunDetail && runLoading)" indeterminate class="mb-3" />
    <UiAlert v-else-if="testError" type="error" class="mb-3">{{ testError }}</UiAlert>
    <template v-else-if="test || (isRunDetail && run)">
      <div class="d-flex flex-wrap align-center gap-3 mb-3">
        <span class="text-subtitle-1 font-weight-medium">{{ displayName }}</span>
        <template v-if="!isRunDetail">
          <span v-if="test" class="text-body-2 text-medium-emphasis">{{ engineLabel }}</span>
          <template v-if="!runId">
            <UiCheckbox
              v-if="test?.engine === 'browser'"
              v-model="showBrowserWindow"
              class="show-browser-check"
              label="Chromium 창 띄우기(확인용)"
            />
            <UiBtn color="primary" variant="flat" :loading="starting" @click="startRun">시작</UiBtn>
          </template>
        </template>
        <template v-if="runId">
          <span :class="statusPillClass(run?.status)">
            <span class="pill-dot" aria-hidden="true" />
            {{ run?.status ?? '조회 중...' }}
          </span>
          <UiBtn v-if="run?.status === 'Running'" color="error" variant="flat" :loading="stopping" @click="stopRun">중지</UiBtn>
          <UiBtn
            v-else-if="run && (run.status === 'Finished' || run.status === 'Failed')"
            :to="`/runs/${run.id}/result`"
            color="primary"
            variant="text"
          >
            결과 보기
          </UiBtn>
        </template>
      </div>
      <UiAlert v-if="apiError" type="error" class="mb-3">{{ apiError }}</UiAlert>
      <UiAlert v-if="!isRunDetail && test?.engine === 'browser' && showBrowserWindow" type="info" class="mb-3">
        백엔드가 이 Mac에서 직접 돌아야 창이 보입니다. Docker/원격 서버만 쓰면 DISPLAY 또는 xvfb가 필요합니다.
      </UiAlert>

      <template v-if="runId">
        <p class="text-subtitle-2 mb-1">실행 로그</p>
        <div ref="logPanelRef" class="log-panel">
          <pre class="log-content">{{ logContent || '실행을 시작하면 로그가 표시됩니다.' }}</pre>
        </div>
      </template>
    </template>
    <UiAlert v-else-if="isRunDetail && !run && !testLoading" type="info">실행 정보를 불러오는 중입니다.</UiAlert>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { get, post, getApiErrorMessage } from '../services/api'
import { statusPillClass } from '../utils/statusPill'
import { getRunHeaderOverridesForApi } from '../services/runHeaders'
import UiBtn from '../components/UiBtn.vue'
import UiProgress from '../components/UiProgress.vue'
import UiAlert from '../components/UiAlert.vue'
import UiCheckbox from '../components/UiCheckbox.vue'

const route = useRoute()
const isRunDetail = computed(() => route.name === 'run-detail' && route.params.id)
const testId = computed(() => (isRunDetail.value ? null : route.params.id))
const runIdFromRoute = computed(() => (isRunDetail.value ? route.params.id : null))

const test = ref(null)
const testLoading = ref(true)
const testError = ref('')
const runId = ref(null)
const engineLabel = ref('')
const run = ref(null)
const runLoading = ref(false)
const starting = ref(false)
const stopping = ref(false)
const apiError = ref('')
const logContent = ref('')
const logPanelRef = ref(null)
/** 브라우저 테스트만: POST runs 시 showBrowser */
const showBrowserWindow = ref(false)
let pollTimer = null
let logPollTimer = null

/** 로그 패널이 하단 근처일 때만 폴링 후 자동 스크롤(위로 읽는 중에는 스크롤 유지). */
function isLogPanelNearBottom(el, thresholdPx = 72) {
  if (!el) return true
  const gap = el.scrollHeight - el.scrollTop - el.clientHeight
  return gap <= thresholdPx
}

const displayName = computed(() => run.value?.testName ?? test.value?.name ?? '—')

async function loadTest() {
  if (!testId.value) return
  testLoading.value = true
  testError.value = ''
  try {
    test.value = await get(`tests/${testId.value}`)
    const e = test.value?.engine === 'browser' ? 'browser' : 'http'
    engineLabel.value = e === 'browser' ? '브라우저 (렌더링)' : 'k6 (HTTP)'
  } catch (err) {
    testError.value = getApiErrorMessage(err)
  } finally {
    testLoading.value = false
  }
}

async function loadRunFromRoute() {
  if (!runIdFromRoute.value) return
  runLoading.value = true
  testError.value = ''
  try {
    runId.value = runIdFromRoute.value
    run.value = await get(`runs/${runId.value}`)
  } catch (err) {
    testError.value = getApiErrorMessage(err)
  } finally {
    runLoading.value = false
  }
}

async function startRun() {
  starting.value = true
  apiError.value = ''
  try {
    const o = getRunHeaderOverridesForApi()
    const payload = {}
    if (Object.keys(o).length > 0) payload.requestHeaderOverrides = o
    if (test.value?.engine === 'browser' && showBrowserWindow.value) payload.showBrowser = true
    const res = await post(
      `tests/${testId.value}/runs`,
      Object.keys(payload).length > 0 ? payload : {},
    )
    runId.value = res.id
    run.value = res
  } catch (err) {
    apiError.value = getApiErrorMessage(err)
  } finally {
    starting.value = false
  }
}

async function stopRun() {
  if (!runId.value) return
  stopping.value = true
  apiError.value = ''
  try {
    const res = await post(`runs/${runId.value}/stop`, null)
    run.value = res
  } catch (err) {
    apiError.value = getApiErrorMessage(err)
  } finally {
    stopping.value = false
  }
}

async function pollRun() {
  if (!runId.value) return
  try {
    const res = await get(`runs/${runId.value}`)
    run.value = res
    if (res.status === 'Running') {
      pollTimer = setTimeout(pollRun, 2000)
    } else {
      pollTimer = null
    }
  } catch {
    pollTimer = setTimeout(pollRun, 2000)
  }
}

async function pollLogs() {
  if (!runId.value) return
  try {
    const res = await get(`runs/${runId.value}/logs`)
    const panel = logPanelRef.value
    const followTail = isLogPanelNearBottom(panel)
    logContent.value = res.log ?? ''
    await nextTick()
    if (followTail && logPanelRef.value) {
      logPanelRef.value.scrollTop = logPanelRef.value.scrollHeight
    }
  } catch {
    // ignore
  }
  if (runId.value && run.value?.status === 'Running') {
    logPollTimer = setTimeout(pollLogs, 1000)
  }
}

watch(runId, (id) => {
  if (pollTimer) clearTimeout(pollTimer)
  pollTimer = null
  if (logPollTimer) clearTimeout(logPollTimer)
  logPollTimer = null
  logContent.value = ''
  if (id) {
    pollRun()
    pollLogs()
  }
})

onMounted(() => {
  if (isRunDetail.value) {
    testLoading.value = false
    loadRunFromRoute()
  } else {
    loadTest()
  }
})
onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
  if (logPollTimer) clearTimeout(logPollTimer)
})
</script>

<style scoped>
.run-test {
  width: 100%;
}
.log-panel {
  height: 50vh;
  min-height: 280px;
  overflow: auto;
  background: var(--bg-elevated);
  border: 0.5px solid var(--border-default);
  border-radius: 8px;
  padding: 12px;
}
.show-browser-check {
  max-width: 220px;
}
.log-content {
  margin: 0;
  font-family: ui-monospace, monospace;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-secondary);
}
</style>
