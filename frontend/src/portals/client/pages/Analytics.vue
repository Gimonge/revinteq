<template>
  <div style="display:flex;flex-direction:column;gap:18px">

    <div class="fade-up">
      <div style="font-size:21px;font-weight:900;letter-spacing:-.4px;margin-bottom:3px">Analytics</div>
      <div style="display:flex;align-items:center;gap:8px">
        <div style="font-size:13px;color:var(--slate-light);font-weight:600">Performance breakdown — {{ periodLabel }}</div>
        <span v-if="loading && initialLoaded" class="rv-spin" style="width:10px;height:10px;border-width:2px;opacity:.5"></span>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="rv-card card-reveal">
      <div class="rv-ch">
        <span class="rv-ct">Filters</span>
        <button v-if="isCustomRange||filterPlatform" class="rv-btn rv-btn-s rv-btn-xs" @click="clearAll">✕ Reset</button>
      </div>
      <div class="rv-cb" style="display:flex;flex-direction:column;gap:12px">
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <button v-for="p in presets" :key="p.label"
            class="rv-btn rv-btn-s rv-btn-sm"
            :style="activePreset===p.label?{background:'var(--green)',color:'#fff',borderColor:'var(--green)'}:{}"
            @click="applyPreset(p)">
            {{ p.label }}
          </button>
        </div>
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <div style="display:flex;align-items:center;gap:8px">
            <label style="font-size:11.5px;font-weight:800;color:var(--slate-mid);white-space:nowrap">From</label>
            <input v-model="dateFrom" class="rv-fi" type="date" style="width:150px">
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <label style="font-size:11.5px;font-weight:800;color:var(--slate-mid);white-space:nowrap">To</label>
            <input v-model="dateTo" class="rv-fi" type="date" style="width:150px">
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <label style="font-size:11.5px;font-weight:800;color:var(--slate-mid);white-space:nowrap">Platform</label>
            <select v-model="filterPlatform" class="rv-fs" style="font-size:12px;padding:5px 10px;min-width:130px">
              <option value="">All Platforms</option>
              <option value="facebook">Facebook</option>
              <option value="instagram">Instagram</option>
              <option value="organic">Organic</option>
              <option value="referral">Referral</option>
            </select>
          </div>
          <button class="rv-btn rv-btn-p rv-btn-sm" @click="applyCustomRange" :disabled="!dateFrom||!dateTo||loading">
            <span v-if="loading" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
            <span v-else>Apply</span>
          </button>
        </div>
      </div>
    </div>

    <!-- KPI cards -->
    <div class="rv-stat-grid fade-up">
      <div class="rv-sc">
        <div class="rv-sc-label">Total Revenue</div>
        <div class="rv-sc-value">{{ fmtK(m.total_revenue) }}</div>
        <div class="rv-sc-sub">{{ filterPlatform || 'All platforms' }}</div>
      </div>
      <div class="rv-sc b">
        <div class="rv-sc-label">Facebook Revenue</div>
        <div class="rv-sc-value">{{ fmtK(m.facebook_revenue) }}</div>
        <div class="rv-sc-sub">{{ fbPct }}% of total</div>
      </div>
      <div class="rv-sc ig">
        <div class="rv-sc-label">Instagram Revenue</div>
        <div class="rv-sc-value" style="background:linear-gradient(135deg,var(--ig1),var(--ig3));-webkit-background-clip:text;-webkit-text-fill-color:transparent">
          {{ fmtK(m.instagram_revenue) }}
        </div>
        <div class="rv-sc-sub">{{ igPct }}% of total</div>
      </div>
      <div class="rv-sc a">
        <div class="rv-sc-label">ROAS</div>
        <div class="rv-sc-value">{{ m.roas ? m.roas.toFixed(1)+'x' : '—' }}</div>
        <div class="rv-sc-sub">{{ m.total_sales_count||0 }} sales · KES {{ m.roas ? m.roas.toFixed(2) : '0' }} per spend</div>
      </div>
    </div>

    <!-- AOV strip -->
    <div class="rv-aov fade-up" style="animation-delay:.1s">
      <div class="rv-aov-cell">
        <div class="rv-aov-label">AOV — All</div>
        <div class="rv-aov-value">{{ fmtK(m.avg_order_value) }}</div>
      </div>
      <div class="rv-aov-cell">
        <div class="rv-aov-label">Facebook AOV</div>
        <div class="rv-aov-value">{{ fmtK(m.facebook_aov) }}</div>
      </div>
      <div class="rv-aov-cell">
        <div class="rv-aov-label">Instagram AOV</div>
        <div class="rv-aov-value" style="background:linear-gradient(135deg,var(--ig1),var(--ig3));-webkit-background-clip:text;-webkit-text-fill-color:transparent">
          {{ fmtK(m.instagram_aov) }}
        </div>
      </div>
      <div class="rv-aov-cell">
        <div class="rv-aov-label">Ad Spend</div>
        <div class="rv-aov-value">{{ fmtK(m.total_spend) }}</div>
      </div>
      <div class="rv-aov-cell">
        <div class="rv-aov-label">Conversations</div>
        <div class="rv-aov-value">{{ m.total_conversations||0 }}</div>
      </div>
    </div>

    <!-- Ad performance table -->
    <div class="rv-card card-reveal">
      <div class="rv-ch">
        <div>
          <span class="rv-ct">Ad Performance</span>
          <div class="rv-cst">{{ filteredAds.length }} ads{{ filterPlatform ? ' on '+filterPlatform : '' }}</div>
        </div>
        <button class="rv-btn rv-btn-s rv-btn-sm" @click="loadData" :disabled="loading">↻ Sync</button>
      </div>
      <div v-if="loading && !initialLoaded" style="padding:32px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else class="rv-tw">
        <table class="rv-table">
          <thead><tr>
            <th>Ad</th><th>Platform</th><th>Spend</th>
            <th>Revenue</th><th>ROI</th><th>AOV</th>
            <th>Sales</th><th>DMs</th>
          </tr></thead>
          <tbody>
            <tr v-for="ad in adPaginated" :key="ad.id">
              <td><strong>{{ ad.name }}</strong></td>
              <td><span class="rv-badge" :class="ad.platform==='instagram'?'rv-big':'rv-bb'">{{ ad.platform }}</span></td>
              <td>{{ fmtK(ad.spend) }}</td>
              <td><strong>{{ fmtK(ad.revenue) }}</strong></td>
              <td><strong :style="{color:'var(--green)'}">{{ ad.roi||0 }}%</strong></td>
              <td>{{ fmtK(ad.aov) }}</td>
              <td>{{ ad.sales_count||0 }}</td>
              <td>{{ ad.conversations||0 }}</td>
            </tr>
            <tr v-if="!filteredAds.length">
              <td colspan="8" style="text-align:center;color:var(--slate-light);padding:32px">
                {{ ads.length ? 'No ads match your filters.' : 'No ad data — connect Facebook/Instagram to see performance' }}
              </td>
            </tr>
          </tbody>
          <tfoot v-if="filteredAds.length">
            <tr style="background:var(--bg);font-weight:900;border-top:2px solid var(--border)">
              <td colspan="2" style="font-size:11px;color:var(--slate-mid)">TOTALS ({{ filteredAds.length }} ads)</td>
              <td>{{ fmtK(adTotals.spend) }}</td>
              <td>{{ fmtK(adTotals.revenue) }}</td>
              <td :style="{color:'var(--green)'}">{{ adTotals.roi.toFixed(1) }}%</td>
              <td>{{ fmtK(adTotals.aov) }}</td>
              <td>{{ adTotals.sales }}</td>
              <td>{{ adTotals.conversations }}</td>
            </tr>
          </tfoot>
        </table>
        <!-- Pagination -->
        <div v-if="adTotalPages>1" style="display:flex;gap:8px;align-items:center;justify-content:center;padding:14px;border-top:1px solid var(--border)">
          <button class="rv-btn rv-btn-s rv-btn-xs" @click="adPage=1" :disabled="adPage===1">««</button>
          <button class="rv-btn rv-btn-s rv-btn-xs" @click="adPage--" :disabled="adPage===1">‹</button>
          <template v-for="p in adPageRange" :key="p">
            <button class="rv-btn rv-btn-xs" :class="p===adPage?'rv-btn-p':'rv-btn-s'" @click="adPage=p">{{ p }}</button>
          </template>
          <button class="rv-btn rv-btn-s rv-btn-xs" @click="adPage++" :disabled="adPage===adTotalPages">›</button>
          <button class="rv-btn rv-btn-s rv-btn-xs" @click="adPage=adTotalPages" :disabled="adPage===adTotalPages">»»</button>
          <span style="font-size:12px;color:var(--slate-mid);margin-left:8px">
            {{ (adPage-1)*adPageSize+1 }}–{{ Math.min(adPage*adPageSize,filteredAds.length) }} of {{ filteredAds.length }}
          </span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'
import { fmtK as _fmtK } from '@/utils/format'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

const auth           = useAuthStore()
const loading        = ref(true)
const initialLoaded  = ref(false)
const activePreset   = ref('This Month')
const isCustomRange  = ref(false)
const filterPlatform = ref('')
const adPage     = ref(1)
const adPageSize = 20

const dateFrom = ref(dayjs().startOf('month').format('YYYY-MM-DD'))
const dateTo   = ref(dayjs().format('YYYY-MM-DD'))

const m = ref({
  total_revenue:0, facebook_revenue:0, instagram_revenue:0,
  roi:0, avg_order_value:0, facebook_aov:0, instagram_aov:0,
  cost_per_sale:0, total_spend:0, total_sales_count:0, total_conversations:0, roas:0, cpa:0, cpl:0, pipeline_count:0,
})
const ads = ref([])

const fbPct = computed(() => m.value.total_revenue ? Math.round((m.value.facebook_revenue/m.value.total_revenue)*100) : 0)
const igPct = computed(() => m.value.total_revenue ? Math.round((m.value.instagram_revenue/m.value.total_revenue)*100) : 0)

const filteredAds = computed(() => {
  if (!filterPlatform.value) return ads.value
  return ads.value.filter(a => a.platform === filterPlatform.value)
})

const adTotals = computed(() => {
  const list    = filteredAds.value
  const spend   = list.reduce((s,a)=>s+Number(a.spend||0),0)
  const revenue = list.reduce((s,a)=>s+Number(a.revenue||0),0)
  const sales   = list.reduce((s,a)=>s+Number(a.sales_count||0),0)
  const convs   = list.reduce((s,a)=>s+Number(a.conversations||0),0)
  return {
    spend, revenue, sales, conversations: convs,
    roi: spend ? ((revenue-spend)/spend*100) : 0,
    aov: sales ? revenue/sales : 0,
  }
})

const adTotalPages  = computed(() => Math.ceil(filteredAds.value.length / adPageSize) || 1)
const adPaginated   = computed(() => filteredAds.value.slice((adPage.value-1)*adPageSize, adPage.value*adPageSize))
const adPageRange   = computed(() => {
  const t=adTotalPages.value, c=adPage.value, p=[]
  for (let i=Math.max(1,c-2); i<=Math.min(t,c+2); i++) p.push(i)
  return p
})

const periodLabel = computed(() => {
  const from = dayjs(dateFrom.value).format('D MMM YYYY')
  const to   = dayjs(dateTo.value).format('D MMM YYYY')
  return from === to ? from : `${from} – ${to}`
})

const presets = [
  { label:'Today',      from: dayjs().format('YYYY-MM-DD'),                                           to: dayjs().format('YYYY-MM-DD') },
  { label:'This Week',  from: dayjs().startOf('week').format('YYYY-MM-DD'),                           to: dayjs().format('YYYY-MM-DD') },
  { label:'This Month', from: dayjs().startOf('month').format('YYYY-MM-DD'),                          to: dayjs().format('YYYY-MM-DD') },
  { label:'Last Month', from: dayjs().subtract(1,'month').startOf('month').format('YYYY-MM-DD'),      to: dayjs().subtract(1,'month').endOf('month').format('YYYY-MM-DD') },
  { label:'Last 7d',    from: dayjs().subtract(6,'days').format('YYYY-MM-DD'),                        to: dayjs().format('YYYY-MM-DD') },
  { label:'Last 30d',   from: dayjs().subtract(29,'days').format('YYYY-MM-DD'),                       to: dayjs().format('YYYY-MM-DD') },
  { label:'Last 90d',   from: dayjs().subtract(89,'days').format('YYYY-MM-DD'),                       to: dayjs().format('YYYY-MM-DD') },
]

function resetPage() { adPage.value = 1 }

function applyPreset(p) {
  dateFrom.value      = p.from
  dateTo.value        = p.to
  activePreset.value  = p.label
  isCustomRange.value = false
  resetPage()
  loadData()
}

function applyCustomRange() {
  if (!dateFrom.value || !dateTo.value) return
  activePreset.value  = ''
  isCustomRange.value = true
  resetPage()
  loadData()
}

function clearAll() {
  filterPlatform.value = ''
  isCustomRange.value  = false
  resetPage()
  applyPreset(presets.find(p => p.label === 'This Month'))
}

function fmtK(v) { return _fmtK(v, auth.tenant?.currency || 'KES') }

async function loadData() {
  loading.value = true
  const params = `date_from=${dateFrom.value}&date_to=${dateTo.value}${filterPlatform.value ? '&platform='+filterPlatform.value : ''}`

  const [metricsRes, adsRes] = await Promise.allSettled([
    api.get(`/metrics/snapshot/?${params}`),
    api.get(`/meta/ads/performance/?${params}`),
  ])

  if (metricsRes.status === 'fulfilled' && metricsRes.value.data) {
    Object.assign(m.value, metricsRes.value.data)
  }
  if (adsRes.status === 'fulfilled') {
    ads.value = adsRes.value.data || []
  }

  loading.value = false
  initialLoaded.value = true
}

useAutoRefresh(loadData, 60000)
</script>
