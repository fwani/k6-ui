<template>
  <div class="run-test">
    <div class="d-flex align-center justify-space-between mb-3">
      <h1 class="text-h5 mb-0">{{ isRunDetail ? '실행 상세' : '테스트 실행' }}</h1>
      <v-btn v-if="test && !isRunDetail" variant="text" size="small" :to="`/tests/${testId}/edit`">수정</v-btn>
    </div>
    <v-progress-linear v-if="testLoading || (isRunDetail && runLoading)" indeterminate color="primary" class="mb-3" />
    <v-alert v-else-if="testError" type="error" density="compact" class="mb-3">{{ testError }}</v-alert>
    <template v-else-if="test || (isRunDetail && run)">
      <div class="d-flex flex-wrap align-center gap-3 mb-3">
        <span class="text-subtitle-1 font-weight-medium">{{ displayName }}</span>
        <template v-if="!isRunDetail">
          <span v-if="test" class="text-body-2 text-medium-emphasis">{{ engineLabel }}</span>
          <template v-if="!runId">
            <v-btn color="primary" :loading="starting" @click="startRun">시작</v-btn>
          </template>
        </template>
        <template v-if="runId">
          <v-chip
            :color="statusColor(run?.status)"
            size="small"
            variant="flat"
          >
            {{ run?.status ?? '조회 중...' }}
          </v-chip>
          <v-btn v-if="run?.status === 'Running'" color="error" variant="tonal" size="small" :loading="stopping" @click="stopRun">중지</v-btn>
          <v-btn v-else-if="run && (run.status === 'Finished' || run.status === 'Failed')" :to="`/runs/${run.id}/result`" color="primary" variant="text" size="small">결과 보기</v-btn>
        </template>
      </div>
      <v-alert v-if="apiError" type="error" density="compact" class="mb-3">{{ apiError }}</v-alert>

      <template v-if="runId">
        <p class="text-subtitle-2 mb-1">실행 로그</p>
        <div
          ref="logPanelRef"
          class="log-panel"
        >
          <pre class="log-content">{{ logContent || '실행을 시작하면 로그가 표시됩니다.' }}</pre>
        </div>
      </template>
    </template>
    <v-alert v-else-if="isRunDetail && !run && !testLoading" type="info" density="compact">실행 정보를 불러오는 중입니다.</v-alert>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { get, post, getApiErrorMessage } from '../services/api'

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
let pollTimer = null
let logPollTimer = null

const displayName = computed(() => run.value?.testName ?? test.value?.name ?? '—')

function statusColor(status) {
  const s = (status || '').toLowerCase()
  if (s === 'finished') return 'success'
  if (s === 'failed') return 'error'
  if (s === 'running') return 'warning'
  return 'default'
}

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
    const res = await post(`tests/${testId.value}/runs`, {})
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
    logContent.value = res.log ?? ''
    await nextTick()
    if (logPanelRef.value) {
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
  background: rgb(var(--v-theme-surface-variant));
  padding: 12px;
}
.log-content {
  margin: 0;
  font-family: ui-monospace, monospace;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-all;
  color: rgb(var(--v-theme-on-surface-variant));
}
</style>
