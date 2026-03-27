<template>
  <div :class="['ui-alert', `ui-alert--${type}`]" role="alert">
    <button
      v-if="closable"
      type="button"
      class="ui-alert__close btn btn-ghost"
      aria-label="닫기"
      @click="$emit('close')"
    >
      ×
    </button>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  type: { type: String, default: 'info' },
  closable: { type: Boolean, default: false },
})
defineEmits(['close'])
</script>

<style scoped>
.ui-alert {
  padding: 8px 12px;
  border-radius: 8px;
  border: 0.5px solid var(--border-default);
  font-size: 13px;
  position: relative;
}
.ui-alert--error {
  background: color-mix(in srgb, var(--accent-danger) 12%, transparent);
  color: var(--text-primary);
  border-color: color-mix(in srgb, var(--accent-danger) 35%, transparent);
}
.ui-alert--info {
  background: color-mix(in srgb, var(--accent-info) 10%, transparent);
  color: var(--text-primary);
}
.ui-alert--warning {
  background: color-mix(in srgb, var(--accent-warning) 12%, transparent);
  color: var(--text-primary);
}
.ui-alert__close {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: auto;
  padding: 0 6px;
  line-height: 1;
}
</style>
