<template>
  <div v-if="!auth.isLoggedIn || !isAdminUser" style="background:var(--bg)">
    <AdminLogin @success="onLoginSuccess" />
  </div>
  <div v-else style="display:flex;background:var(--bg);min-height:100vh">
    <!-- Mobile overlay -->
    <div class="rv-mob-overlay" :class="{show: sidebarOpen}" @click="sidebarOpen=false"></div>

    <AdminSidebar
      :page="page"
      :user="auth.user"
      :tenant-count="tenantCount"
      :rec-count="recCount"
      :class="{'rv-mob-nav-open': sidebarOpen}"
      @nav="navigate"
      @logout="handleLogout"
      @close="sidebarOpen=false"
    />
    <div class="rv-main">
      <!-- Topbar -->
      <div class="rv-topbar">
        <!-- Hamburger (mobile only) -->
        <button class="rv-burger" @click="sidebarOpen=!sidebarOpen" aria-label="Menu">
          <span></span><span></span><span></span>
        </button>
        <div class="rv-topbar-title">{{ pageTitle }}</div>
        <div class="rv-topbar-right" style="display:flex;align-items:center;gap:12px">

          <!-- Client switcher -->
          <div v-if="tenants.length" style="position:relative">
            <select
              v-model="selectedClientId"
              @change="onClientSwitch"
              class="rv-fs"
              style="font-size:12px;padding:6px 10px;min-width:180px;cursor:pointer"
            >
              <option value="">👤 Switch Client Account</option>
              <option v-for="t in tenants" :key="t.id" :value="t.id">
                {{ t.name }} ({{ t.status }})
              </option>
            </select>
          </div>

          <!-- Impersonation banner -->
          <div v-if="impersonating" style="display:flex;align-items:center;gap:8px;background:var(--amber);color:#000;padding:6px 12px;border-radius:var(--r-md);font-size:12px;font-weight:700">
            👁️ Acting as: <strong>{{ impersonateName }}</strong>
            <button
              @click="stopImpersonate"
              style="background:#000;color:#fff;border:none;border-radius:4px;padding:2px 8px;cursor:pointer;font-size:11px;font-weight:700"
            >✕ Exit</button>
          </div>

          <span style="font-size:13px;font-weight:700;color:var(--slate-mid)">{{ auth.user?.email }}</span>
          <button class="rv-btn rv-btn-s rv-btn-sm" @click="handleLogout">🚪 Logout</button>
        </div>
      </div>

      <!-- Pages -->
      <div class="rv-scroll">
        <Overview        v-if="page==='overview'"        @nav="navigate" @open-client="openClient" @impersonate="startImpersonate" @toast="showToast" />
        <Clients         v-if="page==='clients'"         @nav="navigate" @open-client="openClient" @impersonate="startImpersonate" />
        <AddClient       v-if="page==='add-client'"      @nav="navigate" @toast="showToast" />
        <ClientDetail    v-if="page==='client-detail'"   :tenant="selectedTenant" @nav="navigate" @impersonate="startImpersonate" @toast="showToast" />
        <MpesaSetup      v-if="page==='mpesa'"           @nav="navigate" @open-client="openClient" @toast="showToast" />
        <SmsSetup        v-if="page==='sms'"             @nav="navigate" @open-client="openClient" @toast="showToast" />
        <ApiKeys         v-if="page==='api-keys'"        @nav="navigate" @toast="showToast" />
        <Analytics       v-if="page==='analytics'"       @nav="navigate" />
        <Recommendations v-if="page==='recommendations'" @nav="navigate" />

        <!-- Client portal embedded view when impersonating -->
        <ClientView
          v-if="page==='client-view'"
          :tenant="impersonateTenant"
          @nav="navigate"
          @toast="showToast"
          @exit="stopImpersonate"
        />
      </div>
    </div>
    <div v-if="toast.show" class="rv-toast" :class="toast.type">{{ toast.icon }} {{ toast.msg }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AdminSidebar    from '@/components/shared/AdminSidebar.vue'
import AdminLogin      from './pages/Login.vue'
import Overview        from './pages/Overview.vue'
import Clients         from './pages/Clients.vue'
import AddClient       from './pages/AddClient.vue'
import ClientDetail    from './pages/ClientDetail.vue'
import MpesaSetup      from './pages/MpesaSetup.vue'
import SmsSetup        from './pages/SmsSetup.vue'
import ApiKeys         from './pages/ApiKeys.vue'
import Analytics       from './pages/Analytics.vue'
import Recommendations from './pages/Recommendations.vue'
import ClientView      from './pages/ClientView.vue'
import api, { setImpersonateTenant, clearImpersonateTenant } from '@/api'

const auth = useAuthStore()
const page            = ref('overview')
const selectedTenant  = ref(null)
const tenantCount     = ref(0)
const recCount        = ref(0)
const tenants         = ref([])
const selectedClientId = ref('')
const impersonating   = ref(false)
const impersonateName = ref('')
const impersonateTenant = ref(null)
const sidebarOpen = ref(false)
const toast = ref({ show:false, msg:'', type:'green', icon:'✅' })
let toastTimer

const isAdminUser = computed(() =>
  auth.user?.role === 'SUPER_ADMIN' || auth.user?.role === 'ADMIN' || auth.user?.is_superuser
)

const PAGE_TITLES = {
  overview:'Admin Dashboard', clients:'All Clients', 'add-client':'Add New Client',
  'client-detail':'Client Detail', mpesa:'M-Pesa Setup', sms:'SMS Setup',
  'api-keys':'API Keys', analytics:'Cross-Client Analytics', recommendations:'All Recommendations',
  'client-view': impersonating.value ? `Acting as: ${impersonateName.value}` : 'Client View',
}
const pageTitle = computed(() =>
  page.value === 'client-view'
    ? `Acting as: ${impersonateName.value}`
    : (PAGE_TITLES[page.value] || 'Admin')
)

function navigate(p, tenant=null) {
  page.value = p
  sidebarOpen.value = false
  if (tenant) { selectedTenant.value = tenant }
}
function openClient(t) { selectedTenant.value = t; page.value = 'client-detail' }

async function startImpersonate(t) {
  try {
    // Set header BEFORE the API call so the response also has context
    setImpersonateTenant(t.id)
    await api.post(`/tenants/impersonate/${t.id}/`)
    impersonating.value = true
    impersonateName.value = t.name
    impersonateTenant.value = t
    selectedClientId.value = t.id
    page.value = 'client-view'
    showToast(`Now acting as ${t.name} — you can perform all client actions`, 'green')
  } catch(e) {
    clearImpersonateTenant()
    showToast('Failed to switch to client account', 'red')
  }
}

async function stopImpersonate() {
  try {
    await api.post('/tenants/impersonate/stop/')
  } catch(e) {}
  clearImpersonateTenant()
  impersonating.value = false
  impersonateName.value = ''
  impersonateTenant.value = null
  selectedClientId.value = ''
  page.value = 'overview'
  showToast('Returned to admin view', 'green')
}

async function onClientSwitch() {
  if (!selectedClientId.value) {
    if (impersonating.value) await stopImpersonate()
    return
  }
  const tenant = tenants.value.find(t => t.id === selectedClientId.value)
  if (tenant) await startImpersonate(tenant)
}

function handleLogout() {
  auth.logout()
  window.location.href = '/admin'
}

function onLoginSuccess() { loadCounts() }

function showToast(msg, type='green') {
  clearTimeout(toastTimer)
  toast.value = { show:true, msg, type, icon: type==='green'?'✅':type==='red'?'❌':'ℹ️' }
  toastTimer = setTimeout(() => { toast.value.show = false }, 4000)
}

async function loadCounts() {
  try {
    const r = await api.get('/tenants/')
    const list = r.data.results || r.data || []
    tenants.value = list
    tenantCount.value = list.length
  } catch(e) {}
  try {
    const r = await api.get('/recommendations/?is_dismissed=false')
    recCount.value = (r.data.results || r.data || []).length
  } catch(e) {}
}

onMounted(() => { if (isAdminUser.value) loadCounts() })
</script>
