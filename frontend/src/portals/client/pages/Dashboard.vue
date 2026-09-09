<template>
  <div style="display:flex;flex-direction:column;gap:18px" :class="{'rv-refresh-flash': flashing}">
    <!-- Live indicator -->
    <div style="display:flex;align-items:center;justify-content:flex-end">
      <span style="display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;color:var(--slate-light)">
        <span v-if="refreshing" class="rv-spin" style="width:10px;height:10px;border-width:1.5px"></span>
        <span v-else style="width:8px;height:8px;border-radius:50%;background:var(--green);display:inline-block;animation:pulse 2s infinite"></span>
        {{ refreshing ? 'Updating...' : lastUpdated ? 'Live · ' + new Date(lastUpdated).toLocaleTimeString() : 'Loading...' }}
      </span>
    </div>
    <!-- GPS Strip -->
    <div class="rv-gps fade-up" :class="gpsClass">
      <div>
        <div class="rv-gps-lbl">Revenue GPS — {{ monthLabel }}</div>
        <div class="rv-gps-status"><i :class="['ti', gpsIcon]" aria-hidden="true"></i> {{ gpsTitle }}</div>
        <div class="rv-gps-sub">{{ gpsSub }}</div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div class="rv-gps-pct">{{ gpsPercent }}%</div>
        <div class="rv-gps-pct-lbl">Goal progress</div>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="rv-stat-grid">
      <div class="rv-sc card-reveal" style="animation-delay:.05s">
        <div class="rv-sc-label">Total Revenue</div>
        <div class="rv-sc-value count-up">{{ fmtK(metrics.total_revenue) }}</div>
        <div class="rv-sc-sub">This month &bull; All platforms</div>
      </div>
      <div class="rv-sc b card-reveal" style="animation-delay:.1s">
        <div class="rv-sc-label">Ad Spend</div>
        <div class="rv-sc-value count-up">{{ fmtK(metrics.total_spend) }}</div>
        <div class="rv-sc-sub">Facebook + Instagram</div>
      </div>
      <div class="rv-sc a card-reveal" style="animation-delay:.15s">
        <div class="rv-sc-label">ROI</div>
        <div class="rv-sc-value count-up">{{ metrics.roi || 0 }}%</div>
        <div class="rv-sc-sub">Return on ad spend</div>
      </div>
      <div class="rv-sc p card-reveal" style="animation-delay:.2s">
        <div class="rv-sc-label">Conversations</div>
        <div class="rv-sc-value count-up">{{ metrics.total_conversations || 0 }}</div>
        <div class="rv-sc-sub">WhatsApp clicks this month</div>
      </div>
    </div>

    <!-- AOV Strip -->
    <div class="rv-aov card-reveal" style="animation-delay:.25s">
      <div class="rv-aov-cell"><div class="rv-aov-label">AOV — All</div><div class="rv-aov-value">{{ fmtK(metrics.avg_order_value) }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Facebook AOV</div><div class="rv-aov-value">{{ fmtK(metrics.facebook_aov) }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Instagram AOV</div><div class="rv-aov-value" style="background:linear-gradient(135deg,var(--ig1),var(--ig3));-webkit-background-clip:text;-webkit-text-fill-color:transparent">{{ fmtK(metrics.instagram_aov) }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Rev / Conversation</div><div class="rv-aov-value">{{ fmtK(metrics.total_spend>0?(metrics.total_revenue/Math.max(metrics.total_conversations,1)):0) }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Cost / Conv.</div><div class="rv-aov-value">{{ fmtK(metrics.cost_per_conversation) }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">ROAS</div><div class="rv-aov-value" style="color:var(--green)">{{ metrics.roas ? metrics.roas.toFixed(2)+"x" : "—" }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">CPA</div><div class="rv-aov-value">{{ metrics.cpa ? fmtK(metrics.cpa) : "—" }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">CPL</div><div class="rv-aov-value">{{ metrics.cpl ? fmtK(metrics.cpl) : "—" }}</div></div>
    </div>

    <!-- Ad Spend & DM Metrics -->
    <div v-if="adSpend.facebook.impressions || adSpend.instagram.impressions || waClicks.total" class="rv-card card-reveal" style="animation-delay:.4s">
      <div class="rv-ch">
        <span class="rv-ct">Ad Spend &amp; Channel Activity — This Month</span>
      </div>
      <div class="rv-cb" style="display:flex;flex-direction:column;gap:16px">
        <!-- Platform breakdown -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
          <!-- Facebook -->
          <div style="background:var(--bg);border-radius:var(--r-md);padding:14px;border:1px solid var(--border)">
            <div style="font-size:10.5px;font-weight:800;color:var(--blue);text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px"><i class="ti ti-brand-facebook" aria-hidden="true"></i> Facebook</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
              <div><div style="font-size:10px;color:var(--slate-light);font-weight:700">Spend</div><div style="font-size:14px;font-weight:900">{{ fmtK(adSpend.facebook.spend) }}</div></div>
              <div><div style="font-size:10px;color:var(--slate-light);font-weight:700">Impressions</div><div style="font-size:14px;font-weight:900">{{ fmtNum(adSpend.facebook.impressions) }}</div></div>
              <div><div style="font-size:10px;color:var(--slate-light);font-weight:700">Clicks</div><div style="font-size:14px;font-weight:900">{{ fmtNum(adSpend.facebook.clicks) }}</div></div>
              <div><div style="font-size:10px;color:var(--slate-light);font-weight:700">DMs Started</div><div style="font-size:14px;font-weight:900;color:var(--blue)">{{ adSpend.facebook.dm_conversations }}</div></div>
            </div>
          </div>
          <!-- Instagram -->
          <div style="background:var(--bg);border-radius:var(--r-md);padding:14px;border:1px solid var(--border)">
            <div style="font-size:10.5px;font-weight:800;background:linear-gradient(90deg,var(--ig1),var(--ig3));-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px"><i class="ti ti-brand-instagram" aria-hidden="true"></i> Instagram</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
              <div><div style="font-size:10px;color:var(--slate-light);font-weight:700">Spend</div><div style="font-size:14px;font-weight:900">{{ fmtK(adSpend.instagram.spend) }}</div></div>
              <div><div style="font-size:10px;color:var(--slate-light);font-weight:700">Impressions</div><div style="font-size:14px;font-weight:900">{{ fmtNum(adSpend.instagram.impressions) }}</div></div>
              <div><div style="font-size:10px;color:var(--slate-light);font-weight:700">Clicks</div><div style="font-size:14px;font-weight:900">{{ fmtNum(adSpend.instagram.clicks) }}</div></div>
              <div><div style="font-size:10px;color:var(--slate-light);font-weight:700">DMs Started</div><div style="font-size:14px;font-weight:900;color:var(--purple)">{{ adSpend.instagram.dm_conversations }}</div></div>
            </div>
          </div>
        </div>
        <!-- DM conversations by channel -->
        <div>
          <div style="font-size:10.5px;font-weight:800;color:var(--slate-mid);text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px"><i class="ti ti-message-circle" aria-hidden="true"></i> Conversations started from ads (last 30 days)</div>
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px">
            <div style="text-align:center;padding:10px;background:var(--green-light);border-radius:var(--r-md)">
              <div style="font-size:18px;font-weight:900;color:var(--green)">{{ waClicks.whatsapp }}</div>
              <div style="font-size:10px;font-weight:700;color:var(--green)">WhatsApp</div>
            </div>
            <div style="text-align:center;padding:10px;background:var(--blue-light);border-radius:var(--r-md)">
              <div style="font-size:18px;font-weight:900;color:var(--blue)">{{ waClicks.messenger }}</div>
              <div style="font-size:10px;font-weight:700;color:var(--blue)">Messenger</div>
            </div>
            <div style="text-align:center;padding:10px;background:var(--purple-light);border-radius:var(--r-md)">
              <div style="font-size:18px;font-weight:900;color:var(--purple)">{{ waClicks.instagram }}</div>
              <div style="font-size:10px;font-weight:700;color:var(--purple)">Instagram DM</div>
            </div>
            <div style="text-align:center;padding:10px;background:var(--bg);border-radius:var(--r-md);border:1px solid var(--border)">
              <div style="font-size:18px;font-weight:900;color:var(--slate)">{{ waClicks.total }}</div>
              <div style="font-size:10px;font-weight:700;color:var(--slate-mid)">Total</div>
            </div>
          </div>
          <div style="margin-top:10px;text-align:center;padding:10px;background:var(--green-light);border-radius:var(--r-md)">
            <div style="font-size:18px;font-weight:900;color:var(--green)"><i class="ti ti-circle-check" aria-hidden="true"></i> {{ waClicks.synced_to_sale }}</div>
            <div style="font-size:10px;font-weight:700;color:var(--green)">Synced to a sale via Kommo</div>
          </div>
        </div>
      </div>
    </div>

    <div class="rv-g2">
      <!-- 7-day chart -->
      <div class="rv-card card-reveal" style="animation-delay:.3s">
        <div class="rv-ch"><span class="rv-ct">Revenue — Last 7 Days</span></div>
        <div class="rv-cb">
          <div v-if="dailyRevenue.length===0" style="color:var(--slate-light);font-size:13px;font-weight:600;text-align:center;padding:20px">No sales data yet</div>
          <div v-for="d in dailyRevenue" :key="d.date" class="rv-c-row">
            <div class="rv-c-lbl">{{ d.label }}</div>
            <div class="rv-c-track">
              <div class="rv-c-bar" :style="{width:d.width+'%',background:d.color}"></div>
            </div>
            <div class="rv-c-val">{{ fmtK(d.amount) }}</div>
          </div>
        </div>
      </div>
      <!-- Guidance -->
      <div class="rv-card card-reveal" style="animation-delay:.35s">
        <div class="rv-ch"><span class="rv-ct">Today's Guidance</span></div>
        <div class="rv-cb" style="display:flex;flex-direction:column;gap:10px">

          <!-- 1. No goal set -->
          <div v-if="!hasGoal" class="rv-al rv-al-b" style="margin:0">
            <i class="ti ti-target" aria-hidden="true"></i> <strong>Set a monthly revenue goal</strong> — Go to Revenue Goals to activate your GPS tracker and start measuring progress this month.
          </div>

          <!-- 2. Goal progress -->
          <div v-if="hasGoal && metrics.goal_status==='ahead'" class="rv-al rv-al-g" style="margin:0">
            <i class="ti ti-rocket" aria-hidden="true"></i> <strong>Ahead of goal!</strong> You're {{ gpsPercent }}% towards your {{ monthLabel }} target. Keep logging every sale to maintain accuracy.
          </div>
          <div v-else-if="hasGoal && metrics.goal_status==='behind'" class="rv-al rv-al-a" style="margin:0">
            <i class="ti ti-alert-triangle" aria-hidden="true"></i> <strong>Behind target.</strong> You're {{ gpsPercent }}% towards goal. You need <strong>{{ fmtK(metrics.required_daily_revenue) }}/day</strong> for the rest of the month to catch up.
          </div>
          <div v-else-if="hasGoal && metrics.goal_status==='on_track'" class="rv-al rv-al-b" style="margin:0">
            <i class="ti ti-circle-check" aria-hidden="true"></i> <strong>On track!</strong> {{ gpsPercent }}% to goal — {{ dayjs().daysInMonth()-dayjs().date() }} days left this month.
          </div>

          <!-- 3. No sales today -->
          <div v-if="hasGoal && todayRevenue===0" class="rv-al rv-al-a" style="margin:0">
            <i class="ti ti-clipboard-list" aria-hidden="true"></i> <strong>No sales logged today.</strong> Made a sale? Log it now to keep your Revenue GPS accurate.
          </div>

          <!-- 4. Cold pipeline deals -->
          <div v-if="coldDeals>0" class="rv-al rv-al-a" style="margin:0">
            <i class="ti ti-flame" aria-hidden="true"></i> <strong>{{ coldDeals }} pipeline deal{{ coldDeals>1?'s are':' is' }} going cold.</strong> These contacts haven't been followed up — reach out today before they go cold.
          </div>

          <!-- 5. Facebook not connected -->
          <div v-if="!auth.tenant?.meta_fb_connected" class="rv-al rv-al-b" style="margin:0">
            <i class="ti ti-brand-facebook" aria-hidden="true"></i> <strong>Connect your Facebook Ads</strong> — Go to Facebook Ads and connect your account to track ad spend and measure ROI automatically.
          </div>

          <!-- 6. AOV tip -->
          <div v-if="hasGoal && metrics.avg_order_value>0 && salesNeeded>0" style="font-size:12.5px;color:var(--slate-mid);font-weight:600;line-height:1.6;padding:10px 12px;background:var(--bg);border-radius:var(--r-md)">
            <i class="ti ti-bulb" aria-hidden="true"></i> At your current average order of <strong>{{ fmtK(metrics.avg_order_value) }}</strong>, you need approximately <strong>{{ salesNeeded }} more sales</strong> to reach your {{ monthLabel }} goal.
          </div>

          <!-- 7. All good -->
          <div v-if="hasGoal && coldDeals===0 && todayRevenue>0 && metrics.goal_status!=='behind' && auth.tenant?.meta_fb_connected"
            class="rv-al rv-al-g" style="margin:0">
            <i class="ti ti-circle-check" aria-hidden="true"></i> <strong>Everything looks good today.</strong> Keep logging sales and following up on your pipeline.
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'
import { fmtK as _fmtK, fmtFull, fmtNum } from '@/utils/format'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

const auth = useAuthStore()
const metrics = ref({ total_revenue:0, total_spend:0, roi:0, roas:0, cpa:0, cpl:0, total_conversations:0, avg_order_value:0, facebook_aov:0, instagram_aov:0, cost_per_conversation:0, goal_status:'no_goal', goal_progress_percent:0, revenue_goal:0, required_daily_revenue:0, revenue_gap:0 })
const dailyRevenue = ref([])
const coldDeals = ref(0)
const flashing  = ref(false)
const waClicks  = ref({ total:0, whatsapp:0, messenger:0, instagram:0, synced_to_sale:0 })
const adSpend   = ref({
  facebook:  { spend:0, impressions:0, clicks:0, dm_conversations:0 },
  instagram: { spend:0, impressions:0, clicks:0, dm_conversations:0 },
  conversations: { whatsapp:0, messenger:0, instagram:0, total:0 },
})

const monthLabel  = computed(() => dayjs().format('MMMM YYYY'))
const hasGoal     = computed(() => !!metrics.value.revenue_goal)
const gpsPercent  = computed(() => Math.round(metrics.value.goal_progress_percent || 0))
const gpsClass    = computed(() => metrics.value.goal_status || 'no_goal')
const gpsIcon     = computed(() => ({ ahead:'ti-rocket', on_track:'ti-circle-check', behind:'ti-alert-triangle', no_goal:'ti-map-pin' })[gpsClass.value])
const gpsTitle    = computed(() => ({ ahead:'Ahead of Goal', on_track:'On Track', behind:'Behind Goal', no_goal:'No Goal Set' })[gpsClass.value])
const gpsSub      = computed(() => {
  if (!hasGoal.value) return 'Go to Revenue Goals to set a monthly target'
  if (gpsClass.value==='ahead') return `Need ${fmtK(metrics.value.required_daily_revenue)}/day to maintain lead`
  if (gpsClass.value==='behind') return `Need ${fmtK(metrics.value.required_daily_revenue)}/day to catch up — ${dayjs().daysInMonth()-dayjs().date()} days left`
  return `${gpsPercent.value}% to goal — ${dayjs().daysInMonth()-dayjs().date()} days remaining`
})
const todayRevenue = computed(() => {
  if (!dailyRevenue.value?.length) return 0
  const today = dayjs().format('YYYY-MM-DD')
  const todayEntry = dailyRevenue.value.find(d => d.date === today)
  return todayEntry?.revenue || 0
})

const salesNeeded = computed(() => {
  const gap = (metrics.value.revenue_goal||0) - (metrics.value.total_revenue||0)
  if (gap<=0 || !metrics.value.avg_order_value) return '0'
  return Math.ceil(gap/metrics.value.avg_order_value)
})

// fmtNum imported from @/utils/format
function fmtK(v, cur) {
  return _fmtK(v, cur || auth.tenant?.currency || 'KES')
}

async function loadWaClicks() {
  try {
    const r = await api.get('/whatsapp/stats/')
    waClicks.value = r.data || { total:0, whatsapp:0, messenger:0, instagram:0, synced_to_sale:0 }
  } catch(e) {}
}

async function loadData() {
  // Brief flash to signal refresh
  flashing.value = true
  setTimeout(() => { flashing.value = false }, 400)
  try {
    const r = await api.get('/metrics/snapshot/')
    if (r.data) Object.assign(metrics.value, r.data)
  } catch(e) {}
  try {
    const r = await api.get('/sales/daily/?days=7')
    const data = r.data || []
    const max  = Math.max(...data.map(d=>d.amount||0), 1)
    dailyRevenue.value = data.map((d,i) => ({
      date: d.date, label: dayjs(d.date).format('ddd MMM D'),
      amount: d.amount||0, width: Math.round(((d.amount||0)/max)*100),
      color: i===data.length-1?'var(--border-mid)':i>=data.length-2?'linear-gradient(90deg,var(--ig1),var(--ig2))':'var(--green)',
    }))
  } catch(e) {}
  try {
    const r = await api.get('/pipeline/deals/?stage=new_click&velocity=cold')
    coldDeals.value = (r.data.results||r.data||[]).length
  } catch(e) {}
  try {
    const r = await api.get('/metrics/adspend/?days=30')
    if (r.data) {
      adSpend.value.facebook      = r.data.facebook || adSpend.value.facebook
      adSpend.value.instagram     = r.data.instagram || adSpend.value.instagram
      adSpend.value.conversations = r.data.conversations || adSpend.value.conversations
    }
  } catch(e) {}
}
const { lastUpdated, refreshing } = useAutoRefresh(loadData, 30000)
</script>
