import { createApp } from 'vue'
import { createPinia } from 'pinia'
import VueApexCharts from 'vue3-apexcharts'
import App from './App.vue'
import './assets/main.css'
import { fmtK, fmtFull, fmtNum, fmtDate, fmtPct } from '@/utils/format'

const app = createApp(App)
app.use(createPinia())
app.use(VueApexCharts)
// Global format helpers available as $fmtK, $fmtFull etc in all templates
app.config.globalProperties.$fmtK    = fmtK
app.config.globalProperties.$fmtFull = fmtFull
app.config.globalProperties.$fmtNum  = fmtNum
app.config.globalProperties.$fmtDate = fmtDate
app.config.globalProperties.$fmtPct  = fmtPct

app.mount('#app')
