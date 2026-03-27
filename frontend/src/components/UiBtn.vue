<template>
  <router-link v-if="to" :to="to" :class="btnClass">
    <slot />
  </router-link>
  <a v-else-if="href" :href="href" :target="target" :rel="rel" :class="btnClass">
    <slot />
  </a>
  <button
    v-else
    :type="nativeType"
    :class="btnClass"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="ui-btn__spinner" aria-hidden="true" />
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  to: { type: [String, Object], default: undefined },
  href: { type: String, default: undefined },
  target: { type: String, default: undefined },
  rel: { type: String, default: undefined },
  variant: { type: String, default: 'text' },
  color: { type: String, default: undefined },
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  nativeType: { type: String, default: 'button' },
  icon: { type: Boolean, default: false },
})

defineEmits(['click'])

const btnClass = computed(() => {
  const c = ['btn', 'ui-btn']
  if (props.icon) {
    c.push('btn-icon')
    return c.join(' ')
  }
  if (props.variant === 'flat' && props.color === 'primary') {
    c.push('btn-primary')
  } else if (props.variant === 'flat' && props.color === 'error') {
    c.push('btn-danger')
  } else if (props.variant === 'outlined') {
    c.push('btn-outline')
  } else if (props.variant === 'text' && props.color === 'primary') {
    c.push('btn-ghost', 'ui-btn--text-primary')
  } else {
    c.push('btn-ghost')
  }
  return c.join(' ')
})
</script>

<style scoped>
.ui-btn--text-primary {
  color: var(--accent-success) !important;
}
.ui-btn__spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 6px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: ui-spin 0.7s linear infinite;
  vertical-align: middle;
}
@keyframes ui-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
