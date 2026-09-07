<template>
  <div style="display:flex;flex-direction:column;gap:18px">
    <!-- Header -->
    <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:10px" class="fade-up">
      <div>
        <div style="font-size:21px;font-weight:900;letter-spacing:-.4px">Instagram Ads</div>
        <div style="font-size:13px;color:var(--slate-light);font-weight:600;margin-top:3px;display:flex;align-items:center;gap:6px">
          <span v-if="syncing" class="rv-spin" style="width:10px;height:10px;border-width:1.5px"></span>
          <span v-else style="width:8px;height:8px;border-radius:50%;background:var(--green);display:inline-block;animation:pulse 2s infinite"></span>
          {{ syncStatus }}
        </div>
      </div>
      <div style="display:flex;gap:8px">
        <button class="rv-btn rv-btn-s rv-btn-sm" @click="syncNow(true)" :disabled="syncing">
          <span v-if="syncing" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
          <span v-else>↻ Force Sync</span>
        </button>
        <button v-if="!connected" @click="connectInstagram" :disabled="connecting"
  style="background:linear-gradient(135deg,var(--ig1),var(--ig2));color:#fff;border:none;padding:6px 13px;border-radius:var(--r-md);font-size:12px;font-weight:800;cursor:pointer;display:inline-flex;align-items:center;gap:6px">
  <span v-if="connecting" class="rv-spin" style="width:12px;height:12px;border-width:2px;border-color:rgba(255,255,255,.3);border-top-color:#fff"></span>
  <span v-else>📸 Connect Instagram</span>
</button>
        <button v-else disabled
  style="background:var(--green);color:#fff;border:none;padding:6px 13px;border-radius:var(--r-md);font-size:12px;font-weight:800;opacity:.7;cursor:default;display:inline-flex;align-items:center;gap:6px">
  ✅ Instagram Connected
</button>
      </div>
    </div>

    <div v-if="!connected" class="rv-al rv-al-b card-reveal">
      📘 Connect your Instagram Ads account to see performance data here. Click "Connect Facebook" to get started.
    </div>

    <template v-if="connected">
      <!-- Summary KPIs -->
      <div class="rv-stat-grid fade-up">
        <div class="rv-sc card-reveal" style="animation-delay:.05s">
          <div class="rv-sc-label">Total Spend</div>
          <div class="rv-sc-value">{{ fmtK(totals.spend) }}</div>
          <div class="rv-sc-sub">This month</div>
        </div>
        <div class="rv-sc b card-reveal" style="animation-delay:.1s">
          <div class="rv-sc-label">Revenue Attributed</div>
          <div class="rv-sc-value">{{ fmtK(totals.revenue) }}</div>
          <div class="rv-sc-sub">Instagram platform sales</div>
        </div>
        <div class="rv-sc a card-reveal" style="animation-delay:.15s">
          <div class="rv-sc-label">ROI</div>
          <div class="rv-sc-value" :style="{color:roiColor(totals.roi)}">{{ totals.roi }}%</div>
          <div class="rv-sc-sub">Return on ad spend</div>
        </div>
        <div class="rv-sc p card-reveal" style="animation-delay:.2s">
          <div class="rv-sc-label">DM Conversations</div>
          <div class="rv-sc-value">{{ totals.conversations }}</div>
          <div class="rv-sc-sub">Conversations started</div>
        </div>
      </div>

      <!-- Full metrics strip: CTR, CPM, CPR, Frequency, Impressions, Clicks, AOV -->
      <div class="rv-aov card-reveal" style="animation-delay:.25s">
        <div class="rv-aov-cell">
          <div class="rv-aov-label" title="Click-Through Rate — clicks ÷ impressions">CTR ℹ</div>
          <div class="rv-aov-value" :style="{color:ctrColor(totals.ctr)}">{{ totals.ctr }}%</div>
        </div>
        <div class="rv-aov-cell">
          <div class="rv-aov-label" title="Cost per 1,000 impressions">CPM ℹ</div>
          <div class="rv-aov-value">{{ fmtK(totals.cpm) }}</div>
        </div>
        <div class="rv-aov-cell">
          <div class="rv-aov-label" title="Cost per DM conversation started">CPR ℹ</div>
          <div class="rv-aov-value" :style="{color:cprColor(totals.cpr,totals.aov)}">{{ fmtK(totals.cpr) }}</div>
        </div>
        <div class="rv-aov-cell">
          <div class="rv-aov-label">Impressions</div>
          <div class="rv-aov-value">{{ fmtNum(totals.impressions) }}</div>
        </div>
        <div class="rv-aov-cell">
          <div class="rv-aov-label">Clicks</div>
          <div class="rv-aov-value">{{ fmtNum(totals.clicks) }}</div>
        </div>
        <div class="rv-aov-cell">
          <div class="rv-aov-label">AOV</div>
          <div class="rv-aov-value">{{ fmtK(totals.aov) }}</div>
        </div>
      </div>

      <!-- Campaign table with expandable ad rows -->
      <div class="rv-card card-reveal" style="animation-delay:.3s">
        <div class="rv-ch">
          <div>
            <div class="rv-ct">Campaign Performance — Instagram</div>
            <div class="rv-cst">{{ campaigns.length }} campaigns · synced {{ lastSyncLabel }} · click a row to see ad breakdown</div>
          </div>
        </div>
        <div v-if="loading" style="padding:32px;text-align:center"><span class="rv-spin"></span></div>
        <div v-else class="rv-tw">
          <table class="rv-table">
            <thead><tr>
              <th></th>
              <th>Campaign</th>
              <th>Status</th>
              <th>Spend</th>
              <th>Impressions</th>
              <th title="Click-Through Rate">CTR</th>
              <th title="Cost per 1,000 impressions">CPM</th>
              <th>DMs</th>
              <th title="Cost Per Result — cost per DM conversation">CPR</th>
              <th>Revenue</th>
              <th>ROI</th>
            </tr></thead>
            <tbody>
              <template v-for="c in campaigns" :key="c.id">
                <!-- Campaign row -->
                <tr @click="toggleExpand(c.id)" style="cursor:pointer" :style="{background: expanded[c.id]?'var(--green-light)':''}">
                  <td style="width:28px;text-align:center;font-size:12px;color:var(--slate-light)">
                    {{ expanded[c.id] ? '▼' : '▶' }}
                  </td>
                  <td><strong>{{ c.name }}</strong></td>
                  <td><span class="rv-badge" :class="c.status==='ACTIVE'?'rv-bg':'rv-bgy'">{{ c.status }}</span></td>
                  <td>{{ fmtK(c.spend||0) }}</td>
                  <td>{{ fmtNum(c.impressions||0) }}</td>
                  <td>
                    <span :style="{color:ctrColor(c.ctr),fontWeight:800}">{{ c.ctr||0 }}%</span>
                    <div style="font-size:10px;color:var(--slate-light)">{{ ctrLabel(c.ctr) }}</div>
                  </td>
                  <td>{{ fmtK(c.cpm||0) }}</td>
                  <td><strong>{{ c.conversations||0 }}</strong></td>
                  <td>
                    <span :style="{color:cprColor(c.cpr,c.aov),fontWeight:700}">{{ fmtK(c.cpr||0) }}</span>
                    <div style="font-size:10px;color:var(--slate-light)">{{ cprLabel(c.cpr, c.aov) }}</div>
                  </td>
                  <td><strong>{{ fmtK(c.revenue||0) }}</strong></td>
                  <td>
                    <strong :style="{color:roiColor(c.roi)}">{{ c.roi||0 }}%</strong>
                  </td>
                </tr>
                <!-- Expanded ad breakdown -->
                <tr v-if="expanded[c.id]" :key="c.id+'_exp'">
                  <td colspan="11" style="padding:0;background:var(--bg)">
                    <div style="padding:16px">
                      <div style="font-size:11px;font-weight:900;color:var(--green);text-transform:uppercase;letter-spacing:.8px;margin-bottom:10px">
                        Ad Breakdown — {{ c.name }}
                      </div>
                      <div v-if="!adDetails[c.id]" style="text-align:center;padding:12px">
                        <span class="rv-spin" style="width:16px;height:16px"></span>
                      </div>
                      <table v-else class="rv-table" style="font-size:12px">
                        <thead><tr>
                          <th>Ad Name</th><th>Format</th><th>Status</th>
                          <th>Spend</th><th>Impressions</th><th>CTR</th>
                          <th>CPM</th><th>DMs</th><th>CPR</th>
                        </tr></thead>
                        <tbody>
                          <tr v-for="ad in adDetails[c.id]" :key="ad.id">
                            <td>{{ ad.name }}</td>
                            <td><span class="rv-badge rv-bgy" style="font-size:10px">{{ ad.ad_format||'—' }}</span></td>
                            <td><span class="rv-badge" :class="ad.status==='ACTIVE'?'rv-bg':'rv-bgy'" style="font-size:10px">{{ ad.status }}</span></td>
                            <td>{{ fmtK(adSpend(ad)) }}</td>
                            <td>{{ fmtNum(adImpressions(ad)) }}</td>
                            <td :style="{color:ctrColor(adCtr(ad)),fontWeight:800}">{{ adCtr(ad) }}%</td>
                            <td>{{ fmtK(adCpm(ad)) }}</td>
                            <td>{{ adConversations(ad) }}</td>
                            <td :style="{color:cprColor(adCpr(ad),c.aov),fontWeight:700}">{{ fmtK(adCpr(ad)) }}</td>
                          </tr>
                          <tr v-if="!adDetails[c.id].length">
                            <td colspan="9" style="text-align:center;color:var(--slate-light);padding:16px">No ad data available</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="campaigns.length===0">
                <td colspan="11" style="text-align:center;color:var(--slate-light);padding:32px">
                  No campaign data — syncing from Meta...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Metric definitions reference card -->
      <div class="rv-card card-reveal" style="animation-delay:.35s">
        <div class="rv-ch"><div class="rv-ct">Metric Definitions</div></div>
        <div class="rv-cb">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div v-for="m in metricDefs" :key="m.key" style="display:flex;gap:10px;align-items:flex-start">
              <div style="width:40px;height:40px;border-radius:var(--r-md);background:var(--bg);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0">{{ m.icon }}</div>
              <div>
                <div style="font-size:12.5px;font-weight:900;color:var(--slate)">{{ m.name }}</div>
                <div style="font-size:11.5px;color:var(--slate-mid);font-weight:600;line-height:1.4">{{ m.def }}</div>
                <div style="font-size:11px;color:var(--green);font-weight:700;margin-top:2px">{{ m.benchmark }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'
import { fmtK as _fmtK, fmtFull, fmtNum } from '@/utils/format'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

const emit = defineEmits(['toast'])
const auth = useAuthStore()
const campaigns   = ref([])
const loading     = ref(true)
const syncing     = ref(false)
const lastSynced  = ref(null)
const syncMessage = ref('')
const expanded    = reactive({})
const adDetails   = reactive({})

const connected = computed(() => {
  return auth.tenant?.meta_ig_connected === true
})
const currency  = computed(() => auth.tenant?.currency || 'KES')
const lastSyncLabel = computed(() => lastSynced.value ? dayjs(lastSynced.value).format('D MMM h:mm A') : 'never')
const syncStatus = computed(() => {
  if (syncing.value)    return 'Syncing from Meta...'
  if (syncMessage.value) return syncMessage.value
  return lastSynced.value ? `Live · synced ${lastSyncLabel.value}` : 'Auto-sync on page load'
})

const totals = computed(() => {
  const spend         = campaigns.value.reduce((s,c)=>s+(c.spend||0),0)
  const impressions   = campaigns.value.reduce((s,c)=>s+(c.impressions||0),0)
  const clicks        = campaigns.value.reduce((s,c)=>s+(c.clicks||0),0)
  const conversations = campaigns.value.reduce((s,c)=>s+(c.conversations||0),0)
  const revenue       = campaigns.value.reduce((s,c)=>s+(c.revenue||0),0)
  const aov           = campaigns.value.length ? campaigns.value.reduce((s,c)=>s+(c.aov||0),0)/campaigns.value.length : 0
  return {
    spend, impressions, clicks, conversations, revenue, aov,
    ctr: impressions   ? round2((clicks/impressions)*100)        : 0,
    cpm: impressions   ? round2((spend/impressions)*1000)        : 0,
    cpr: conversations ? round2(spend/conversations)             : 0,
    roi: spend         ? Math.round(((revenue-spend)/spend)*100) : 0,
  }
})

const metricDefs = [
  { key:'ctr', icon:'👆', name:'CTR — Click-Through Rate',    def:'Percentage of people who saw your ad and clicked the message button. Outbound clicks ÷ impressions × 100.', benchmark:'Benchmark: ≥2% is strong, 1–2% average, <1% needs creative refresh' },
  { key:'cpm', icon:'👁️', name:'CPM — Cost Per 1,000 Impressions', def:'How much you pay to show your ad to 1,000 people. Driven by audience size, competition and time of year.', benchmark:'Lower CPM = cheaper reach. Kenya CPMs are lower than Western markets' },
  { key:'cpr', icon:'💬', name:'CPR — Cost Per Result',        def:'How much you pay for each DM conversation started. Total spend ÷ conversations. Your key cost metric.', benchmark:'Ideal: CPR < 20% of your Average Order Value' },
  { key:'roi', icon:'💰', name:'ROI — Return on Ad Spend',     def:'(Revenue - Spend) ÷ Spend × 100. How much revenue you earned for every KES spent on ads.', benchmark:'Target: ≥150% ROI. Above 300% = scale the budget' },
]

function round2(v) { return Math.round(v * 100) / 100 }
function fmtK(v, cur) {
  return _fmtK(v, cur || auth.tenant?.currency || 'KES')
}
// fmtNum imported from @/utils/format
function ctrColor(ctr)          { return ctr>=2?'var(--green)':ctr>=1?'var(--blue)':'var(--amber)' }
function ctrLabel(ctr)          { return ctr>=2?'Strong':ctr>=1?'Average':'Low — refresh creative' }
function cprColor(cpr, aov)     { if (!cpr||!aov) return 'var(--slate)'; const r=cpr/aov; return r<0.2?'var(--green)':r<0.5?'var(--blue)':'var(--amber)' }
function cprLabel(cpr, aov)     { if (!cpr||!aov) return ''; const r=cpr/aov; return r<0.2?'Efficient':r<0.5?'Moderate':'High cost per DM' }
function roiColor(roi)          { return roi>=150?'var(--green)':roi>=50?'var(--blue)':'var(--amber)' }

// Per-ad computed helpers
function adSpend(ad)        { return ad.spend_records?.reduce((s,r)=>s+parseFloat(r.spend||0),0)||0 }
function adImpressions(ad)  { return ad.spend_records?.reduce((s,r)=>s+(r.impressions||0),0)||0 }
function adClicks(ad)       { return ad.spend_records?.reduce((s,r)=>s+(r.clicks||0),0)||0 }
function adConversations(ad){ return ad.spend_records?.reduce((s,r)=>s+(r.dm_conversations||0),0)||0 }
function adCtr(ad)          { const i=adImpressions(ad),c=adClicks(ad); return i?round2((c/i)*100):0 }
function adCpm(ad)          { const i=adImpressions(ad),s=adSpend(ad);  return i?round2((s/i)*1000):0 }
function adCpr(ad)          { const d=adConversations(ad),s=adSpend(ad); return d?round2(s/d):0 }

async function toggleExpand(campaignId) {
  expanded[campaignId] = !expanded[campaignId]
  if (expanded[campaignId] && !adDetails[campaignId]) {
    try {
      const r = await api.get(`/meta/campaigns/${campaignId}/`)
      adDetails[campaignId] = r.data.ads || []
    } catch(e) {
      adDetails[campaignId] = []
    }
  }
}

const connecting = ref(false)
async function connectInstagram() {
  connecting.value = true
  try {
    const r = await api.get('/meta/auth/')
    if (r.data.oauth_url) {
      window.location.href = r.data.oauth_url
    }
  } catch(e) {
    emit('toast', 'Failed to start Instagram connection', 'red')
  }
  connecting.value = false
}

async function syncNow(force = false) {
  if (!connected.value) return
  syncing.value = true
  syncMessage.value = ''
  try {
    const r = await api.post('/meta/sync/', { force })
    syncMessage.value = r.data.message || 'Synced'
    if (r.data.synced > 0 || force) await loadCampaigns()
    else if (r.data.results?.[0]?.last_synced) lastSynced.value = r.data.results[0].last_synced
  } catch(e) {
    syncMessage.value = 'Sync unavailable — showing cached data'
  }
  syncing.value = false
}

async function loadCampaigns() {
  loading.value = true
  try {
    const r = await api.get('/meta/campaigns/?platform=instagram')
    campaigns.value = r.data.results || r.data || []
    if (campaigns.value[0]?.last_synced) lastSynced.value = campaigns.value[0].last_synced
  } catch(e) {}
  loading.value = false
}

onMounted(async () => {
  await auth.fetchUser()
  const params = new URLSearchParams(window.location.search)
  if (params.get('meta_connected') === '1') {
    window.history.replaceState({}, '', window.location.pathname)
    await auth.fetchUser()
    emit('toast', '✅ Instagram connected successfully! Your ad data is now syncing.', 'green')
  }
  if (params.get('meta_error')) {
    const errMsg = decodeURIComponent(params.get('meta_error'))
    emit('toast', `Instagram connection failed: ${errMsg}`, 'red')
    window.history.replaceState({}, '', window.location.pathname)
  }
})

async function loadData() {
  if (!connected.value) { loading.value = false; return }
  await syncNow(false)
  if (!campaigns.value.length) await loadCampaigns()
}

const { lastUpdated, refreshing } = useAutoRefresh(loadData, 300_000)
</script>
