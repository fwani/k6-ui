<template>
  <div ref="rootEl" class="inline-tag-editor">
    <div
      v-if="!editMode"
      class="inline-tag-editor__display"
      role="button"
      tabindex="0"
      title="클릭하여 태그 편집"
      @click.stop="enterEdit"
      @keydown.enter.prevent="enterEdit"
    >
      <template v-if="displayTags.length">
        <UiChip
          v-for="tag in displayTags.slice(0, 4)"
          :key="tag"
          size="x-small"
          :color="tagColorKey(tag)"
          class="mr-1 mb-1"
        >
          {{ tag }}
        </UiChip>
        <span v-if="displayTags.length > 4" class="text-caption text-medium-emphasis">
          +{{ displayTags.length - 4 }}
        </span>
      </template>
      <span v-else class="text-caption text-medium-emphasis inline-tag-editor__placeholder">태그 추가…</span>
    </div>
    <div v-else class="inline-tag-editor__panel" @click.stop>
      <div class="inline-tag-editor__panel-body">
        <p v-if="saveError" class="inline-tag-editor__err">{{ saveError }}</p>
        <p v-if="localTags.length" class="tags-chips d-flex flex-wrap gap-1 mb-2">
          <UiChip
            v-for="(tg, ti) in localTags"
            :key="ti + '-' + tg"
            closable
            size="x-small"
            :color="tagColorKey(tg)"
            @click:close="removeTag(ti)"
          >
            {{ tg }}
          </UiChip>
        </p>
        <div class="tag-input-wrap">
          <UiTextField
            v-model="tagDraft"
            label=""
            placeholder="검색 또는 새 태그 · Enter"
            hide-details="auto"
            :disabled="saving"
            @focus="onTagInputFocus"
            @blur="onTagInputBlur"
            @keydown.enter.prevent="onTagEnter"
            @keydown.down.prevent="onTagArrowDown"
            @keydown.up.prevent="onTagArrowUp"
          />
          <ul
            v-show="tagInputFocused && filteredSuggestions.length"
            class="tag-suggest-list"
            role="listbox"
          >
            <li
              v-for="(s, idx) in filteredSuggestions"
              :key="s"
              role="option"
              class="tag-suggest-list__item"
              :class="{ 'tag-suggest-list__item--active': idx === tagHighlightIndex }"
              @mousedown.prevent="selectSuggestion(s)"
            >
              {{ s }}
            </li>
          </ul>
        </div>
      </div>
      <div class="inline-tag-editor__actions">
        <UiBtn
          color="primary"
          variant="flat"
          native-type="button"
          :loading="saving"
          :disabled="saving"
          @click.stop="saveAndClose"
        >
          적용
        </UiBtn>
        <UiBtn variant="text" native-type="button" :disabled="saving" @click.stop="cancelEdit">
          취소
        </UiBtn>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { get, put, getApiErrorMessage } from '../services/api'
import { normalizeTagList, tagColorKey } from '../utils/tags'
import UiTextField from './UiTextField.vue'
import UiChip from './UiChip.vue'
import UiBtn from './UiBtn.vue'

const props = defineProps({
  tags: { type: Array, default: () => [] },
  testId: { type: String, required: true },
})

const emit = defineEmits(['saved'])

const rootEl = ref(null)
const editMode = ref(false)
const localTags = ref([])
const tagDraft = ref('')
const existingTagNames = ref([])
/** 제안 목록은 입력란에 포커스가 있을 때만 표시 */
const tagInputFocused = ref(false)
const tagHighlightIndex = ref(-1)
const saving = ref(false)
const saveError = ref('')

const displayTags = computed(() => normalizeTagList(props.tags))

const filteredSuggestions = computed(() => {
  const needle = (tagDraft.value || '').trim().toLowerCase()
  const pool = existingTagNames.value.filter((t) => !localTags.value.includes(t))
  if (!needle) return pool.slice(0, 40)
  return pool.filter((t) => t.toLowerCase().includes(needle)).slice(0, 40)
})

watch(filteredSuggestions, (list) => {
  tagHighlightIndex.value = list.length ? 0 : -1
})

async function loadExistingTags() {
  try {
    const data = await get('tests/tags')
    existingTagNames.value = Array.isArray(data.items) ? data.items : []
  } catch {
    existingTagNames.value = []
  }
}

function onTagInputFocus() {
  tagInputFocused.value = true
}

function onTagInputBlur() {
  window.setTimeout(() => {
    tagInputFocused.value = false
  }, 200)
}

function onTagArrowDown() {
  const list = filteredSuggestions.value
  if (!list.length) return
  tagInputFocused.value = true
  const n = list.length
  if (tagHighlightIndex.value < 0) tagHighlightIndex.value = 0
  else tagHighlightIndex.value = (tagHighlightIndex.value + 1) % n
}

function onTagArrowUp() {
  const list = filteredSuggestions.value
  if (!list.length) return
  tagInputFocused.value = true
  const n = list.length
  if (tagHighlightIndex.value < 0) tagHighlightIndex.value = n - 1
  else tagHighlightIndex.value = (tagHighlightIndex.value - 1 + n) % n
}

function onTagEnter() {
  const list = filteredSuggestions.value
  if (
    tagInputFocused.value
    && list.length > 0
    && tagHighlightIndex.value >= 0
    && tagHighlightIndex.value < list.length
  ) {
    selectSuggestion(list[tagHighlightIndex.value])
    return
  }
  addTagsFromDraft()
}

function selectSuggestion(name) {
  addTagNamed(name)
}

function addTagNamed(name) {
  const t = String(name || '').trim().slice(0, 32)
  if (!t || localTags.value.includes(t)) return
  if (localTags.value.length >= 32) return
  localTags.value.push(t)
  tagDraft.value = ''
}

function addTagsFromDraft() {
  const raw = (tagDraft.value || '').trim()
  if (!raw) return
  const parts = raw.split(/[,，]/).map((s) => s.trim()).filter(Boolean)
  const seen = new Set(localTags.value.map((x) => String(x)))
  for (const p of parts) {
    const t = p.slice(0, 32)
    if (!t || seen.has(t)) continue
    if (localTags.value.length >= 32) break
    seen.add(t)
    localTags.value.push(t)
  }
  tagDraft.value = ''
}

function removeTag(i) {
  localTags.value.splice(i, 1)
}

async function enterEdit() {
  saveError.value = ''
  localTags.value = [...displayTags.value]
  tagDraft.value = ''
  tagInputFocused.value = false
  editMode.value = true
  await nextTick()
  document.addEventListener('click', onDocClick, true)
  window.addEventListener('keydown', onEscape, true)
  loadExistingTags()
}

function cancelEdit() {
  if (saving.value) return
  saveError.value = ''
  editMode.value = false
  document.removeEventListener('click', onDocClick, true)
  window.removeEventListener('keydown', onEscape, true)
}

function onEscape(e) {
  if (e.key !== 'Escape' || !editMode.value || saving.value) return
  const ae = document.activeElement
  if (ae && rootEl.value?.contains(ae) && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA')) {
    e.preventDefault()
    e.stopPropagation()
    ae.blur()
    return
  }
  e.preventDefault()
  cancelEdit()
}

function onDocClick(e) {
  if (!editMode.value || !rootEl.value) return
  if (!rootEl.value.contains(e.target)) {
    saveAndClose()
  }
}

async function saveAndClose() {
  if (!editMode.value || saving.value) return
  const next = normalizeTagList(localTags.value)
  const prev = displayTags.value
  if (next.length === prev.length && next.every((x, i) => x === prev[i])) {
    cancelEdit()
    return
  }
  saving.value = true
  saveError.value = ''
  try {
    await put(`tests/${props.testId}`, { tags: next })
    emit('saved', next)
  } catch (err) {
    saveError.value = getApiErrorMessage(err)
    saving.value = false
    return
  }
  saving.value = false
  cancelEdit()
}

</script>

<style scoped>
.inline-tag-editor {
  position: relative;
  min-height: 28px;
}
.inline-tag-editor__display {
  cursor: pointer;
  border-radius: 6px;
  padding: 2px 4px;
  margin: -2px -4px;
  outline: none;
}
.inline-tag-editor__display:hover {
  background: color-mix(in srgb, var(--text-primary) 6%, transparent);
}
.inline-tag-editor__display:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--accent-success) 55%, transparent);
  outline-offset: 1px;
}
.inline-tag-editor__placeholder {
  font-style: italic;
}
.inline-tag-editor__panel {
  position: relative;
  z-index: 30;
  display: flex;
  flex-direction: column;
  min-width: 260px;
  max-width: min(360px, 92vw);
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border-default);
  background: var(--bg-elevated, var(--bg-surface));
  box-shadow: 0 8px 24px color-mix(in srgb, var(--text-primary) 14%, transparent);
}
.inline-tag-editor__panel-body {
  flex: 1 1 auto;
  min-width: 0;
}
.inline-tag-editor__err {
  font-size: 12px;
  color: var(--accent-danger);
  margin: 0 0 8px;
}
.inline-tag-editor__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  flex-shrink: 0;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-default);
}
.tag-input-wrap {
  position: relative;
}
.tag-input-wrap :deep(.field-label) {
  display: none;
}
.tag-suggest-list {
  position: absolute;
  z-index: 40;
  left: 0;
  right: 0;
  top: 100%;
  margin: 4px 0 0;
  padding: 4px 0;
  list-style: none;
  max-height: 200px;
  overflow-y: auto;
  border-radius: 8px;
  border: 1px solid var(--border-default, rgba(0, 0, 0, 0.12));
  background: var(--bg-elevated, var(--bg-default, #fff));
  box-shadow: 0 4px 12px color-mix(in srgb, var(--text-primary, #000) 12%, transparent);
}
.tag-suggest-list__item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 0.875rem;
}
.tag-suggest-list__item:hover,
.tag-suggest-list__item--active {
  background: color-mix(in srgb, var(--text-primary) 8%, transparent);
}
</style>
