<template>
  <div>
    <h1 class="text-h5 mb-2">실행 목록 (히스토리)</h1>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
    <v-alert v-else-if="error" type="error" closable density="compact" class="mb-2">{{ error }}</v-alert>
    <template v-else>
      <v-table v-if="items.length" class="compact-table">
        <thead>
          <tr>
            <th>테스트 이름</th>
            <th>상태</th>
            <th>시작</th>
            <th>종료</th>
            <th>요약</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in items" :key="r.id">
            <td>{{ r.testName }}</td>
            <td>
              <v-chip
                :color="statusColor(r.status)"
                size="small"
                variant="flat"
              >
                {{ r.status }}
              </v-chip>
            </td>
            <td>{{ formatDate(r.startedAt) }}</td>
            <td>{{ formatDate(r.finishedAt) }}</td>
            <td class="text-medium-emphasis text-body-2">
              <template v-if="r.resultSummary">
                평균 {{ formatMs(r.resultSummary.avgResponseTime) }} / 실패율 {{ formatPercent(r.resultSummary.failureRate) }}
              </template>
              <span v-else>—</span>
            </td>
            <td>
              <v-btn :to="`/runs/${r.id}/result`" variant="text" size="small" color="primary">결과</v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
      <p v-else class="text-body-2 text-medium-emphasis">실행 이력이 없습니다.</p>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { get, getApiErrorMessage } from '../services/api'

const items = ref([])
const loading = ref(true)
const error = ref('')

function statusColor(status) {
  const s = (status || '').toLowerCase()
  if (s === 'finished') return 'success'
  if (s === 'failed') return 'error'
  if (s === 'running') return 'warning'
  return 'default'
}

function formatDate(d) {
  if (!d) return '—'
  const dt = new Date(d)
  return dt.toLocaleString()
}

function formatMs(ms) {
  if (ms == null) return '—'
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`
  return `${Number(ms).toFixed(0)}ms`
}

function formatPercent(rate) {
  if (rate == null) return '—'
  return `${(rate * 100).toFixed(2)}%`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await get('runs?page=1&limit=50')
    items.value = res.items || []
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.compact-table :deep(th),
.compact-table :deep(td) {
  padding: 4px 8px;
}
</style>
