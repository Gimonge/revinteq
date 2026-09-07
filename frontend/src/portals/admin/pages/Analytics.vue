<template>
  <div style="display:flex;flex-direction:column;gap:20px" class="fade-up">
    <div class="rv-page-header">
      <div>
        <div class="rv-page-title">Cross-Client Analytics</div>
        <div class="rv-page-sub">Revenue intelligence across all tenants — this month</div>
      </div>
    </div>

    <!-- Summary KPIs -->
    <div class="rv-stat-grid">
      <div class="rv-sc card-reveal">
        <div class="rv-sc-label">Total Revenue (All)</div>
        <div class="rv-sc-value">{{ fmt(totals.revenue) }}</div>
        <div class="rv-sc-sub">All clients this month</div>
      </div>
      <div class="rv-sc b card-reveal" style="animation-delay:.05s">
        <div class="rv-sc-label">Total Ad Spend</div>
        <div class="rv-sc-value">{{ fmt(totals.spend) }}</div>
        <div class="rv-sc-sub">Facebook + Instagram</div>
      </div>
      <div class="rv-sc a card-reveal" style="animation-delay:.1s">
        <div class="rv-sc-label">Combined ROI</div>
        <div class="rv-sc-value">{{ totals.roi }}%</div>
        <div class="rv-sc-sub">Blended across all clients</div>
      </div>
      <div class="rv-sc p card-reveal" style="animation-delay:.15s">
        <div class="rv-sc-label">Total Goals Set</div>
        <div class="rv-sc-value">{{ totals.withGoal }}</div>
        <div class="rv-sc-sub">{{ totals.onTrack }} on track or ahead</div>
      </div>
    </div>

    <!-- Performance table with goals -->
    <div class="rv-card card-reveal">
      <div class="rv-ch"><div class="rv-ct">Performance by Client — This Month</div></div>
      <div v-if="loading" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else class="rv-tw">
        <table class="rv-table">
          <thead><tr>
            <th>Client</th>
            <th>Revenue</th>
            <th>Monthly Goal</th>
            <th>Goal Progress</th>
            <th>Goal Status</th>
            <th>Sales</th>
            <th>AOV</th>
            <th>Conv. Rate</th>
            <th>Open Pipeline</th>
          </tr></thead>
          <tbody>
            <tr v-for="t in sortedClients" :key="t.id">
              <td><strong>{{ t.name }}</strong></td>
              <td><strong>{{ fmt(t.monthly_revenue||0) }}</strong></td>
              <td style="color:var(--slate-mid)">{{ t.monthly_goal ? fmt(t.monthly_goal) : '—' }}</td>
              <td>
                <div v-if="t.monthly_goal" style="display:flex;align-items:center;gap:7px;min-width:110px">
                  <div style="flex:1;background:var(--bg);border-radius:4px;height:7px;overflow:hidden;border:1px solid var(--border)">
                    <div :style="{
                      width: Math.min(t.goal_progress||0,100)+'%',
                      height:'100%', borderRadius:'4px',
                      background: goalBarColor(t.goal_status)
                    }"></div>
                  </div>
                  <span style="font-size:11px;font-weight:800;min-width:30px"
                    :style="{color:goalColor(t.goal_status)}">
                    {{ t.goal_progress||0 }}%
                  </span>
                </div>
                <span v-else style="color:var(--slate-light);font-size:12px">—</span>
              </td>
              <td>
                <span v-if="t.monthly_goal" class="rv-badge" :class="goalBadge(t.goal_status)" style="font-size:10px">
                  {{ goalLabel(t.goal_status) }}
                </span>
                <span v-else style="color:var(--slate-light);font-size:11px;font-weight:600">No goal</span>
              </td>
              <td>{{ t.sales_count||0 }}</td>
              <td>{{ fmt(t.aov||0) }}</td>
              <td>{{ t.conv_rate||0 }}%</td>
              <td>{{ t.open_deals||0 }}</td>
            </tr>
            <tr v-if="clients.length===0">
              <td colspan="9" style="text-align:center;color:var(--slate-light);padding:32px">No data yet</td>
            </tr>
          </tbody>
          <!-- Totals footer -->
          <tfoot v-if="clients.length > 1">
            <tr>
              <td><strong>TOTAL / AVG</strong></td>
              <td><strong>{{ fmt(totals.revenue) }}</strong></td>
              <td><strong>{{ fmt(totals.totalGoal) }}</strong></td>
              <td>
                <div style="display:flex;align-items:center;gap:7px;min-width:110px">
                  <div style="flex:1;background:rgba(255,255,255,.3);border-radius:4px;height:7px;overflow:hidden">
                    <div :style="{width:Math.min(totals.avgProgress,100)+'%',height:'100%',borderRadius:'4px',background:'rgba(255,255,255,.8)'}"></div>
                  </div>
                  <span style="font-size:11px;font-weight:800">{{ totals.avgProgress }}%</span>
                </div>
              </td>
              <td></td>
              <td><strong>{{ totals.sales }}</strong></td>
              <td></td>
              <td></td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- Goal achievement visual -->
    <div class="rv-card card-reveal" style="animation-delay:.1s">
      <div class="rv-ch"><div class="rv-ct">Goal Achievement — All Clients</div></div>
      <div class="rv-cb">
        <div v-if="clientsWithGoal.length===0" style="color:var(--slate-light);font-size:13px;font-weight:600;text-align:center;padding:20px">
          No clients have set a goal this month yet.
        </div>
        <div v-for="t in clientsWithGoal" :key="t.id" style="margin-bottom:16px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-size:13px;font-weight:800;color:var(--slate)">{{ t.name }}</span>
              <span class="rv-badge" :class="goalBadge(t.goal_status)" style="font-size:10px">{{ goalLabel(t.goal_status) }}</span>
            </div>
            <span style="font-size:12px;font-weight:700;color:var(--slate-mid)">
              {{ fmt(t.monthly_revenue||0) }} / {{ fmt(t.monthly_goal) }}
            </span>
          </div>
          <div style="background:var(--bg);border-radius:6px;height:12px;overflow:hidden;border:1px solid var(--border);position:relative">
            <!-- Goal line at 100% -->
            <div style="position:absolute;right:0;top:0;bottom:0;width:2px;background:var(--amber);z-index:2"></div>
            <div :style="{
              width: Math.min((t.goal_progress||0),100)+'%',
              height:'100%', borderRadius:'6px',
              background: goalBarColor(t.goal_status),
              transition:'width .8s cubic-bezier(.4,0,.2,1)'
            }"></div>
          </div>
          <div style="display:flex;justify-content:space-between;margin-top:3px">
            <span style="font-size:10px;color:var(--slate-light);font-weight:600">KES 0</span>
            <span style="font-size:10px;color:var(--amber);font-weight:700">Goal: {{ fmt(t.monthly_goal) }}</span>
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

const clients = ref([])
const loading = ref(true)

const sortedClients = computed(() =>
  [...clients.value].sort((a,b)=>(b.monthly_revenue||0)-(a.monthly_revenue||0))
)
const clientsWithGoal = computed(() =>
  clients.value.filter(t => t.monthly_goal)
    .sort((a,b)=>(b.goal_progress||0)-(a.goal_progress||0))
)

const totals = computed(() => {
  const withGoal = clients.value.filter(t => t.monthly_goal)
  return {
    revenue:     clients.value.reduce((s,t)=>s+(t.monthly_revenue||0),0),
    spend:       clients.value.reduce((s,t)=>s+(t.ad_spend||0),0),
    sales:       clients.value.reduce((s,t)=>s+(t.sales_count||0),0),
    totalGoal:   withGoal.reduce((s,t)=>s+(t.monthly_goal||0),0),
    roi:         clients.value.length ? Math.round(clients.value.reduce((s,t)=>s+(t.roi||0),0)/clients.value.length) : 0,
    withGoal:    withGoal.length,
    onTrack:     withGoal.filter(t=>t.goal_status==='ahead'||t.goal_status==='on_track').length,
    avgProgress: withGoal.length ? Math.round(withGoal.reduce((s,t)=>s+(t.goal_progress||0),0)/withGoal.length) : 0,
  }
})

function goalBadge(s)   { return {'ahead':'rv-bg','on_track':'rv-bb','behind':'rv-ba','no_goal':'rv-bgy'}[s]||'rv-bgy' }
function goalLabel(s)   { return {'ahead':'🚀 Ahead','on_track':'✅ On Track','behind':'⚠️ Behind','no_goal':'No Goal'}[s]||'—' }
function goalColor(s)   { return {'ahead':'var(--green)','on_track':'var(--blue)','behind':'var(--amber)'}[s]||'var(--slate-light)' }
function goalBarColor(s){ return {'ahead':'var(--green)','on_track':'var(--blue)','behind':'var(--amber)','no_goal':'var(--border-mid)'}[s]||'var(--border-mid)' }
function fmt(v) { return _fmtK(v) }

async function loadData() {
  loading.value = true
  try { const r = await api.get('/tenants/'); clients.value = r.data.results || r.data || [] } catch(e) {}
  loading.value = false
}
useAutoRefresh(loadData, 60000)
</script>
