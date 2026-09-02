<template>
  <div class="field ui-select">
    <label v-if="label" class="field-label">{{ label }}</label>
    <select
      :value="modelValue"
      class="ui-select__el"
      :disabled="disabled"
      @change="onChange"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option
        v-for="(it, idx) in normalizedItems"
        :key="idx"
        :value="it.value"
      >
        {{ it.title }}
      </option>
    </select>
    <p v-if="errorMessages?.length && hideDetails !== true" class="field-error">{{ errorMessages[0] }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number, Object, null], default: null },
  items: { type: Array, default: () => [] },
  itemTitle: { type: String, default: 'title' },
  itemValue: { type: String, default: 'value' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: undefined },
  disabled: { type: Boolean, default: false },
  errorMessages: { type: Array, default: () => [] },
  hideDetails: { type: [String, Boolean], default: false },
})

const emit = defineEmits(['update:modelValue'])

const normalizedItems = computed(() => {
  return props.items.map((it) => {
    if (typeof it === 'string' || typeof it === 'number') {
      return { title: String(it), value: it }
    }
    return {
      title: it[props.itemTitle] ?? it.title ?? '',
      value: it[props.itemValue] ?? it.value,
    }
  })
})

function onChange(e) {
  const v = e.target.value
  const raw = props.items.find((it) => {
    if (typeof it === 'object' && it !== null) {
      const val = it[props.itemValue] ?? it.value
      return String(val) === v
    }
    return String(it) === v
  })
  if (raw !== undefined && typeof raw === 'object' && raw !== null && !(typeof raw === 'string')) {
    emit('update:modelValue', raw[props.itemValue] ?? raw.value)
  } else {
    const num = Number(v)
    emit('update:modelValue', Number.isNaN(num) ? v : num)
  }
}
</script>

<style scoped>
.field-error {
  font-size: 12px;
  color: var(--accent-danger);
  margin: 4px 0 0;
}
.ui-select__el {
  width: 100%;
}
</style>
