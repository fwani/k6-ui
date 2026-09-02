<template>
  <div class="page-section">
    <h1 class="page-title">성능 테스트</h1>
    <p class="page-lead">
      테스트를 정의하고 실행한 뒤, 실행 목록에서 상세·결과를 확인하세요.
    </p>

    <div class="d-flex flex-wrap gap-3 mb-6">
      <router-link
        to="/tests"
        class="surface-card flex-grow-1 text-decoration-none"
        style="min-width: 160px"
      >
        <div class="d-flex align-center gap-2">
          <UiIcon icon="mdi-format-list-bulleted" size="large" class="text-primary" />
          <div>
            <div class="surface-card__title">테스트 목록</div>
            <div class="surface-card__sub">테스트 정의·수정</div>
          </div>
        </div>
      </router-link>
      <router-link
        to="/runs"
        class="surface-card flex-grow-1 text-decoration-none"
        style="min-width: 160px"
      >
        <div class="d-flex align-center gap-2">
          <UiIcon icon="mdi-play-circle-outline" size="large" class="text-primary" />
          <div>
            <div class="surface-card__title">실행 목록</div>
            <div class="surface-card__sub">실행 이력·상세·결과</div>
          </div>
        </div>
      </router-link>
    </div>

    <h2 class="text-subtitle-1 font-weight-medium mb-2" style="color: var(--text-primary)">최근 실행</h2>
    <UiProgress v-if="loading" indeterminate class="mb-2" style="max-width: 400px" />
    <template v-else-if="recent.length">
      <ul class="home-recent-list">
        <li v-for="r in recent" :key="r.id" class="home-recent-item">
          <router-link :to="`/runs/${r.id}`" class="home-recent-link">
            <span :class="statusPillClass(r.status)" class="mr-2">
              <span class="pill-dot" aria-hidden="true" />
              {{ r.status }}
            </span>
            <span class="home-recent-name">{{ r.testName }}</span>
            <span class="home-recent-date text-caption text-medium-emphasis">{{ formatDate(r.startedAt) }}</span>
          </router-link>
          <UiBtn :to="`/runs/${r.id}/result`" variant="text" color="primary" @click.stop>결과</UiBtn>
        </li>
      </ul>
      <UiBtn to="/runs" variant="text" color="primary" class="mt-2">전체 실행 목록</UiBtn>
    </template>
    <p v-else class="text-body-2" style="color: var(--text-secondary)">최근 실행 이력이 없습니다.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { get } from '../services/api'
import { statusPillClass } from '../utils/statusPill'
import UiProgress from '../components/UiProgress.vue'
import UiBtn from '../components/UiBtn.vue'
import UiIcon from '../components/UiIcon.vue'

const loading = ref(true)
const recent = ref([])

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

<style scoped>
.text-primary {
  color: var(--accent-success);
}
.text-decoration-none {
  text-decoration: none;
  color: inherit;
}
.home-recent-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-width: 560px;
}
.home-recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 0.5px solid var(--border-default);
}
.home-recent-link {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  flex: 1;
  min-width: 0;
  text-decoration: none;
  color: inherit;
}
.home-recent-name {
  flex: 1;
  min-width: 0;
}
</style>
