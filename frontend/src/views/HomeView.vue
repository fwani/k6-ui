<template>
  <div>
    <h1 class="text-h5 mb-2">성능 테스트</h1>
    <p class="text-body-2 text-medium-emphasis mb-4">
      테스트를 정의하고 실행한 뒤, 실행 목록에서 상세·결과를 확인하세요.
    </p>

    <div class="d-flex flex-wrap gap-3 mb-6">
      <v-card
        to="/tests"
        variant="tonal"
        class="flex-grow-1"
        min-width="160"
        style="cursor: pointer"
      >
        <v-card-text class="d-flex align-center gap-2">
          <v-icon size="large">mdi-format-list-bulleted</v-icon>
          <div>
            <div class="text-subtitle-1 font-weight-medium">테스트 목록</div>
            <div class="text-caption text-medium-emphasis">테스트 정의·수정</div>
          </div>
        </v-card-text>
      </v-card>
      <v-card
        to="/runs"
        variant="tonal"
        class="flex-grow-1"
        min-width="160"
        style="cursor: pointer"
      >
        <v-card-text class="d-flex align-center gap-2">
          <v-icon size="large">mdi-play-circle-outline</v-icon>
          <div>
            <div class="text-subtitle-1 font-weight-medium">실행 목록</div>
            <div class="text-caption text-medium-emphasis">실행 이력·상세·결과</div>
          </div>
        </v-card-text>
      </v-card>
    </div>

    <h2 class="text-subtitle-1 font-weight-medium mb-2">최근 실행</h2>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" style="max-width: 400px" />
    <template v-else-if="recent.length">
      <v-list density="compact" class="bg-transparent" style="max-width: 560px">
        <v-list-item
          v-for="r in recent"
          :key="r.id"
          :to="`/runs/${r.id}`"
          class="px-0"
        >
          <template #prepend>
            <v-chip :color="statusColor(r.status)" size="small" variant="flat" class="mr-2">
              {{ r.status }}
            </v-chip>
          </template>
          <v-list-item-title>{{ r.testName }}</v-list-item-title>
          <v-list-item-subtitle>{{ formatDate(r.startedAt) }}</v-list-item-subtitle>
          <template #append>
            <v-btn :to="`/runs/${r.id}/result`" variant="text" size="small" color="primary" @click.stop>결과</v-btn>
          </template>
        </v-list-item>
      </v-list>
      <v-btn to="/runs" variant="text" size="small" class="mt-2">전체 실행 목록</v-btn>
    </template>
    <p v-else class="text-body-2 text-medium-emphasis">최근 실행 이력이 없습니다.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { get } from '../services/api'

const loading = ref(true)
const recent = ref([])

function statusColor(status) {
  const s = (status || '').toLowerCase()
  if (s === 'finished') return 'success'
  if (s === 'failed') return 'error'
  if (s === 'running') return 'warning'
  return 'default'
}

function formatDate(d) {
  if (!d) return '—'
  const dt = new Date(typeof d === 'string' && !/Z|[+-]\d{2}:?\d{2}$/.test(d) ? d.replace(/\.\d+$/, '') + 'Z' : d)
  if (Number.isNaN(dt.getTime())) return '—'
  return dt.toLocaleString('ko-KR', { dateStyle: 'short', timeStyle: 'short' })
}

onMounted(async () => {
  try {
    const res = await get('runs?page=1&limit=5')
    recent.value = res.items || []
  } catch {
    recent.value = []
  } finally {
    loading.value = false
  }
})
</script>
