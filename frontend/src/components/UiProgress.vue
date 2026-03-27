<template>
  <div class="progress-track ui-progress" :class="{ 'ui-progress--indeterminate': indeterminate }">
    <div v-if="indeterminate" class="progress-bar ui-progress__bar" />
  </div>
</template>

<script setup>
defineProps({
  indeterminate: { type: Boolean, default: false },
})
</script>

<style scoped>
.ui-progress--indeterminate .ui-progress__bar {
  width: 35%;
  animation: ui-progress-slide 1.1s ease-in-out infinite;
}

@keyframes ui-progress-slide {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(400%);
  }
}
</style>
