<template>
  <v-app>
    <v-app-bar color="primary" density="compact">
      <v-app-bar-title>성능 테스트</v-app-bar-title>
      <v-spacer />
      <v-btn to="/" variant="text">홈</v-btn>
      <v-btn to="/tests" variant="text">테스트 목록</v-btn>
      <v-btn to="/runs" variant="text">실행 목록</v-btn>
    </v-app-bar>
    <v-main>
      <v-container fluid class="py-3 px-0">
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
</script>

<style>
/* v-card hover: 연한 노란색 (전체 공통) */
.v-card {
  position: relative;
  overflow: hidden;
}
.v-card:hover::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  background-color: #fffde7;
  opacity: 0.7;
  pointer-events: none;
}
.v-card > * {
  position: relative;
  z-index: 1;
}

/* 툴팁 가독성: 밝은 배경 + 진한 글씨 */
.v-tooltip .v-overlay__content {
  background: #fff !important;
  color: #1a1a1a !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
/* 탭 호버 시: 우리가 밝은 레이어를 덮고, 글씨 강제로 진하게 */
.v-tabs .v-tab {
  position: relative;
}
.v-tabs .v-tab:hover::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: #e0e0e0;
  z-index: 0;
  border-radius: 4px;
  pointer-events: none;
}
.v-tabs .v-tab .v-btn__content,
.v-tabs .v-tab .v-icon,
.v-tabs .v-tab span,
.v-tabs .v-tab label {
  position: relative;
  z-index: 1;
}
.v-tabs .v-tab:hover .v-btn__content,
.v-tabs .v-tab:hover .v-icon,
.v-tabs .v-tab:hover span,
.v-tabs .v-tab:hover label {
  color: #1a1a1a !important;
}
.v-tabs .v-tab:hover .v-btn__overlay {
  opacity: 0 !important;
}
</style>
