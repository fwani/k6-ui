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
    <v-expansion-panels class="mb-3" variant="accordion">
      <v-expansion-panel>
        <v-expansion-panel-title class="text-body-2">
          다음 실행에 붙일 헤더 (인증·Cookie 등)
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <p class="text-caption text-medium-emphasis mb-2">
            브라우저에만 저장되며 테스트 정의에는 올라가지 않습니다. 실행 시 테스트에 저장된 Headers와 합쳐지고, 같은 이름은 여기 값이 우선합니다.
          </p>
          <v-sheet border rounded class="pa-3 mb-3 text-caption text-medium-emphasis">
            <p class="mb-2 font-weight-medium text-high-emphasis">필드 설명 (부하가 치는 <strong>대상 API</strong> 요청에 붙습니다)</p>
            <ul class="pl-4 mb-0" style="list-style: disc; line-height: 1.5">
              <li class="mb-1">
                <strong>Bearer 토큰</strong>: OAuth/JWT 등 <strong>액세스 토큰 문자열만</strong> 입력합니다.
                앞에 <code class="code-chip">Bearer</code> 를 붙이지 않아도 되며, 실행 시 <code class="code-chip">Authorization: Bearer …</code> 로 자동 조합됩니다.
                이미 <code class="code-chip">Bearer xxx</code> 형태면 그대로 둬도 됩니다.
              </li>
              <li class="mb-1">
                <strong>헤더 이름</strong>: HTTP 요청 헤더의 <strong>키</strong>입니다. 예:
                <code class="code-chip">Cookie</code>,
                <code class="code-chip">X-Api-Key</code>,
                <code class="code-chip">Authorization</code>(Bearer 칸 대신 직접 넣을 때).
              </li>
              <li>
                <strong>값</strong>: 위 이름에 대응하는 <strong>헤더 전체 값</strong>입니다.
                세션 쿠키는 개발자 도구 등에서 복사한 쿠키 문자열을 넣고, 이름에 <code class="code-chip">Cookie</code> 를 적습니다.
              </li>
            </ul>
          </v-sheet>
          <v-text-field
            v-model="runHdr.bearer"
            label="Bearer 토큰 (선택)"
            type="password"
            autocomplete="off"
            density="compact"
            hide-details="auto"
            class="mb-1"
          />
          <p class="text-caption text-medium-emphasis mb-3">비우면 이 칸은 사용하지 않습니다.</p>
          <div v-for="(row, i) in runHdr.extras" :key="i" class="d-flex flex-wrap align-center gap-2 mb-2">
            <v-text-field
              v-model="row.key"
              label="헤더 이름"
              placeholder="Cookie, X-Api-Key …"
              density="compact"
              hide-details="auto"
              class="flex-grow-1"
              style="min-width: 140px"
            />
            <v-text-field
              v-model="row.value"
              label="값"
              placeholder="헤더에 실릴 문자열 전체"
              density="compact"
              hide-details="auto"
              class="flex-grow-1"
              style="min-width: 160px"
            />
            <v-btn
              icon="mdi-delete-outline"
              variant="text"
              size="small"
              :disabled="runHdr.extras.length <= 1"
              aria-label="행 삭제"
              @click="removeExtraRow(i)"
            />
          </div>
          <v-btn size="small" variant="text" class="mb-2" @click="addExtraRow">헤더 행 추가</v-btn>
          <v-checkbox
            v-model="runHdr.persist"
            label="이 브라우저에 기억 (localStorage)"
            density="compact"
            hide-details
            class="mt-1"
          />
          <div class="d-flex flex-wrap gap-2 mt-2">
            <v-btn size="small" color="primary" @click="saveRunHdr">저장</v-btn>
            <v-btn size="small" variant="text" @click="clearRunHdr">모두 지우기</v-btn>
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get, del, getApiErrorMessage } from '../services/api'
import {
  loadRunHeadersForm,
  saveRunHeadersForm,
  clearRunHeadersForm,
} from '../services/runHeaders'

const router = useRouter()
const items = ref([])
const selectedIds = ref([])
const loading = ref(true)
const error = ref('')

const runHdr = reactive({
  bearer: '',
  extras: [{ key: '', value: '' }],
  persist: false,
})

function applyLoadedRunHdr() {
  const x = loadRunHeadersForm()
  runHdr.bearer = x.bearer
  runHdr.extras = x.extras.length ? x.extras.map((r) => ({ ...r })) : [{ key: '', value: '' }]
  runHdr.persist = x.persist
}

function addExtraRow() {
  runHdr.extras.push({ key: '', value: '' })
}

function removeExtraRow(i) {
  if (runHdr.extras.length <= 1) return
  runHdr.extras.splice(i, 1)
}

function saveRunHdr() {
  saveRunHeadersForm({
    bearer: runHdr.bearer,
    extras: runHdr.extras.map((r) => ({ key: r.key, value: r.value })),
    persist: runHdr.persist,
  })
}

function clearRunHdr() {
  clearRunHeadersForm()
  runHdr.bearer = ''
  runHdr.extras = [{ key: '', value: '' }]
  runHdr.persist = false
}

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

onMounted(() => {
  applyLoadedRunHdr()
  load()
})
</script>

<style scoped>
.compact-table :deep(th),
.compact-table :deep(td) {
  padding: 4px 8px;
}
.code-chip {
  font-size: 0.85em;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.07);
  font-family: ui-monospace, monospace;
}
</style>
