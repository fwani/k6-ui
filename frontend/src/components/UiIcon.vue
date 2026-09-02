<template>
  <i :class="['mdi', icon, sizeClass]" aria-hidden="true" />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** e.g. mdi-delete-outline (second part only: delete-outline) — pass full after mdi- */
  icon: { type: String, required: true },
  size: { type: [String, Number], default: undefined },
})

const sizeClass = computed(() => {
  if (props.size == null) return 'ui-icon--md'
  const n = Number(props.size)
  if (!Number.isNaN(n)) return `ui-icon--px-${n}`
  return `ui-icon--${props.size}`
})
</script>

<style scoped>
.ui-icon--md {
  font-size: 1.25rem;
}
.ui-icon--px-20 {
  font-size: 20px;
}
.ui-icon--small {
  font-size: 14px;
}
.ui-icon--x-small {
  font-size: 12px;
}
.ui-icon--large {
  font-size: 1.75rem;
}
</style>
