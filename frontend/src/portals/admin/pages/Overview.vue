<template>
  <div style="display:flex;flex-direction:column;gap:20px" class="fade-up">
    <!-- Header -->
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:4px">
      <span style="display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;color:var(--slate-light)">
        <span v-if="refreshing" class="rv-spin" style="width:10px;height:10px;border-width:1.5px"></span>
        <span v-else style="width:8px;height:8px;border-radius:50%;background:var(--green);display:inline-block;animation:pulse 2s infinite"></span>
        {{ refreshing ? 'Updating...' : lastUpdated ? 'Live · ' + new Date(lastUpdated).toLocaleTimeString() : 'Loading...' }}
      </span>
    </div>
    <div class="rv-page-header">
      <div>
        <div class="rv-page-title">Admin Dashboard</div>
        <div class="rv-page-sub">Cross-client overview — all tenants at a glance</div>
      </div>
      <button class="rv-btn rv-btn-p" @click="$emit('nav','add-client')"><i class="ti ti-plus" aria-hidden="true"></i> Add New Client</button>
    </div>

    <!-- Stat grid -->
    <div class="rv-stat-grid">
      <div class="rv-sc card-reveal" style="animation-delay:.05s">
        <span class="rv-sc-icon"><i class="ti ti-building" aria-hidden="true"></i></span>
        <div class="rv-sc-label">Total Clients</div>
        <div class="rv-sc-value count-up">{{ stats.total }}</div>
        <div class="rv-sc-sub">{{ stats.active }} active &bull; {{ stats.trial }} trial</div>
      </div>
      <div class="rv-sc b card-reveal" style="animation-delay:.1s">
        <span class="rv-sc-icon"><i class="ti ti-currency-dollar" aria-hidden="true"></i></span>
        <div class="rv-sc-label">Monthly Revenue (All)</div>
        <div class="rv-sc-value count-up">{{ fmt(stats.revenue) }}</div>
        <div class="rv-sc-sub">Across all clients this month</div>
      </div>
      <div class="rv-sc a card-reveal" style="animation-delay:.15s">
        <span class="rv-sc-icon"><i class="ti ti-target" aria-hidden="true"></i></span>
        <div class="rv-sc-label">Open Pipeline Deals</div>
        <div class="rv-sc-value count-up">{{ stats.openDeals }}</div>
        <div class="rv-sc-sub">Across all clients</div>
      </div>
      <div class="rv-sc p card-reveal" style="animation-delay:.2s">
        <span class="rv-sc-icon"><i class="ti ti-trophy" aria-hidden="true"></i></span>
        <div class="rv-sc-label">Clients on Track / Ahead</div>
        <div class="rv-sc-value count-up">{{ stats.onTrack }}</div>
        <div class="rv-sc-sub">of {{ stats.withGoal }} clients with goals set</div>
      </div>
    </div>

    <!-- Client Performance table -->
    <div class="rv-card card-reveal" style="animation-delay:.25s">
      <div class="rv-ch">
        <div>
          <div class="rv-ct">Client Performance — This Month</div>
          <div class="rv-cst">Click a row to open client detail</div>
        </div>
        <button class="rv-btn rv-btn-s rv-btn-sm" @click="loadData"><i class="ti ti-refresh" aria-hidden="true"></i> Refresh</button>
      </div>
      <div v-if="loading" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else-if="tenants.length===0" class="rv-empty">
        <div class="rv-empty-icon"><i class="ti ti-building" aria-hidden="true"></i></div>
        <div class="rv-empty-title">No clients yet</div>
        <div class="rv-empty-sub">Add your first client to get started</div>
      </div>
      <div v-else class="rv-tw">
        <table class="rv-table">
          <thead><tr>
            <th>Client</th>
            <th>Status</th>
            <th>Monthly Revenue</th>
            <th>Monthly Goal</th>
            <th>Goal Progress</th>
            <th>Open Deals</th>
            <th>Last Sale</th>
            <th>Actions</th>
          </tr></thead>
          <tbody>
            <tr v-for="t in tenants" :key="t.id" style="cursor:pointer" @click="openClient(t)">
              <td><strong>{{ t.name }}</strong></td>
              <td><span class="rv-badge" :class="statusBadge(t.status)">{{ t.status }}</span></td>
              <td><strong>{{ fmt(t.monthly_revenue||0) }}</strong></td>
              <td style="color:var(--slate-mid)">
                {{ t.monthly_goal ? fmt(t.monthly_goal) : '—' }}
              </td>
              <td>
                <div v-if="t.monthly_goal" style="display:flex;align-items:center;gap:8px;min-width:120px">
                  <div style="flex:1;background:var(--bg);border-radius:4px;height:8px;overflow:hidden;border:1px solid var(--border)">
                    <div :style="{
                      width: Math.min(t.goal_progress||0, 100) + '%',
                      height: '100%',
                      borderRadius: '4px',
                      background: goalBarColor(t.goal_status),
                      transition: 'width .6s ease'
                    }"></div>
                  </div>
                  <span style="font-size:11px;font-weight:800;min-width:36px"
                    :style="{color: goalColor(t.goal_status)}">
                    {{ t.goal_progress||0 }}%
                  </span>
                  <span class="rv-badge" :class="goalBadge(t.goal_status)" style="padding:2px 7px;font-size:10px">
                    {{ goalLabel(t.goal_status) }}
                  </span>
                </div>
                <span v-else style="color:var(--slate-light);font-size:12px;font-weight:600">No goal set</span>
              </td>
              <td>{{ t.open_deals||0 }}</td>
              <td>{{ t.last_sale || '—' }}</td>
              <td style="display:flex;gap:6px;white-space:nowrap" @click.stop>
                <button class="rv-btn rv-btn-s rv-btn-xs" @click="openClient(t)">View</button>
                <button class="rv-btn rv-btn-a rv-btn-xs" @click="$emit('impersonate',t)"><i class="ti ti-eye" aria-hidden="true"></i> Act as</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Revenue + Goal bars -->
    <div class="rv-card card-reveal" style="animation-delay:.3s">
      <div class="rv-ch"><div class="rv-ct">Revenue vs Goal — by Client</div></div>
      <div class="rv-cb">
        <div v-if="tenants.length===0" style="color:var(--slate-light);font-size:13px;font-weight:600">No data yet.</div>
        <div v-for="t in sortedTenants" :key="t.id" style="margin-bottom:14px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:12px;font-weight:800;color:var(--slate)">{{ t.name }}</span>
            <span style="font-size:11px;font-weight:700;color:var(--slate-mid)">
              {{ fmt(t.monthly_revenue||0) }}
              <span v-if="t.monthly_goal" style="color:var(--slate-light)"> / {{ fmt(t.monthly_goal) }}</span>
            </span>
          </div>
          <!-- Revenue bar -->
          <div style="background:var(--bg);border-radius:4px;height:10px;overflow:hidden;border:1px solid var(--border);position:relative">
            <!-- Goal marker -->
            <div v-if="t.monthly_goal && maxRevOrGoal(t) > 0"
              :style="{
                position:'absolute', top:0, bottom:0, width:'2px',
                left: Math.min((t.monthly_goal / maxRevOrGoal(t)) * 100, 100) + '%',
                background:'var(--amber)', zIndex:2
              }"></div>
            <!-- Revenue fill -->
            <div :style="{
              width: maxRevOrGoal(t) > 0 ? Math.min(((t.monthly_revenue||0) / maxRevOrGoal(t)) * 100, 100) + '%' : '0%',
              height:'100%', borderRadius:'4px',
              background: goalBarColor(t.goal_status),
              transition:'width .8s cubic-bezier(.4,0,.2,1)'
            }"></div>
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

const emit = defineEmits(['nav','impersonate','open-client'])
const tenants = ref([])
const loading = ref(true)
const stats   = ref({ total:0, active:0, trial:0, revenue:0, openDeals:0, onTrack:0, withGoal:0 })

async function loadData() {
  loading.value = true
  try {
    const r = await api.get('/tenants/')
    tenants.value = r.data.results || r.data || []
    const withGoal = tenants.value.filter(t => t.monthly_goal)
    stats.value = {
      total:     tenants.value.length,
      active:    tenants.value.filter(t=>t.status==='active').length,
      trial:     0, // trial status removed
      revenue:   tenants.value.reduce((s,t)=>s+(t.monthly_revenue||0),0),
      openDeals: tenants.value.reduce((s,t)=>s+(t.open_deals||0),0),
      withGoal:  withGoal.length,
      onTrack:   withGoal.filter(t=>t.goal_status==='ahead'||t.goal_status==='on_track').length,
    }
  } catch(e) { console.error(e) }
  loading.value = false
}

function openClient(t) { emit('open-client', t) }
function statusBadge(s) { return {'active':'rv-bg','trial':'rv-bb','suspended':'rv-ba','inactive':'rv-bgy'}[s]||'rv-bgy' }
function goalBadge(s)   { return {'ahead':'rv-bg','on_track':'rv-bb','behind':'rv-ba','no_goal':'rv-bgy'}[s]||'rv-bgy' }
function goalLabel(s)   { return {'ahead':'Ahead','on_track':'On Track','behind':'Behind','no_goal':'—'}[s]||'—' }
function goalColor(s)   { return {'ahead':'var(--green)','on_track':'var(--blue)','behind':'var(--amber)','no_goal':'var(--slate-light)'}[s]||'var(--slate-light)' }
function goalBarColor(s){ return {'ahead':'var(--green)','on_track':'var(--blue)','behind':'var(--amber)','no_goal':'var(--border-mid)'}[s]||'var(--border-mid)' }

function fmt(v) { return _fmtK(v) }

const sortedTenants = computed(() => [...tenants.value].sort((a,b)=>(b.monthly_revenue||0)-(a.monthly_revenue||0)))
const maxRev = computed(() => Math.max(...tenants.value.map(t=>t.monthly_revenue||0), 1))
function maxRevOrGoal(t) { return Math.max(t.monthly_revenue||0, t.monthly_goal||0, 1) }
function barWidth(v) { return Math.round((v/maxRev.value)*100) }

const { lastUpdated, refreshing } = useAutoRefresh(loadData, 30000)
</script>
