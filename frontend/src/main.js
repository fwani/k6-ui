import './styles/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { initTheme } from './utils/theme'
import '@mdi/font/css/materialdesignicons.css'

initTheme()
createApp(App).use(router).mount('#app')
