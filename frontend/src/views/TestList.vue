<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-2 flex-wrap gap-2">
      <h1 class="text-h5">테스트 목록</h1>
      <div class="d-flex align-center gap-2">
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
        <v-btn color="primary" to="/tests/new" prepend-icon="mdi-plus" size="small">새 테스트</v-btn>
      </div>
    </div>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
    <v-alert v-else-if="error" type="error" closable density="compact" class="mb-2">{{ error }}</v-alert>
    <template v-else>
      <v-table v-if="items.length" class="compact-table">
        <thead>
          <tr>
            <th style="width: 48px">
              <v-checkbox
                :model-value="selectedIds.length === items.length && items.length > 0"
                :indeterminate="selectedIds.length > 0 && selectedIds.length < items.length"
                hide-details
                density="compact"
                @update:model-value="toggleSelectAll"
              />
            </th>
            <th>이름</th>
            <th>대상 URL</th>
            <th>메서드</th>
            <th>VUs</th>
            <th>제한 시간(초)</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in items" :key="t.id">
            <td>
              <v-checkbox
                :model-value="selectedIds.includes(t.id)"
                hide-details
                density="compact"
                @update:model-value="(v) => toggleSelect(t.id, v)"
              />
            </td>
            <td>{{ t.name }}</td>
            <td class="text-truncate" style="max-width: 200px">{{ t.targetUrl }}</td>
            <td>{{ t.httpMethod }}</td>
            <td>{{ t.vus }}</td>
            <td>{{ t.duration }}</td>
            <td>
              <v-btn :to="`/tests/${t.id}/edit`" variant="text" size="small" color="primary">수정</v-btn>
              <v-btn :to="`/tests/${t.id}/run`" variant="text" size="small" color="primary">실행</v-btn>
              <v-btn variant="text" size="small" color="secondary" @click="cloneTest(t)">복제</v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
      <p v-else class="text-body-2 text-medium-emphasis">
        등록된 테스트가 없습니다.
        <v-btn to="/tests/new" variant="text" size="small" color="primary">새 테스트 만들기</v-btn>
      </p>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get, del, getApiErrorMessage } from '../services/api'

const router = useRouter()
const items = ref([])
const selectedIds = ref([])
const loading = ref(true)
const error = ref('')

function toggleSelect(id, checked) {
  if (checked) {
    if (!selectedIds.value.includes(id)) selectedIds.value = [...selectedIds.value, id]
  } else {
    selectedIds.value = selectedIds.value.filter((x) => x !== id)
  }
}

function toggleSelectAll(checked) {
  if (checked) {
    selectedIds.value = items.value.map((t) => t.id)
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

function cloneTest(t) {
  router.push({ path: '/tests/new', query: { cloneFrom: t.id } })
}

async function doDelete() {
  const ids = [...selectedIds.value]
  error.value = ''
  for (const id of ids) {
    try {
      await del(`tests/${id}`)
    } catch (err) {
      error.value = getApiErrorMessage(err)
      await load()
      return
    }
  }
  selectedIds.value = []
  await load()
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await get('tests')
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
