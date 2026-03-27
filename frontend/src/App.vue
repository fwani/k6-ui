<template>
  <div class="app-root">
    <header class="app-shell">
      <div class="app-shell__left">
        <router-link to="/" class="app-title app-title-link">성능 테스트</router-link>
        <nav class="app-shell__nav" aria-label="주요 메뉴">
          <router-link to="/" class="app-nav-link" exact-active-class="app-nav-link--active">홈</router-link>
          <router-link to="/tests" class="app-nav-link" active-class="app-nav-link--active">테스트 목록</router-link>
          <router-link to="/runs" class="app-nav-link" active-class="app-nav-link--active">실행 목록</router-link>
        </nav>
      </div>
      <div class="app-shell__right">
        <button type="button" class="btn btn-icon" aria-label="테마 전환" @click="onToggleTheme">
          <UiIcon :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'" size="20" />
        </button>
      </div>
    </header>
    <main class="app-main-area">
      <div class="app-container">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { initTheme, toggleTheme } from './utils/theme'
import UiIcon from './components/UiIcon.vue'

const theme = ref('dark')

onMounted(() => {
  initTheme()
  theme.value = document.documentElement.dataset.theme || 'dark'
})

function onToggleTheme() {
  toggleTheme()
  theme.value = document.documentElement.dataset.theme || 'dark'
}

const isDark = computed(() => theme.value === 'dark')
</script>
