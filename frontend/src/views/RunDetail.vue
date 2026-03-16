<template>
  <div>
    <h1 class="text-h5 mb-2">실행 상세</h1>
    <p class="text-body-2 text-medium-emphasis">상세 (Phase 4에서 구현)</p>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
const runId = route.params.id
</script>
