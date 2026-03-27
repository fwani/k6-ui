<template>
  <label class="ui-checkbox">
    <input
      ref="inputRef"
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      @change="onChange"
    />
    <span v-if="label" class="ui-checkbox__label">{{ label }}</span>
  </label>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  label: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  indeterminate: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const inputRef = ref(null)

function syncIndeterminate() {
  const el = inputRef.value
  if (el) el.indeterminate = props.indeterminate
}

function onChange(e) {
  emit('update:modelValue', e.target.checked)
}

watch(
  () => [props.indeterminate, props.modelValue],
  () => syncIndeterminate(),
  { flush: 'post' },
)

onMounted(() => syncIndeterminate())
</script>

<style scoped>
.ui-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
}
.ui-checkbox input {
  width: 18px;
  height: 18px;
  accent-color: var(--accent-success);
}
</style>
