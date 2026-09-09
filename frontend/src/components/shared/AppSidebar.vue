<template>
  <nav class="rv-sidebar" :class="{'rv-mob-nav-open': open}">
    <!-- Mobile close button -->
    <div v-if="isMobile" style="display:flex;justify-content:flex-end;padding:12px 14px 0">
      <button @click="$emit('close')" style="background:none;border:none;color:rgba(255,255,255,.5);font-size:20px;cursor:pointer;padding:4px"><i class="ti ti-x" aria-hidden="true"></i></button>
    </div>

    <div class="rv-sb-logo">
      <div class="rv-logo-mark"><span>Revinteq</span></div>
      <div class="rv-logo-tenant">{{ tenant?.name || 'Loading...' }}</div>
    </div>

    <div class="rv-sb-section">Main</div>
    <div class="rv-nav-item" :class="{active:page==='dashboard'}" @click="nav('dashboard')"><span class="rv-nav-icon"><i class="ti ti-home" aria-hidden="true"></i></span>Dashboard</div>
    <div class="rv-nav-item" :class="{active:page==='analytics'}" @click="nav('analytics')"><span class="rv-nav-icon"><i class="ti ti-chart-bar" aria-hidden="true"></i></span>Analytics</div>
    <div class="rv-nav-item" :class="{active:page==='pipeline'}"  @click="nav('pipeline')"><span class="rv-nav-icon"><i class="ti ti-target" aria-hidden="true"></i></span>Sales Pipeline</div>

    <div class="rv-sb-section">Sales</div>
    <div class="rv-nav-item" :class="{active:page==='log'}"     @click="nav('log')"><span class="rv-nav-icon"><i class="ti ti-pencil" aria-hidden="true"></i></span>Log a Sale</div>
    <div class="rv-nav-item" :class="{active:page==='history'}" @click="nav('history')"><span class="rv-nav-icon"><i class="ti ti-clipboard-list" aria-hidden="true"></i></span>Sales History</div>
    <div class="rv-nav-item" :class="{active:page==='bulk'}"    @click="nav('bulk')"><span class="rv-nav-icon"><i class="ti ti-upload" aria-hidden="true"></i></span>Bulk Upload</div>

    <div class="rv-sb-section">Ads</div>
    <div class="rv-nav-item" :class="{active:page==='facebook'}"  @click="nav('facebook')"><span class="rv-nav-icon"><i class="ti ti-brand-facebook" aria-hidden="true"></i></span>Facebook Ads</div>
    <div class="rv-nav-item" :class="{active:page==='instagram'}" @click="nav('instagram')"><span class="rv-nav-icon"><i class="ti ti-brand-instagram" aria-hidden="true"></i></span>Instagram Ads</div>

    <div class="rv-sb-section">Goals &amp; Comms</div>
    <div class="rv-nav-item" :class="{active:page==='goals'}" @click="nav('goals')"><span class="rv-nav-icon"><i class="ti ti-target" aria-hidden="true"></i></span>Revenue Goals</div>
    <div class="rv-nav-item" :class="{active:page==='sms'}"   @click="nav('sms')"><span class="rv-nav-icon"><i class="ti ti-device-mobile" aria-hidden="true"></i></span>SMS</div>

    <div class="rv-sb-section">Account</div>
    <div class="rv-nav-item" :class="{active:page==='settings'}" @click="nav('settings')"><span class="rv-nav-icon"><i class="ti ti-settings" aria-hidden="true"></i></span>Settings</div>

    <div class="rv-sb-section">Customers</div>
    <div class="rv-nav-item" :class="{active:page==='customers'}" @click="nav('customers')"><span class="rv-nav-icon"><i class="ti ti-users" aria-hidden="true"></i></span>Customers</div>

    <div class="rv-sb-footer">
      <div class="rv-user-row">
        <div class="rv-avatar">{{ initials }}</div>
        <div style="min-width:0">
          <div class="rv-user-name" style="font-size:11.5px">{{ user?.email }}</div>
          <div class="rv-user-biz">{{ tenant?.name }}</div>
        </div>
        <button @click="$emit('logout')" style="margin-left:auto;background:none;border:none;color:rgba(255,255,255,.35);cursor:pointer;font-size:16px" title="Logout"><i class="ti ti-logout" aria-hidden="true"></i></button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
const props = defineProps({ page: String, user: Object, tenant: Object })
const emit  = defineEmits(['nav', 'logout', 'close'])

const isMobile = ref(false)
function checkMobile() { isMobile.value = window.innerWidth < 768 }
onMounted(() => { checkMobile(); window.addEventListener('resize', checkMobile) })
onUnmounted(() => window.removeEventListener('resize', checkMobile))

const initials = computed(() => props.user?.email?.[0]?.toUpperCase() || 'C')

function nav(page) {
  emit('nav', page)
  if (isMobile.value) emit('close')
}
</script>
