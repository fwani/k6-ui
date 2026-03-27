<template>
  <div class="page-section">
    <div class="d-flex align-center justify-space-between mb-2 flex-wrap gap-2">
      <h1 class="page-title mb-0">실행 결과 목록 (히스토리)</h1>
      <UiBtn
        v-if="items.length"
        color="error"
        variant="flat"
        :disabled="selectedIds.length === 0"
        @click="confirmDelete"
      >
        선택 삭제 ({{ selectedIds.length }})
      </UiBtn>
    </div>
    <UiProgress v-if="loading" indeterminate class="mb-2" />
    <UiAlert v-else-if="error" type="error" closable class="mb-2" @close="error = ''">{{ error }}</UiAlert>
    <template v-else>
      <table v-if="items.length" class="compact-table">
        <thead>
          <tr>
            <th style="width: 48px">
              <UiCheckbox
                :model-value="deletableIds.length > 0 && selectedIds.length === deletableIds.length"
                :indeterminate="selectedIds.length > 0 && selectedIds.length < deletableIds.length"
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
              <UiCheckbox
                :model-value="selectedIds.includes(r.id)"
                :disabled="r.status === 'Running'"
                @update:model-value="(v) => toggleSelect(r.id, v)"
              />
            </td>
            <td>{{ r.testName }}</td>
            <td>
              <span :class="enginePillClass(r.engine)">
                <span class="pill-dot" aria-hidden="true" />
                {{ r.engine === 'browser' ? '브라우저' : 'HTTP' }}
              </span>
            </td>
            <td>
              <span :class="statusPillClass(r.status)">
                <span class="pill-dot" aria-hidden="true" />
                {{ r.status }}
              </span>
            </td>
            <td>{{ formatDate(r.startedAt) }}</td>
            <td>{{ formatDate(r.finishedAt) }}</td>
            <td class="text-medium-emphasis text-body-2">
              <template v-if="r.resultSummary">
                평균 {{ formatMs(r.resultSummary.avgResponseTime) }} / 종합
                {{ formatPercent(r.resultSummary.overallFailureRate ?? 0) }}
              </template>
              <span v-else>—</span>
            </td>
            <td>
              <UiBtn :to="`/runs/${r.id}`" variant="text" color="primary">상세</UiBtn>
              <UiBtn :to="`/runs/${r.id}/result`" variant="text" color="primary">결과</UiBtn>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="text-body-2 text-medium-emphasis">실행 이력이 없습니다.</p>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { get, del, getApiErrorMessage } from '../services/api'
import { statusPillClass, enginePillClass } from '../utils/statusPill'
import UiBtn from '../components/UiBtn.vue'
import UiProgress from '../components/UiProgress.vue'
import UiAlert from '../components/UiAlert.vue'
import UiCheckbox from '../components/UiCheckbox.vue'

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
