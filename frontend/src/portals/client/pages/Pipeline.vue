<template>
  <div style="display:flex;flex-direction:column;gap:18px">
    <div style="display:flex;align-items:center;justify-content:space-between" class="fade-up">
      <div>
        <div style="font-size:21px;font-weight:900;letter-spacing:-.4px">Sales Pipeline</div>
        <div style="font-size:13px;color:var(--slate-light);font-weight:600;margin-top:3px">Every real ad click, and whether it's synced as a sale from Kommo</div>
      </div>
      <select v-model="platformFilter" class="rv-fi" style="width:auto;padding:7px 11px;font-size:12.5px">
        <option value="">All Platforms</option><option value="facebook">Facebook</option><option value="instagram">Instagram</option>
      </select>
    </div>

    <!-- Pipeline summary -->
    <div class="rv-aov card-reveal" style="animation-delay:.1s">
      <div class="rv-aov-cell"><div class="rv-aov-label">Total Clicks</div><div class="rv-aov-value">{{ summary.total }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Qualified Hot</div><div class="rv-aov-value" style="color:#dc2626">{{ summary.qualifiedHot }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Closed Won</div><div class="rv-aov-value" style="color:var(--green)">{{ summary.closedWon }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Closed Lost</div><div class="rv-aov-value" style="color:var(--red)">{{ summary.closedLost }}</div></div>
    </div>

    <!-- All Kommo Leads (raw, not tied to an ad click) -->
    <div v-if="kommoLeads.connected" class="rv-card card-reveal" style="animation-delay:.2s">
      <div class="rv-ch" style="display:flex;align-items:center;justify-content:space-between">
        <span class="rv-ct">All Kommo Leads</span>
        <div style="display:flex;align-items:center;gap:8px">
          <button class="rv-btn rv-btn-s rv-btn-sm" @click="kommoPage=Math.max(1,kommoPage-1); loadKommoLeads()" :disabled="kommoPage<=1 || kommoLeadsLoading">
            <i class="ti ti-chevron-left" aria-hidden="true"></i>
          </button>
          <span style="font-size:12px;font-weight:700;color:var(--slate-light)">Page {{ kommoPage }}</span>
          <button class="rv-btn rv-btn-s rv-btn-sm" @click="kommoPage++; loadKommoLeads()" :disabled="kommoLeads.results.length<15 || kommoLeadsLoading">
            <i class="ti ti-chevron-right" aria-hidden="true"></i>
          </button>
        </div>
      </div>
      <div v-if="kommoLeadsLoading" style="padding:30px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else-if="kommoLeads.results.length===0" class="rv-empty">
        <div style="font-weight:800;margin-top:8px">No leads on this page</div>
      </div>
      <div v-else class="rv-tw">
        <table class="rv-table">
          <thead><tr><th>Lead</th><th>Stage</th><th>Value</th><th>Updated</th></tr></thead>
          <tbody>
            <tr v-for="lead in kommoLeads.results" :key="lead.id">
              <td><strong>{{ lead.name }}</strong></td>
              <td><span class="rv-badge" :class="isClosedWon(lead.stage_name)?'rv-bg':isClosedLost(lead.stage_name)?'rv-br':'rv-bgy'">{{ lead.stage_name }}</span></td>
              <td>{{ lead.price ? fmtMoney(lead.price) : '—' }}</td>
              <td style="white-space:nowrap">{{ lead.updated_at ? timeAgo(new Date(lead.updated_at*1000)) : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Deal list -->
    <div class="rv-card card-reveal" style="animation-delay:.15s">
      <div v-if="loading" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else-if="filtered.length===0" class="rv-empty">
        <div class="rv-empty-icon"><i class="ti ti-flame" aria-hidden="true"></i></div>
        <div style="font-weight:800;margin-top:8px">No clicks yet</div>
        <div style="font-size:12.5px;color:var(--slate-light);margin-top:4px">Deals appear here automatically when a customer clicks your ads</div>
      </div>
      <div v-else class="rv-tw">
        <table class="rv-table">
          <thead>
            <tr>
              <th>Customer</th><th>Platform</th><th>Channel</th><th>Ad / Campaign</th>
              <th>Clicked</th><th>Velocity</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="deal in filtered" :key="deal.id">
              <td><strong>{{ deal.customer_name || 'Anonymous' }}</strong><div v-if="deal.customer_phone" style="font-size:11px;color:var(--slate-light);font-weight:600">{{ deal.customer_phone }}</div></td>
              <td>
                <span :style="deal.platform==='instagram'?igStyle:''"><i :class="['ti', platformIcon(deal.platform)]" aria-hidden="true"></i> {{ deal.platform==='instagram'?'Instagram':'Facebook' }}</span>
              </td>
              <td><i :class="['ti', channelIcon(deal.source)]" aria-hidden="true"></i> {{ channelLabel(deal.source) }}</td>
              <td>{{ deal.ad_name || '—' }}<div v-if="deal.campaign_name" style="font-size:11px;color:var(--slate-light);font-weight:600">{{ deal.campaign_name }}</div></td>
              <td style="white-space:nowrap">{{ timeAgo(deal.new_click_at || deal.created_at) }}</td>
              <td><span class="rv-d-vel" :class="velClass(deal.velocity)" style="margin-top:0"><i :class="['ti', velIcon(deal.velocity)]" :style="{color: velColor(deal.velocity)}" aria-hidden="true"></i> {{ deal.velocity }}</span></td>
              <td>
                <span v-if="deal.has_sale" class="rv-badge rv-bg"><i class="ti ti-circle-check" aria-hidden="true"></i> Synced Sale</span>
                <span v-else class="rv-badge rv-bgy">Awaiting Kommo</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { useFormat } from '@/composables/useFormat'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
dayjs.extend(relativeTime)

const { fmtMoney } = useFormat()

defineEmits(['nav','toast'])
const deals  = ref([])
const funnel = ref({ connected:false, stages:[] })
const kommoLeads = ref({ connected:false, results:[] })
const kommoPage = ref(1)
const kommoLeadsLoading = ref(false)
const loading = ref(true)
const platformFilter = ref('')

const filtered = computed(() => platformFilter.value ? deals.value.filter(d=>d.platform===platformFilter.value) : deals.value)
const summary  = computed(() => {
  const stages = funnel.value.stages || []
  const sumMatching = (re) => stages.filter(s=>re.test(s.name)).reduce((a,s)=>a+s.count,0)
  return {
    total:       deals.value.length,
    qualifiedHot: sumMatching(/hot/i),
    closedWon:    sumMatching(/won/i),
    closedLost:   sumMatching(/lost/i),
  }
})

const igStyle = 'background:linear-gradient(135deg,var(--ig1),var(--ig3));-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800'
function platformIcon(p) { return p==='instagram'?'ti-brand-instagram':'ti-brand-facebook' }
function channelLabel(source) {
  return {'whatsapp_webhook':'WhatsApp','messenger_webhook':'Messenger','instagram_webhook':'Instagram DM'}[source] || '—'
}
function channelIcon(source) {
  return {'whatsapp_webhook':'ti-brand-whatsapp','messenger_webhook':'ti-brand-messenger','instagram_webhook':'ti-brand-instagram'}[source] || 'ti-message-circle'
}
function velClass(v) { return v==='hot'?'vel-hot':v==='warm'?'vel-warm':'vel-cold' }
function velIcon(v)  { return v==='hot'?'ti-flame':v==='warm'?'ti-circle-filled':'ti-snowflake' }
function velColor(v) { return v==='warm'?'#d97706':v==='hot'?'#dc2626':'#2563eb' }
function timeAgo(dt) { return dt ? dayjs(dt).fromNow() : '' }
function isClosedWon(name)  { return /won/i.test(name || '') }
function isClosedLost(name) { return /lost/i.test(name || '') }

async function loadKommoLeads() {
  kommoLeadsLoading.value = true
  try { const r = await api.get(`/kommo/leads/?limit=15&page=${kommoPage.value}`); kommoLeads.value = r.data } catch(e) {}
  kommoLeadsLoading.value = false
}

async function loadDeals() {
  loading.value = true
  try { const r = await api.get('/pipeline/deals/'); deals.value = r.data.results || r.data || [] } catch(e) {}
  try { const r = await api.get('/kommo/funnel/'); funnel.value = r.data } catch(e) {}
  loading.value = false
  await loadKommoLeads()
}

useAutoRefresh(loadDeals, 45000)
</script>
