<template>
  <div v-if="!auth.isLoggedIn" style="background:var(--bg-client)">
    <ClientLogin @success="onLoginSuccess" />
  </div>
  <div v-else style="display:flex;background:var(--bg-client);min-height:100vh">

    <!-- Mobile overlay -->
    <div class="rv-mob-overlay" :class="{show: sidebarOpen}" @click="sidebarOpen=false"></div>

    <AppSidebar
      :page="page"
      :user="auth.user"
      :tenant="auth.tenant"
      :class="{'rv-mob-nav-open': sidebarOpen}"
      @nav="navigate"
      @logout="handleLogout"
      @close="sidebarOpen=false"
    />

    <div class="rv-main">
      <div class="rv-topbar">
        <!-- Hamburger (mobile only) -->
        <button class="rv-burger" @click="sidebarOpen=!sidebarOpen" aria-label="Menu">
          <span></span><span></span><span></span>
        </button>
        <div class="rv-topbar-title">{{ pageTitle }}</div>
        <div class="rv-topbar-right">
          <span class="rv-badge rv-bg">{{ auth.tenant?.currency || 'KES' }}</span>
          <button class="rv-btn rv-btn-s rv-btn-sm" @click="handleLogout"><i class="ti ti-logout" aria-hidden="true"></i> Logout</button>
        </div>
      </div>
      <div class="rv-scroll">
        <Dashboard    v-if="page==='dashboard'"  @nav="navigate" @toast="showToast" />
        <Analytics    v-if="page==='analytics'"  @nav="navigate" @toast="showToast" />
        <Pipeline     v-if="page==='pipeline'"   @nav="navigate" @toast="showToast" />
        <LogSale      v-if="page==='log'"         @nav="navigate" @toast="showToast" />
        <SalesHistory v-if="page==='history'"    @nav="navigate" @toast="showToast" />
        <BulkUpload   v-if="page==='bulk'"        @nav="navigate" @toast="showToast" />
        <FacebookAds  v-if="page==='facebook'"   @nav="navigate" @toast="showToast" />
        <InstagramAds v-if="page==='instagram'"  @nav="navigate" @toast="showToast" />
        <RevenueGoals v-if="page==='goals'"       @nav="navigate" @toast="showToast" />
        <SMS          v-if="page==='sms'"          @nav="navigate" @toast="showToast" />
        <Customers    v-if="page==='customers'"  @nav="navigate" @toast="showToast" />
        <Settings     v-if="page==='settings'"   @nav="navigate" @toast="showToast" />
      </div>
    </div>
    <div v-if="toast.show" class="rv-toast" :class="toast.type"><i :class="['ti', toast.icon]" aria-hidden="true"></i> {{ toast.msg }}</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppSidebar   from '@/components/shared/AppSidebar.vue'
import ClientLogin  from './pages/Login.vue'
import Dashboard    from './pages/Dashboard.vue'
import Analytics    from './pages/Analytics.vue'
import Pipeline     from './pages/Pipeline.vue'
import LogSale      from './pages/LogSale.vue'
import SalesHistory from './pages/SalesHistory.vue'
import BulkUpload   from './pages/BulkUpload.vue'
import FacebookAds  from './pages/FacebookAds.vue'
import InstagramAds from './pages/InstagramAds.vue'
import RevenueGoals from './pages/RevenueGoals.vue'
import SMS          from './pages/SMS.vue'
import Customers    from './pages/Customers.vue'
import Settings     from './pages/Settings.vue'

const auth        = useAuthStore()
const page        = ref('dashboard')
const sidebarOpen = ref(false)
const toast       = ref({ show:false, msg:'', type:'green', icon:'ti-circle-check' })
let toastTimer

const PAGE_TITLES = {
  dashboard:'Dashboard', analytics:'Analytics', pipeline:'Sales Pipeline',
  log:'Log a Sale', history:'Sales History', bulk:'Bulk Upload',
  facebook:'Facebook Ads', instagram:'Instagram Ads',
  goals:'Revenue Goals', sms:'SMS', customers:'Customers', settings:'Settings',
}
const pageTitle = computed(() => PAGE_TITLES[page.value] || '')

function navigate(p) { page.value = p; sidebarOpen.value = false }

function handleLogout() { auth.logout(); window.location.reload() }

function onLoginSuccess() {
  if (auth.user?.role === 'SUPER_ADMIN' || auth.user?.role === 'ADMIN') {
    window.location.href = '/admin'
  }
}

function showToast(msg, type='green') {
  clearTimeout(toastTimer)
  toast.value = { show:true, msg, type, icon: type==='green'?'ti-circle-check':type==='red'?'ti-circle-x':'ti-info-circle' }
  toastTimer = setTimeout(() => { toast.value.show = false }, 3200)
}
</script>
