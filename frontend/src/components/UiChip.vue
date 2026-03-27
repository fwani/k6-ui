<template>
  <span :class="['pill', chipClass, denseClass]">
    <slot />
    <button
      v-if="closable"
      type="button"
      class="ui-chip__close"
      aria-label="제거"
      @click="$emit('click:close')"
    >
      ×
    </button>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  color: { type: String, default: 'primary' },
  size: { type: String, default: 'small' },
  closable: { type: Boolean, default: false },
  variant: { type: String, default: 'tonal' },
})

defineEmits(['click:close'])

const chipClass = computed(() => {
  const c = props.color
  if (c === 'error') return 'pill-error'
  if (c === 'primary') return 'pill-k6'
  if (c === 'warning') return 'pill-warning'
  if (c === 'browser') return 'pill-browser'
  if (c === 'idle') return 'pill-idle'
  if (typeof c === 'string' && /^tag-[0-7]$/.test(c)) return `pill-${c}`
  return 'pill-idle'
})

const denseClass = computed(() => (props.size === 'x-small' ? 'ui-chip--xs' : ''))
</script>

<style scoped>
.ui-chip__close {
  margin-left: 4px;
  padding: 0 2px;
  border: none;
  background: none;
  cursor: pointer;
  color: inherit;
  font-size: 14px;
  line-height: 1;
}
.ui-chip--xs {
  font-size: 11px;
  padding: 2px 8px;
}
</style>
