<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-2 flex-wrap gap-2">
      <h1 class="text-h5 mb-0">실행 결과 목록 (히스토리)</h1>
      <v-btn
        v-if="items.length"
        color="error"
        variant="outlined"
        size="small"
        :disabled="selectedIds.length === 0"
        @click="confirmDelete"
      >
        선택 삭제 ({{ selectedIds.length }})
      </v-btn>
    </div>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
    <v-alert v-else-if="error" type="error" closable density="compact" class="mb-2">{{ error }}</v-alert>
    <template v-else>
      <v-table v-if="items.length" class="compact-table">
        <thead>
          <tr>
            <th style="width: 48px">
              <v-checkbox
                :model-value="deletableIds.length > 0 && selectedIds.length === deletableIds.length"
                :indeterminate="selectedIds.length > 0 && selectedIds.length < deletableIds.length"
                hide-details
                density="compact"
                @update:model-value="toggleSelectAll"
              />
            </th>
            <th>테스트 이름</th>
            <th>엔진</th>
            <th>상태</th>
            <th>시작</th>
            <th>종료</th>
            <th>요약</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in items" :key="r.id">
            <td>
              <v-checkbox
                :model-value="selectedIds.includes(r.id)"
                :disabled="r.status === 'Running'"
                hide-details
                density="compact"
                @update:model-value="(v) => toggleSelect(r.id, v)"
              />
            </td>
            <td>{{ r.testName }}</td>
            <td class="text-body-2">{{ r.engine === 'browser' ? '브라우저' : 'HTTP' }}</td>
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
              <v-btn :to="`/runs/${r.id}`" variant="text" size="small" color="primary">상세</v-btn>
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
import { ref, computed, onMounted } from 'vue'
import { get, del, getApiErrorMessage } from '../services/api'

const items = ref([])
const selectedIds = ref([])
const loading = ref(true)
const error = ref('')

const deletableIds = computed(() => items.value.filter((r) => r.status !== 'Running').map((r) => r.id))

function toggleSelect(id, checked) {
  if (checked) {
    if (!selectedIds.value.includes(id)) selectedIds.value = [...selectedIds.value, id]
  } else {
    selectedIds.value = selectedIds.value.filter((x) => x !== id)
  }
}

function toggleSelectAll(checked) {
  if (checked) {
    selectedIds.value = [...deletableIds.value]
  } else {
    selectedIds.value = []
  }
}

function confirmDelete() {
  const n = selectedIds.value.length
  if (n === 0) return
  if (!window.confirm(`선택한 ${n}건을 삭제할까요?`)) return
  doDelete()
}

async function doDelete() {
  const ids = [...selectedIds.value]
  error.value = ''
  for (const id of ids) {
    try {
      await del(`runs/${id}`)
    } catch (err) {
      error.value = getApiErrorMessage(err)
      await load()
      return
    }
  }
  selectedIds.value = []
  await load()
}

function statusColor(status) {
  const s = (status || '').toLowerCase()
  if (s === 'finished') return 'success'
  if (s === 'failed') return 'error'
  if (s === 'running') return 'warning'
  return 'default'
}

function formatDate(d) {
  if (!d) return '—'
  const iso = typeof d === 'string' ? d.trim() : d
  const utcStr =
    typeof iso === 'string' && !/Z|[+-]\d{2}:?\d{2}$/.test(iso) ? iso.replace(/\.\d+$/, '') + 'Z' : iso
  const dt = new Date(utcStr)
  if (Number.isNaN(dt.getTime())) return '—'
  const y = dt.getFullYear()
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const day = String(dt.getDate()).padStart(2, '0')
  const h = String(dt.getHours()).padStart(2, '0')
  const min = String(dt.getMinutes()).padStart(2, '0')
  const sec = String(dt.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}:${sec}`
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
