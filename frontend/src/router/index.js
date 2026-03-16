import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import TestList from '../views/TestList.vue'
import TestCreate from '../views/TestCreate.vue'
import TestEdit from '../views/TestEdit.vue'
import RunTest from '../views/RunTest.vue'
import RunList from '../views/RunList.vue'
import RunDetail from '../views/RunDetail.vue'
import RunResult from '../views/RunResult.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/tests', name: 'tests', component: TestList },
  { path: '/tests/new', name: 'test-create', component: TestCreate },
  { path: '/tests/:id/edit', name: 'test-edit', component: TestEdit },
  { path: '/tests/:id/run', name: 'run-test', component: RunTest },
  { path: '/runs', name: 'runs', component: RunList },
  { path: '/runs/:id', name: 'run-detail', component: RunDetail },
  { path: '/runs/:id/result', name: 'run-result', component: RunResult },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
