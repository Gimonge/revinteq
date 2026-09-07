<template>
  <div style="display:flex;flex-direction:column;gap:20px">
    <div class="rv-page-header">
      <div>
        <div class="rv-page-title">Facebook Ads</div>
        <div class="rv-page-sub">{{ selectedAccount ? selectedAccount.account_name : 'Select an ad account to view campaigns' }}</div>
      </div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <button class="rv-btn rv-btn-s rv-btn-sm" @click="syncNow(true)" :disabled="syncing">
          <span v-if="syncing" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
          <span v-else>↻ Force Sync</span>
        </button>
        <button v-if="!fbConnected" class="rv-btn rv-btn-p rv-btn-sm" @click="connectFacebook" :disabled="connecting">
          <span v-if="connecting" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
          <span v-else>📘 Connect Facebook</span>
        </button>
        <button v-else class="rv-btn rv-btn-s rv-btn-sm" disabled style="opacity:.6;cursor:default;color:var(--green)">✅ Facebook Connected</button>
      </div>
    </div>
    <div v-if="syncMsg" class="rv-al rv-al-g" style="margin:0">{{ syncMsg }}</div>
    <div v-if="!fbConnected" class="rv-card card-reveal">
      <div class="rv-cb" style="text-align:center;padding:48px 20px">
        <div style="font-size:48px;margin-bottom:16px">📘</div>
        <div style="font-size:18px;font-weight:900;margin-bottom:8px">Connect your Facebook Ads account</div>
        <div style="font-size:14px;color:var(--slate-mid);font-weight:600;margin-bottom:24px">See your campaign performance, ad spend, and ROI all in one place.</div>
        <button class="rv-btn rv-btn-p" @click="connectFacebook" :disabled="connecting">
          <span v-if="connecting" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
          <span v-else>📘 Connect Facebook</span>
        </button>
      </div>
    </div>
    <div v-if="fbConnected">
      <div class="rv-card card-reveal" style="margin-bottom:4px">
        <div class="rv-cb" style="padding:14px 20px">
          <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
            <div style="font-size:12px;font-weight:900;color:var(--slate-mid);text-transform:uppercase;letter-spacing:.6px;white-space:nowrap">Ad Account</div>
            <select v-model="selectedAccountId" class="rv-fs" style="flex:1;min-width:200px;max-width:400px;font-size:13px" @change="onAccountChange">
              <option value="">— All Accounts —</option>
              <option v-for="acc in adAccounts" :key="acc.id" :value="acc.id">{{ acc.account_name }} ({{ acc.meta_account_id }})</option>
            </select>
            <div v-if="selectedAccount" style="display:flex;gap:6px;align-items:center">
              <span class="rv-badge rv-bg" style="font-size:10px">{{ selectedAccount.platform }}</span>
              <span style="font-size:11px;color:var(--slate-mid)">{{ selectedAccount.currency }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="rv-card card-reveal" style="margin-bottom:4px">
        <div class="rv-cb" style="padding:12px 20px">
          <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
            <div style="font-size:12px;font-weight:900;color:var(--slate-mid);text-transform:uppercase;letter-spacing:.6px">Filters</div>
            <select v-model="filterStatus" class="rv-fs" style="font-size:12px;padding:5px 10px;min-width:120px">
              <option value="">All Status</option>
              <option value="ACTIVE">Active</option>
              <option value="PAUSED">Paused</option>
              <option value="ARCHIVED">Archived</option>
            </select>
            <select v-model="filterPlatform" class="rv-fs" style="font-size:12px;padding:5px 10px;min-width:120px">
              <option value="">All Platforms</option>
              <option value="facebook">Facebook</option>
              <option value="instagram">Instagram</option>
            </select>
            <select v-model="filterObjective" class="rv-fs" style="font-size:12px;padding:5px 10px;min-width:140px">
              <option value="">All Objectives</option>
              <option v-for="obj in uniqueObjectives" :key="obj" :value="obj">{{ obj }}</option>
            </select>
            <input v-model="searchQuery" class="rv-fi" placeholder="Search campaigns..." style="font-size:12px;padding:5px 10px;min-width:180px;flex:1">
            <button v-if="hasFilters" class="rv-btn rv-btn-s rv-btn-xs" @click="clearFilters">✕ Clear</button>
          </div>
        </div>
      </div>
      <div class="rv-g4" style="margin-bottom:4px">
        <div class="rv-sc card-reveal"><div class="rv-sc-label">Total Spend</div><div class="rv-sc-value">{{ fmtK(totals.spend) }}</div><div class="rv-sc-sub">{{ filteredCampaigns.length }} campaigns</div></div>
        <div class="rv-sc card-reveal b" style="animation-delay:.05s"><div class="rv-sc-label">Impressions</div><div class="rv-sc-value">{{ fmtNum(totals.impressions) }}</div><div class="rv-sc-sub">Avg CTR {{ totals.ctr.toFixed(2) }}%</div></div>
        <div class="rv-sc card-reveal" style="animation-delay:.1s"><div class="rv-sc-label">DM Conversations</div><div class="rv-sc-value">{{ totals.conversations }}</div><div class="rv-sc-sub">CPR {{ fmtK(totals.cpr) }}</div></div>
        <div class="rv-sc card-reveal g" style="animation-delay:.15s"><div class="rv-sc-label">Avg ROI</div><div class="rv-sc-value" :style="{color:roiColor(totals.roi)}">{{ totals.roi.toFixed(1) }}%</div><div class="rv-sc-sub">Revenue {{ fmtK(totals.revenue) }}</div></div>
      </div>
      <div class="rv-card card-reveal">
        <div class="rv-ch">
          <div><div class="rv-ct">Campaign Performance</div><div class="rv-cst">{{ filteredCampaigns.length }} of {{ campaigns.length }} campaigns · {{ lastSyncLabel }} · click row for ad breakdown</div></div>
          <span style="font-size:12px;color:var(--slate-mid)">Page {{ currentPage }} of {{ totalPages }}</span>
        </div>
        <div class="rv-cb" style="padding:0">
          <div v-if="loading" style="padding:48px;text-align:center">
            <span class="rv-spin"></span>
            <div style="margin-top:12px;font-size:13px;color:var(--slate-light);font-weight:600">Loading campaigns...</div>
          </div>
          <div v-else-if="filteredCampaigns.length===0" style="padding:48px;text-align:center;color:var(--slate-light);font-size:14px;font-weight:600">
            {{ campaigns.length ? 'No campaigns match your filters.' : 'No campaigns found. Click Force Sync to fetch latest data.' }}
          </div>
          <div v-else class="rv-tw">
            <table class="rv-table">
              <thead><tr>
                <th style="width:28px"></th>
                <th>Campaign</th><th>Status</th><th>Objective</th>
                <th>Spend</th><th>Impressions</th><th>CTR</th><th>CPM</th>
                <th>DMs</th><th>CPR</th><th>Revenue</th><th>ROI</th>
              </tr></thead>
              <tbody>
                <template v-for="c in paginatedCampaigns" :key="c.id">
                  <tr @click="toggleExpand(c.id)" style="cursor:pointer" :style="{background:expanded[c.id]?'var(--green-light)':''}">
                    <td style="text-align:center;font-size:12px;color:var(--slate-light)">{{ expanded[c.id]?'▼':'▶' }}</td>
                    <td><strong style="font-size:13px">{{ c.name }}</strong></td>
                    <td><span class="rv-badge" :class="c.status==='ACTIVE'?'rv-bg':'rv-bgy'">{{ c.status }}</span></td>
                    <td style="font-size:11px;color:var(--slate-mid)">{{ c.objective||'—' }}</td>
                    <td>{{ fmtK(c.spend||0) }}</td>
                    <td>{{ fmtNum(c.impressions||0) }}</td>
                    <td><span :style="{color:ctrColor(c.ctr),fontWeight:800}">{{ c.ctr||0 }}%</span></td>
                    <td>{{ fmtK(c.cpm||0) }}</td>
                    <td><strong>{{ c.conversations||0 }}</strong></td>
                    <td><span :style="{color:cprColor(c.cpr,c.aov),fontWeight:700}">{{ fmtK(c.cpr||0) }}</span></td>
                    <td><strong>{{ fmtK(c.revenue||0) }}</strong></td>
                    <td><strong :style="{color:roiColor(c.roi)}">{{ c.roi||0 }}%</strong></td>
                  </tr>
                  <tr v-if="expanded[c.id]" :key="c.id+'_exp'">
                    <td colspan="12" style="padding:0;background:var(--bg)">
                      <div style="padding:16px">
                        <div style="font-size:11px;font-weight:900;color:var(--green);text-transform:uppercase;letter-spacing:.8px;margin-bottom:10px">Ad Breakdown — {{ c.name }}</div>
                        <div v-if="adDetails[c.id]===null" style="text-align:center;padding:12px"><span class="rv-spin" style="width:16px;height:16px"></span></div>
                        <table v-else class="rv-table" style="font-size:12px">
                          <thead><tr><th>Ad Name</th><th>Format</th><th>Status</th><th>Spend</th><th>Impressions</th><th>CTR</th><th>CPM</th><th>DMs</th><th>CPR</th></tr></thead>
                          <tbody>
                            <tr v-for="ad in (adDetails[c.id]||[])" :key="ad.id">
                              <td>{{ ad.name }}</td>
                              <td><span class="rv-badge rv-bgy" style="font-size:10px">{{ ad.ad_format||'—' }}</span></td>
                              <td><span class="rv-badge" :class="ad.status==='ACTIVE'?'rv-bg':'rv-bgy'" style="font-size:10px">{{ ad.status }}</span></td>
                              <td>{{ fmtK(ad.spend||0) }}</td>
                              <td>{{ fmtNum(ad.impressions||0) }}</td>
                              <td :style="{color:ctrColor(ad.ctr||0),fontWeight:800}">{{ ad.ctr||0 }}%</td>
                              <td>{{ fmtK(ad.cpm||0) }}</td>
                              <td>{{ ad.conversations||0 }}</td>
                              <td>{{ fmtK(ad.cpr||0) }}</td>
                            </tr>
                            <tr v-if="!(adDetails[c.id]||[]).length"><td colspan="9" style="text-align:center;color:var(--slate-light);padding:16px">No ad data available</td></tr>
                          </tbody>
                        </table>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
              <tfoot>
                <tr style="background:var(--bg);font-weight:900;border-top:2px solid var(--border)">
                  <td></td>
                  <td style="font-size:12px;color:var(--slate-mid)">TOTALS ({{ filteredCampaigns.length }})</td>
                  <td></td><td></td>
                  <td>{{ fmtK(totals.spend) }}</td>
                  <td>{{ fmtNum(totals.impressions) }}</td>
                  <td :style="{color:ctrColor(totals.ctr)}">{{ totals.ctr.toFixed(2) }}%</td>
                  <td>{{ fmtK(totals.cpm) }}</td>
                  <td>{{ totals.conversations }}</td>
                  <td>{{ fmtK(totals.cpr) }}</td>
                  <td>{{ fmtK(totals.revenue) }}</td>
                  <td :style="{color:roiColor(totals.roi)}">{{ totals.roi.toFixed(1) }}%</td>
                </tr>
              </tfoot>
            </table>
          </div>
          <div v-if="totalPages>1" style="display:flex;gap:8px;align-items:center;justify-content:center;padding:16px;border-top:1px solid var(--border)">
            <button class="rv-btn rv-btn-s rv-btn-xs" @click="currentPage=1" :disabled="currentPage===1">««</button>
            <button class="rv-btn rv-btn-s rv-btn-xs" @click="currentPage--" :disabled="currentPage===1">‹</button>
            <template v-for="p in pageRange" :key="p">
              <button class="rv-btn rv-btn-xs" :class="p===currentPage?'rv-btn-p':'rv-btn-s'" @click="currentPage=p">{{ p }}</button>
            </template>
            <button class="rv-btn rv-btn-s rv-btn-xs" @click="currentPage++" :disabled="currentPage===totalPages">›</button>
            <button class="rv-btn rv-btn-s rv-btn-xs" @click="currentPage=totalPages" :disabled="currentPage===totalPages">»»</button>
            <span style="font-size:12px;color:var(--slate-mid);margin-left:8px">{{ (currentPage-1)*pageSize+1 }}–{{ Math.min(currentPage*pageSize,filteredCampaigns.length) }} of {{ filteredCampaigns.length }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showAccountSelect" style="position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:2000;display:flex;align-items:center;justify-content:center;padding:16px">
      <div class="rv-card" style="width:100%;max-width:500px;max-height:80vh;overflow-y:auto">
        <div class="rv-ch">
          <div><div class="rv-ct">Select Your Ad Account</div><div class="rv-cst">Choose which Facebook Ad Account to connect</div></div>
          <button @click="showAccountSelect=false" style="background:none;border:none;font-size:20px;cursor:pointer">✕</button>
        </div>
        <div class="rv-cb">
          <div v-if="loadingAccounts" style="text-align:center;padding:32px"><span class="rv-spin"></span></div>
          <div v-else>
            <div v-for="acc in availableAccounts" :key="acc.id" @click="pendingAccount=acc"
              style="padding:14px 16px;border:2px solid var(--border);border-radius:var(--r-md);margin-bottom:10px;cursor:pointer"
              :style="{borderColor:pendingAccount?.id===acc.id?'var(--green)':'var(--border)',background:pendingAccount?.id===acc.id?'var(--green-light)':'var(--card)'}">
              <div style="font-weight:800;font-size:14px">{{ acc.name }}</div>
              <div style="font-size:12px;color:var(--slate-mid)">{{ acc.id }} · {{ acc.currency }}</div>
            </div>
            <div v-if="!availableAccounts.length" class="rv-al rv-al-b">No ad accounts found.</div>
            <div style="display:flex;gap:8px;margin-top:16px">
              <button class="rv-btn rv-btn-p" @click="confirmAccountSelection" :disabled="!pendingAccount||savingAccount">
                <span v-if="savingAccount" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
                <span v-else>✅ Connect This Account</span>
              </button>
              <button class="rv-btn rv-btn-s" @click="showAccountSelect=false">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import { fmtK as _fmtK, fmtNum } from '@/utils/format'

const emit = defineEmits(['toast'])
const auth = useAuthStore()

const campaigns         = ref([])
const adAccounts        = ref([])
const selectedAccountId = ref('')
const loading           = ref(false)
const connecting        = ref(false)
const syncing           = ref(false)
const syncMsg           = ref('')
const expanded          = ref({})
const adDetails         = ref({})
const lastSynced        = ref(null)
const filterStatus      = ref('')
const filterPlatform    = ref('')
const filterObjective   = ref('')
const searchQuery       = ref('')
const currentPage       = ref(1)
const pageSize          = ref(20)
const showAccountSelect = ref(false)
const availableAccounts = ref([])
const pendingAccount    = ref(null)
const loadingAccounts   = ref(false)
const savingAccount     = ref(false)

const fbConnected     = computed(() => auth.tenant?.meta_fb_connected === true)
const currency        = computed(() => auth.tenant?.currency || 'KES')
function fmtK(v)      { return _fmtK(v, currency.value) }
const selectedAccount = computed(() => adAccounts.value.find(a => a.id === selectedAccountId.value) || null)

const filteredCampaigns = computed(() => {
  let list = campaigns.value || []
  if (filterStatus.value)    list = list.filter(c => c.status === filterStatus.value)
  if (filterPlatform.value)  list = list.filter(c => c.platform === filterPlatform.value)
  if (filterObjective.value) list = list.filter(c => c.objective === filterObjective.value)
  if (searchQuery.value)     list = list.filter(c => c.name?.toLowerCase().includes(searchQuery.value.toLowerCase()))
  return list
})

const totalPages         = computed(() => Math.ceil(filteredCampaigns.value.length / pageSize.value) || 1)
const paginatedCampaigns = computed(() => filteredCampaigns.value.slice((currentPage.value-1)*pageSize.value, currentPage.value*pageSize.value))
const pageRange          = computed(() => { const t=totalPages.value,c=currentPage.value,p=[]; for(let i=Math.max(1,c-2);i<=Math.min(t,c+2);i++) p.push(i); return p })
const uniqueObjectives   = computed(() => [...new Set(campaigns.value.map(c=>c.objective).filter(Boolean))].sort())
const hasFilters         = computed(() => filterStatus.value||filterPlatform.value||filterObjective.value||searchQuery.value)

const totals = computed(() => {
  const list = filteredCampaigns.value
  const spend=list.reduce((s,c)=>s+Number(c.spend||0),0)
  const impressions=list.reduce((s,c)=>s+Number(c.impressions||0),0)
  const clicks=list.reduce((s,c)=>s+Number(c.clicks||0),0)
  const conversations=list.reduce((s,c)=>s+Number(c.conversations||0),0)
  const revenue=list.reduce((s,c)=>s+Number(c.revenue||0),0)
  return {
    spend, impressions, conversations, revenue,
    ctr: impressions?(clicks/impressions*100):0,
    cpm: impressions?(spend/impressions*1000):0,
    cpr: conversations?(spend/conversations):0,
    roi: list.length?list.reduce((s,c)=>s+Number(c.roi||0),0)/list.length:0,
  }
})

const lastSyncLabel = computed(() => {
  if (!lastSynced.value) return 'never synced'
  const d=Math.floor((Date.now()-new Date(lastSynced.value))/60000)
  return d<1?'synced just now':d<60?`synced ${d}m ago`:`synced ${Math.floor(d/60)}h ago`
})

watch([filterStatus,filterPlatform,filterObjective,searchQuery,selectedAccountId],()=>{ currentPage.value=1 })

function ctrColor(v)       { return v>=2?'var(--green)':v>=1?'var(--blue)':'var(--amber)' }
function cprColor(cpr,aov) { if(!cpr||!aov) return 'var(--slate)'; const r=cpr/aov; return r<0.2?'var(--green)':r<0.5?'var(--blue)':'var(--amber)' }
function roiColor(v)       { return v>=150?'var(--green)':v>=50?'var(--blue)':'var(--amber)' }
function clearFilters()    { filterStatus.value='';filterPlatform.value='';filterObjective.value='';searchQuery.value='' }

async function loadAdAccounts() {
  try {
    const r = await api.get('/meta/accounts/')
    adAccounts.value = r.data.results||r.data||[]
    if (adAccounts.value.length===1) selectedAccountId.value=adAccounts.value[0].id
  } catch(e) { adAccounts.value=[] }
}

async function loadCampaigns() {
  loading.value=true
  try {
    let url='/meta/campaigns/?platform=facebook'
    if (selectedAccountId.value) url+=`&account=${selectedAccountId.value}`
    const r = await api.get(url)
    const data=r.data
    campaigns.value=Array.isArray(data)?data:(data.results||[])
    if (campaigns.value.length&&campaigns.value[0].last_synced) lastSynced.value=campaigns.value[0].last_synced
  } catch(e) { console.error('loadCampaigns:',e?.response?.status,e?.message); campaigns.value=[] }
  loading.value=false
}

async function onAccountChange() { expanded.value={};adDetails.value={};await loadCampaigns() }

async function toggleExpand(id) {
  expanded.value[id]=!expanded.value[id]
  if (expanded.value[id]&&adDetails.value[id]===undefined) {
    adDetails.value[id]=null
    try { const r=await api.get(`/meta/campaigns/${id}/`);adDetails.value[id]=r.data.ads||[] } catch(e) { adDetails.value[id]=[] }
  }
}

async function syncNow(force=false) {
  syncing.value=true;syncMsg.value=''
  try { const r=await api.post('/meta/sync/',{force});syncMsg.value=r.data.message||'Sync started';if(force) setTimeout(loadCampaigns,3000) } catch(e){syncMsg.value='Sync failed'}
  syncing.value=false
}

async function connectFacebook() {
  connecting.value=true
  try { const r=await api.get('/meta/auth/');if(r.data.oauth_url) window.location.href=r.data.oauth_url } catch(e){emit('toast','Failed to start Facebook connection','red')}
  connecting.value=false
}

async function confirmAccountSelection() {
  if (!pendingAccount.value) return
  savingAccount.value=true
  try {
    await api.post('/meta/select-account/',{account_id:pendingAccount.value.id})
    showAccountSelect.value=false;await auth.fetchUser()
    emit('toast',`✅ Facebook Ads connected — ${pendingAccount.value.name}`,'green')
    await loadAdAccounts();await loadCampaigns()
  } catch(e){emit('toast','Failed to connect account','red')}
  savingAccount.value=false
}

onMounted(async () => {
  await auth.fetchUser()
  const params=new URLSearchParams(window.location.search)
  if (params.get('meta_select_account')==='1') {
    window.history.replaceState({},'',window.location.pathname)
    loadingAccounts.value=true;showAccountSelect.value=true
    try { const r=await api.get('/meta/select-account/');availableAccounts.value=r.data.ad_accounts||[];if(availableAccounts.value.length===1) pendingAccount.value=availableAccounts.value[0] } catch(e){emit('toast','Failed to load ad accounts','red');showAccountSelect.value=false}
    loadingAccounts.value=false
  }
  if (params.get('meta_connected')==='1') { window.history.replaceState({},'',window.location.pathname);await auth.fetchUser();emit('toast','✅ Facebook connected successfully!','green') }
  if (params.get('meta_error')) { emit('toast',`Facebook error: ${decodeURIComponent(params.get('meta_error'))}`,'red');window.history.replaceState({},'',window.location.pathname) }
  await loadAdAccounts()
  await loadCampaigns()
  syncNow(false)
})
</script>