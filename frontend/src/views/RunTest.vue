<template>
  <div class="run-test">
    <h1 class="text-h5 mb-2">테스트 실행</h1>
    <v-progress-linear v-if="testLoading" indeterminate color="primary" class="mb-2" />
    <v-alert v-else-if="testError" type="error" density="compact" class="mb-2">{{ testError }}</v-alert>
    <v-card v-else-if="test" variant="outlined" class="pa-3">
      <p class="text-subtitle-1 mb-2">{{ test.name }}</p>
      <template v-if="!runId">
        <v-btn color="primary" :loading="starting" @click="startRun">시작</v-btn>
      </template>
      <template v-else>
        <p class="mb-2">
          상태:
          <v-chip
            :color="statusColor(run?.status)"
            size="small"
            variant="flat"
            class="ml-1"
          >
            {{ run?.status ?? '조회 중...' }}
          </v-chip>
        </p>
        <div v-if="run?.status === 'Running'" class="mb-2">
          <v-btn color="error" variant="tonal" :loading="stopping" @click="stopRun">중지</v-btn>
        </div>
        <div v-if="run && (run.status === 'Finished' || run.status === 'Failed')" class="mt-2">
          <v-btn :to="`/runs/${run.id}/result`" color="primary" variant="text">결과 보기</v-btn>
        </div>
      </template>
      <v-alert v-if="apiError" type="error" density="compact" class="mt-2">{{ apiError }}</v-alert>
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { get, post, getApiErrorMessage } from '../services/api'

const route = useRoute()
const testId = route.params.id

const test = ref(null)
const testLoading = ref(true)
const testError = ref('')
const runId = ref(null)
const run = ref(null)
const starting = ref(false)
const stopping = ref(false)
const apiError = ref('')
let pollTimer = null

function statusColor(status) {
  const s = (status || '').toLowerCase()
  if (s === 'finished') return 'success'
  if (s === 'failed') return 'error'
  if (s === 'running') return 'warning'
  return 'default'
}

async function loadTest() {
  testLoading.value = true
  testError.value = ''
  try {
    test.value = await get(`tests/${testId}`)
  } catch (err) {
    testError.value = getApiErrorMessage(err)
  } finally {
    testLoading.value = false
  }
}

async function startRun() {
  starting.value = true
  apiError.value = ''
  try {
    const res = await post(`tests/${testId}/runs`, null)
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

watch(runId, (id) => {
  if (pollTimer) clearTimeout(pollTimer)
  pollTimer = null
  if (id) pollRun()
})

onMounted(loadTest)
onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
})
</script>

<style scoped>
.run-test { max-width: 600px; }
</style>
