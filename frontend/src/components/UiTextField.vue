<template>
  <div class="field ui-text-field">
    <label v-if="label" class="field-label">{{ label }}</label>
    <div class="ui-text-field__row">
      <input
        :value="modelValue"
        :type="type"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :disabled="disabled"
        :min="min"
        :max="max"
        :step="step"
        class="ui-text-field__input"
        @input="$emit('update:modelValue', $event.target.value)"
        @focus="$emit('focus', $event)"
        @blur="$emit('blur', $event)"
        @keydown="$emit('keydown', $event)"
        @change="$emit('change', $event)"
      />
      <span v-if="$slots.append" class="ui-text-field__append">
        <slot name="append" />
      </span>
    </div>
    <p v-if="hint && !showError" class="field-hint">{{ hint }}</p>
    <p v-if="showError" class="field-error">{{ errorMessages[0] }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: undefined },
  autocomplete: { type: String, default: undefined },
  disabled: { type: Boolean, default: false },
  min: { type: [String, Number], default: undefined },
  max: { type: [String, Number], default: undefined },
  step: { type: [String, Number], default: undefined },
  errorMessages: { type: Array, default: () => [] },
  hideDetails: { type: [String, Boolean], default: false },
  hint: { type: String, default: '' },
})

defineEmits(['update:modelValue', 'focus', 'blur', 'keydown', 'change'])

const showError = computed(() => {
  if (!props.errorMessages?.length) return false
  if (props.hideDetails === true) return false
  return true
})
</script>

<style scoped>
.ui-text-field__row {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}
.ui-text-field__input {
  flex: 1;
  min-width: 0;
}
.ui-text-field__append {
  flex-shrink: 0;
}
.field-hint {
  font-size: 11px;
  color: var(--text-secondary);
  margin: 4px 0 0;
}
.field-error {
  font-size: 12px;
  color: var(--accent-danger);
  margin: 4px 0 0;
}
</style>
