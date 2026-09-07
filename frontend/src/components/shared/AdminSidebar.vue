<template>
  <nav class="rv-sidebar">
    <!-- Mobile close button -->
    <div v-if="isMobile" style="display:flex;justify-content:flex-end;padding:12px 14px 0">
      <button @click="$emit('close')" style="background:none;border:none;color:rgba(255,255,255,.5);font-size:20px;cursor:pointer;padding:4px">✕</button>
    </div>

    <div class="rv-sb-logo">
      <div class="rv-logo-mark">
        <span>Revinteq</span>
        <span class="rv-admin-badge">Admin</span>
      </div>
      <div class="rv-logo-sub">Gimsc Solutions Ltd — Nakuru</div>
    </div>

    <div class="rv-sb-section">Overview</div>
    <div class="rv-nav-item" :class="{active:page==='overview'}" @click="nav('overview')">
      <span class="rv-nav-icon">🏠</span> Dashboard
    </div>
    <div class="rv-nav-item" :class="{active:page==='clients'}" @click="nav('clients')">
      <span class="rv-nav-icon">🏢</span> All Clients
      <span class="rv-nav-badge">{{ tenantCount }}</span>
    </div>

    <div class="rv-sb-section">Client Management</div>
    <div class="rv-nav-item" :class="{active:page==='add-client'}" @click="nav('add-client')">
      <span class="rv-nav-icon">➕</span> Add New Client
    </div>

    <div class="rv-sb-section">Configuration</div>
    <div class="rv-nav-item" :class="{active:page==='mpesa'}" @click="nav('mpesa')">
      <span class="rv-nav-icon">💚</span> M-Pesa Setup
    </div>
    <div class="rv-nav-item" :class="{active:page==='sms'}" @click="nav('sms')">
      <span class="rv-nav-icon">📱</span> SMS Setup
    </div>
    <div class="rv-nav-item" :class="{active:page==='api-keys'}" @click="nav('api-keys')">
      <span class="rv-nav-icon">🔑</span> API Keys
    </div>

    <div class="rv-sb-section">Intelligence</div>
    <div class="rv-nav-item" :class="{active:page==='analytics'}" @click="nav('analytics')">
      <span class="rv-nav-icon">📊</span> Cross-Client Analytics
    </div>
    <div class="rv-nav-item" :class="{active:page==='recommendations'}" @click="nav('recommendations')">
      <span class="rv-nav-icon">💡</span> All Recommendations
      <span v-if="recCount>0" class="rv-nav-badge alert">{{ recCount }}</span>
    </div>

    <div class="rv-sb-footer">
      <div class="rv-user-row">
        <div class="rv-avatar">{{ initials }}</div>
        <div style="min-width:0">
          <div class="rv-user-name">{{ user?.email || 'Admin' }}</div>
          <div class="rv-user-role">Super Admin</div>
        </div>
        <button @click="$emit('logout')" style="margin-left:auto;background:none;border:none;color:rgba(255,255,255,.35);cursor:pointer;font-size:16px" title="Logout">🚪</button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
const props = defineProps({
  page: String, user: Object,
  tenantCount: { type: Number, default: 0 },
  recCount:    { type: Number, default: 0 },
})
const emit = defineEmits(['nav', 'logout', 'close'])

const isMobile = ref(false)
function checkMobile() { isMobile.value = window.innerWidth < 768 }
onMounted(() => { checkMobile(); window.addEventListener('resize', checkMobile) })
onUnmounted(() => window.removeEventListener('resize', checkMobile))

const initials = computed(() => props.user?.email?.[0]?.toUpperCase() || 'G')

function nav(page) {
  emit('nav', page)
  if (isMobile.value) emit('close')
}
</script>
