<template>
  <div class="run-result">
    <h1 class="text-h5 mb-2">테스트 결과</h1>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
    <v-alert v-else-if="error" type="error" density="compact" class="mb-2">{{ error }}</v-alert>
    <template v-else-if="result">
      <v-sheet class="pa-3 mb-2" rounded>
        <v-list density="compact" class="py-0">
          <v-list-item>
            <v-list-item-title>평균 응답 시간</v-list-item-title>
            <template #append>{{ formatMs(result.avgResponseTime) }}</template>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>최대 응답 시간</v-list-item-title>
            <template #append>{{ formatMs(result.maxResponseTime) }}</template>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>실패율</v-list-item-title>
            <template #append>{{ formatPercent(result.failureRate) }}</template>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>요청 수</v-list-item-title>
            <template #append>{{ result.requestCount }}</template>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>TPS/RPS</v-list-item-title>
            <template #append>{{ result.tpsOrRps?.toFixed(2) ?? '-' }}</template>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>실행 시간</v-list-item-title>
            <template #append>{{ result.executionTime?.toFixed(1) ?? '-' }}초</template>
          </v-list-item>
        </v-list>
      </v-sheet>
      <v-alert v-if="result.errorMessage" type="error" variant="tonal" density="compact" class="mb-2">
        <template #title>실패 사유</template>
        <pre class="text-caption overflow-auto" style="max-height: 20em; white-space: pre-wrap; word-break: break-all;">{{ result.errorMessage }}</pre>
      </v-alert>
      <p v-if="grafanaUrl">
        <v-btn :href="grafanaUrl" target="_blank" rel="noopener" color="primary" variant="text">Grafana 대시보드 열기</v-btn>
      </p>
      <p v-else class="text-body-2 text-medium-emphasis">Grafana URL이 설정되지 않았습니다.</p>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { get, getApiErrorMessage } from '../services/api'

const route = useRoute()
const runId = route.params.id

const result = ref(null)
const grafanaUrl = ref('')
const loading = ref(true)
const error = ref('')

function formatMs(ms) {
  if (ms == null) return '-'
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`
  return `${Number(ms).toFixed(2)}ms`
}

function formatPercent(rate) {
  if (rate == null) return '-'
  return `${(rate * 100).toFixed(2)}%`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [resResult, resConfig] = await Promise.all([
      get(`runs/${runId}/result`),
      get('config').catch(() => ({})),
    ])
    result.value = resResult
    grafanaUrl.value = resConfig.grafanaDashboardUrl || ''
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.run-result { max-width: 560px; }
</style>
