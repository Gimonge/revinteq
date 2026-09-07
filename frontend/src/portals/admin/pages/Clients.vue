<template>
  <div style="display:flex;flex-direction:column;gap:20px" class="fade-up">
    <div class="rv-page-header">
      <div>
        <div class="rv-page-title">All Clients</div>
        <div class="rv-page-sub">Manage all tenant accounts</div>
      </div>
      <button class="rv-btn rv-btn-p" @click="$emit('nav','add-client')">➕ Add New Client</button>
    </div>

    <div class="rv-card card-reveal">
      <div class="rv-ch">
        <div class="rv-ct">Clients</div>
        <input v-model="search" class="rv-fi" placeholder="🔍  Search clients..." style="width:220px;padding:7px 12px;font-size:12.5px">
      </div>
      <div v-if="loading" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else-if="filtered.length===0" class="rv-empty">
        <div class="rv-empty-icon">🏢</div>
        <div class="rv-empty-title">No clients found</div>
        <div class="rv-empty-sub">{{ search ? 'Try a different search term' : 'Add your first client to get started' }}</div>
      </div>
      <div v-else>
        <div v-for="t in filtered" :key="t.id" class="rv-tenant-row">
          <div class="rv-tenant-init" :style="{background:gradientFor(t.name)}">{{ t.name[0] }}</div>
          <div style="flex:1;min-width:0">
            <div class="rv-tenant-name">{{ t.name }}</div>
            <div class="rv-tenant-meta">{{ t.contact_email||'—' }} &bull; {{ t.currency||'KES' }} &bull; {{ t.location||'—' }}</div>
            <!-- Goal progress bar inline -->
            <div v-if="t.monthly_goal" style="display:flex;align-items:center;gap:8px;margin-top:6px;max-width:320px">
              <div style="flex:1;background:var(--bg);border-radius:4px;height:6px;overflow:hidden;border:1px solid var(--border)">
                <div :style="{
                  width: Math.min(t.goal_progress||0,100)+'%',
                  height:'100%', borderRadius:'4px',
                  background: goalBarColor(t.goal_status)
                }"></div>
              </div>
              <span style="font-size:10.5px;font-weight:800;white-space:nowrap"
                :style="{color:goalColor(t.goal_status)}">
                {{ t.goal_progress||0 }}% — {{ goalLabel(t.goal_status) }}
              </span>
              <span style="font-size:10.5px;color:var(--slate-light);font-weight:600;white-space:nowrap">
                {{ fmt(t.monthly_revenue||0) }} / {{ fmt(t.monthly_goal) }}
              </span>
            </div>
            <div v-else style="margin-top:4px;font-size:10.5px;color:var(--slate-light);font-weight:600">
              No revenue goal set this month
            </div>
          </div>
          <div class="rv-tenant-actions">
            <span class="rv-badge" :class="statusBadge(t.status)">{{ t.status }}</span>
            <button v-if="t.status!=='suspended'" class="rv-btn rv-btn-a rv-btn-xs" @click="$emit('impersonate',t)">👁️ View as client</button>
            <button class="rv-btn rv-btn-s rv-btn-xs" @click="$emit('open-client',t)">Open →</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/api'
import { fmtK as _fmtK, fmtFull, fmtNum } from '@/utils/format'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

defineEmits(['nav','impersonate','open-client'])
const tenants = ref([])
const loading = ref(true)
const search  = ref('')

const GRADS = [
  'linear-gradient(135deg,#1F7A4C,#2563EB)',
  'linear-gradient(135deg,#7C3AED,#DD2A7B)',
  'linear-gradient(135deg,#D97706,#f59e0b)',
  'linear-gradient(135deg,#059669,#34d399)',
  'linear-gradient(135deg,#dc2626,#f97316)',
  'linear-gradient(135deg,#0284c7,#38bdf8)',
]
function gradientFor(name) { return GRADS[name.charCodeAt(0) % GRADS.length] }
function statusBadge(s) { return {'active':'rv-bg','trial':'rv-bb','suspended':'rv-ba','inactive':'rv-bgy'}[s]||'rv-bgy' }
function goalBadge(s)   { return {'ahead':'rv-bg','on_track':'rv-bb','behind':'rv-ba','no_goal':'rv-bgy'}[s]||'rv-bgy' }
function goalLabel(s)   { return {'ahead':'🚀 Ahead','on_track':'✅ On Track','behind':'⚠️ Behind','no_goal':'No Goal'}[s]||'—' }
function goalColor(s)   { return {'ahead':'var(--green)','on_track':'var(--blue)','behind':'var(--amber)'}[s]||'var(--slate-light)' }
function goalBarColor(s){ return {'ahead':'var(--green)','on_track':'var(--blue)','behind':'var(--amber)','no_goal':'var(--border-mid)'}[s]||'var(--border-mid)' }
function fmt(v) { return _fmtK(v) }

const filtered = computed(() => {
  if (!search.value) return tenants.value
  const q = search.value.toLowerCase()
  return tenants.value.filter(t => t.name.toLowerCase().includes(q) || (t.contact_email||'').toLowerCase().includes(q))
})

async function loadData() {
  loading.value = true
  try {
    const r = await api.get('/tenants/')
    tenants.value = r.data.results || r.data || []
  } catch(e) { console.error(e) }
  loading.value = false
}
useAutoRefresh(loadData, 45000)
</script>
