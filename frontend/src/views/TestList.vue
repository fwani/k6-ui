<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-2">
      <h1 class="text-h5">테스트 목록</h1>
      <v-btn color="primary" to="/tests/new" prepend-icon="mdi-plus" size="small">새 테스트</v-btn>
    </div>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
    <v-alert v-else-if="error" type="error" closable density="compact" class="mb-2">{{ error }}</v-alert>
    <template v-else>
      <v-table v-if="items.length" class="compact-table">
        <thead>
          <tr>
            <th>이름</th>
            <th>대상 URL</th>
            <th>메서드</th>
            <th>VUs</th>
            <th>지속(초)</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in items" :key="t.id">
            <td>{{ t.name }}</td>
            <td class="text-truncate" style="max-width: 200px">{{ t.targetUrl }}</td>
            <td>{{ t.httpMethod }}</td>
            <td>{{ t.vus }}</td>
            <td>{{ t.duration }}</td>
            <td>
              <v-btn :to="`/tests/${t.id}/edit`" variant="text" size="small" color="primary">수정</v-btn>
              <v-btn :to="`/tests/${t.id}/run`" variant="text" size="small" color="primary">실행</v-btn>
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
import { get, getApiErrorMessage } from '../services/api'

const items = ref([])
const loading = ref(true)
const error = ref('')

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
