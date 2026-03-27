<template>
  <div class="ui-pagination d-flex align-center gap-2 flex-wrap">
    <button type="button" class="btn btn-ghost" :disabled="modelValue <= 1" @click="go(1)">«</button>
    <button type="button" class="btn btn-ghost" :disabled="modelValue <= 1" @click="go(modelValue - 1)">‹</button>
    <span class="text-caption" style="color: var(--text-secondary)">{{ modelValue }} / {{ length }}</span>
    <button
      type="button"
      class="btn btn-ghost"
      :disabled="modelValue >= length"
      @click="go(modelValue + 1)"
    >
      ›
    </button>
    <button
      type="button"
      class="btn btn-ghost"
      :disabled="modelValue >= length"
      @click="go(length)"
    >
      »
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: { type: Number, default: 1 },
  length: { type: Number, default: 1 },
})

const emit = defineEmits(['update:modelValue'])

function go(p) {
  const next = Math.min(Math.max(1, p), props.length)
  emit('update:modelValue', next)
}
</script>
