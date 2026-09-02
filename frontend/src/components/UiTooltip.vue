<template>
  <span class="ui-tooltip" @mouseenter="open = true" @mouseleave="open = false">
    <slot />
    <span v-show="open" class="ui-tooltip__pop" role="tooltip">{{ text }}</span>
  </span>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  text: { type: String, default: '' },
})

const open = ref(false)
</script>

<style scoped>
.ui-tooltip {
  position: relative;
  display: inline-flex;
  vertical-align: middle;
}
.ui-tooltip__pop {
  position: absolute;
  z-index: 50;
  left: 50%;
  bottom: calc(100% + 6px);
  transform: translateX(-50%);
  min-width: 160px;
  max-width: 320px;
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.45;
  color: var(--text-primary);
  background: var(--bg-elevated);
  border: 0.5px solid var(--border-default);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  pointer-events: none;
}
</style>
