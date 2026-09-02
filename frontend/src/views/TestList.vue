<template>
  <div class="page-section">
    <div class="d-flex align-center justify-space-between mb-2 flex-wrap gap-2">
      <h1 class="page-title mb-0">테스트 목록</h1>
      <div class="d-flex align-center gap-2 flex-wrap">
        <UiSelect
          v-model="tagFilter"
          :items="tagSelectItems"
          label="태그"
          hide-details
          class="tag-filter-select"
          style="max-width: 220px; min-width: 160px"
        />
        <UiBtn
          v-if="items.length"
          color="error"
          variant="flat"
          :disabled="selectedIds.length === 0"
          @click="confirmDelete"
        >
          선택 삭제 ({{ selectedIds.length }})
        </UiBtn>
        <UiBtn variant="outlined" to="/tests/new">
          <UiIcon icon="mdi-plus" size="small" class="mr-1" />
          새 테스트
        </UiBtn>
      </div>
    </div>
    <details class="ui-expansion mb-3">
      <summary class="text-body-2">다음 실행에 붙일 헤더 (인증·Cookie 등)</summary>
      <div class="ui-expansion__body">
        <p class="text-caption text-medium-emphasis mb-2">
          브라우저에만 저장되며 테스트 정의에는 올라가지 않습니다. 실행 시 테스트에 저장된 Headers와 합쳐지고, 같은 이름은 여기 값이 우선합니다.
        </p>
        <div class="ui-sheet-bordered pa-3 mb-3 text-caption text-medium-emphasis">
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
        </div>
        <UiTextField
          v-model="runHdr.bearer"
          label="Bearer 토큰 (선택)"
          type="password"
          autocomplete="off"
          hide-details="auto"
          class="mb-1"
        />
        <p class="text-caption text-medium-emphasis mb-3">비우면 이 칸은 사용하지 않습니다.</p>
        <div v-for="(row, i) in runHdr.extras" :key="i" class="d-flex flex-wrap align-center gap-2 mb-2">
          <UiTextField
            v-model="row.key"
            label="헤더 이름"
            placeholder="Cookie, X-Api-Key …"
            hide-details="auto"
            class="flex-grow-1"
            style="min-width: 140px"
          />
          <UiTextField
            v-model="row.value"
            label="값"
            placeholder="헤더에 실릴 문자열 전체"
            hide-details="auto"
            class="flex-grow-1"
            style="min-width: 160px"
          />
          <UiBtn
            icon
            variant="text"
            :disabled="runHdr.extras.length <= 1"
            aria-label="행 삭제"
            @click="removeExtraRow(i)"
          >
            <UiIcon icon="mdi-delete-outline" size="small" />
          </UiBtn>
        </div>
        <UiBtn variant="text" class="mb-2" @click="addExtraRow">헤더 행 추가</UiBtn>
        <UiCheckbox v-model="runHdr.persist" label="이 브라우저에 기억 (localStorage)" class="mt-1" />
        <div class="d-flex flex-wrap gap-2 mt-2">
          <UiBtn color="primary" variant="flat" @click="saveRunHdr">저장</UiBtn>
          <UiBtn variant="text" @click="clearRunHdr">모두 지우기</UiBtn>
        </div>
      </div>
    </details>
    <UiProgress v-if="loading" indeterminate class="mb-2" />
    <UiAlert v-else-if="error" type="error" closable class="mb-2" @close="error = ''">{{ error }}</UiAlert>
    <template v-else>
      <table v-if="items.length" class="compact-table">
        <thead>
          <tr>
            <th style="width: 48px">
              <UiCheckbox
                :model-value="allPageSelected"
                :indeterminate="pageSelectionIndeterminate"
                @update:model-value="toggleSelectAll"
              />
            </th>
            <th>이름</th>
            <th>태그</th>
            <th>대상 URL</th>
            <th>메서드</th>
            <th>VUs</th>
            <th>제한 시간(초)</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in displayItems" :key="t.id">
            <td>
              <UiCheckbox
                :model-value="selectedIds.includes(t.id)"
                @update:model-value="(v) => toggleSelect(t.id, v)"
              />
            </td>
            <td>{{ t.name }}</td>
            <td class="tag-cell" style="max-width: 280px; vertical-align: top">
              <InlineTagEditor :tags="t.tags" :test-id="t.id" @saved="(tags) => onTagsSaved(t, tags)" />
            </td>
            <td class="text-truncate" style="max-width: 200px">{{ t.targetUrl }}</td>
            <td>{{ t.httpMethod }}</td>
            <td>{{ t.vus }}</td>
            <td>{{ t.duration }}</td>
            <td>
              <UiBtn :to="`/tests/${t.id}/edit`" variant="text" color="primary">수정</UiBtn>
              <UiBtn :to="`/tests/${t.id}/run`" variant="text" color="primary">실행</UiBtn>
              <UiBtn variant="text" @click="cloneTest(t)">복제</UiBtn>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="text-body-2 text-medium-emphasis">
        등록된 테스트가 없습니다.
        <UiBtn to="/tests/new" variant="text" color="primary">새 테스트 만들기</UiBtn>
      </p>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get, del, getApiErrorMessage } from '../services/api'
import {
  loadRunHeadersForm,
  saveRunHeadersForm,
  clearRunHeadersForm,
} from '../services/runHeaders'
import UiBtn from '../components/UiBtn.vue'
import UiProgress from '../components/UiProgress.vue'
import UiAlert from '../components/UiAlert.vue'
import UiCheckbox from '../components/UiCheckbox.vue'
import UiTextField from '../components/UiTextField.vue'
import UiSelect from '../components/UiSelect.vue'
import UiIcon from '../components/UiIcon.vue'
import InlineTagEditor from '../components/InlineTagEditor.vue'

const router = useRouter()
const items = ref([])
const tagFilter = ref('')
const selectedIds = ref([])
const loading = ref(true)
const error = ref('')

const tagOptions = computed(() => {
  const s = new Set()
  for (const t of items.value) {
    const arr = Array.isArray(t.tags) ? t.tags : []
    for (const x of arr) {
      const u = String(x ?? '').trim()
      if (u) s.add(u)
    }
  }
  return [...s].sort()
})

const tagSelectItems = computed(() => {
  const opts = [{ title: '전체', value: '' }]
  for (const t of tagOptions.value) {
    opts.push({ title: t, value: t })
  }
  return opts
})

const displayItems = computed(() => {
  if (tagFilter.value == null || tagFilter.value === '') return items.value
  const needle = String(tagFilter.value).trim()
  return items.value.filter((t) => {
    const arr = Array.isArray(t.tags) ? t.tags : []
    return arr.map((x) => String(x ?? '').trim()).includes(needle)
  })
})

const pageSelectionCount = computed(() => {
  const ids = displayItems.value.map((t) => t.id)
  return ids.filter((id) => selectedIds.value.includes(id)).length
})

const allPageSelected = computed(
  () => displayItems.value.length > 0 && pageSelectionCount.value === displayItems.value.length,
)

const pageSelectionIndeterminate = computed(
  () => pageSelectionCount.value > 0 && pageSelectionCount.value < displayItems.value.length,
)

function onTagsSaved(row, tags) {
  row.tags = Array.isArray(tags) ? [...tags] : []
}

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
    selectedIds.value = displayItems.value.map((t) => t.id)
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
.code-chip {
  font-size: 0.82em;
  padding: 1px 6px;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  background: color-mix(in srgb, var(--accent-success) 12%, transparent);
  color: var(--accent-success);
  border: 0.5px solid color-mix(in srgb, var(--accent-success) 25%, transparent);
}
.tag-filter-select :deep(.field-label) {
  font-size: 11px;
}
.tag-cell {
  overflow: visible;
}
</style>
