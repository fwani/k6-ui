<template>
  <div class="field ui-textarea">
    <label v-if="label" class="field-label">{{ label }}</label>
    <textarea
      :value="modelValue"
      :rows="rows"
      :placeholder="placeholder"
      :disabled="disabled"
      class="ui-textarea__input"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <p v-if="errorMessages?.length && hideDetails !== true" class="field-error">{{ errorMessages[0] }}</p>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  rows: { type: [String, Number], default: 4 },
  placeholder: { type: String, default: undefined },
  disabled: { type: Boolean, default: false },
  errorMessages: { type: Array, default: () => [] },
  hideDetails: { type: [String, Boolean], default: false },
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.ui-textarea__input {
  min-height: 80px;
  resize: vertical;
}
.field-error {
  font-size: 12px;
  color: var(--accent-danger);
  margin: 4px 0 0;
}
</style>
