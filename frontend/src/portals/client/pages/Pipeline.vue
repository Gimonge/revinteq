<template>
  <div style="display:flex;flex-direction:column;gap:18px">
    <div style="display:flex;align-items:center;justify-content:space-between" class="fade-up">
      <div>
        <div style="font-size:21px;font-weight:900;letter-spacing:-.4px">Sales Pipeline</div>
        <div style="font-size:13px;color:var(--slate-light);font-weight:600;margin-top:3px">Deals created automatically when customers click your ads</div>
      </div>
      <div style="display:flex;gap:8px">
        <select v-model="platformFilter" class="rv-fi" style="width:auto;padding:7px 11px;font-size:12.5px">
          <option value="">All Platforms</option><option value="facebook">Facebook</option><option value="instagram">Instagram</option>
        </select>
        <button class="rv-btn rv-btn-p rv-btn-sm" @click="showAddDeal=true">+ Add Deal</button>
      </div>
    </div>

    <!-- Pipeline summary -->
    <div class="rv-aov card-reveal" style="animation-delay:.1s">
      <div class="rv-aov-cell"><div class="rv-aov-label">Pipeline Value</div><div class="rv-aov-value">{{ fmtK(summary.value) }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Open Deals</div><div class="rv-aov-value">{{ summary.open }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Hot Leads</div><div class="rv-aov-value">{{ summary.hot }}</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Win Rate</div><div class="rv-aov-value">{{ summary.winRate }}%</div></div>
      <div class="rv-aov-cell"><div class="rv-aov-label">Won This Month</div><div class="rv-aov-value">{{ summary.won }}</div></div>
    </div>

    <!-- Kanban board -->
    <div class="rv-board card-reveal" style="animation-delay:.15s">
      <div v-for="col in columns" :key="col.stage" class="rv-col">
        <div class="rv-col-h" :style="{color:col.color}">
          {{ col.label }}<span class="rv-col-cnt">{{ col.deals.length }}</span>
        </div>
        <div v-for="deal in col.deals.slice(0,3)" :key="deal.id"
          class="rv-deal" :class="deal.stage"
          @click="openDeal(deal)">
          <div class="rv-d-name">{{ deal.customer_name || 'Anonymous' }}</div>
          <div class="rv-d-meta" :style="deal.platform==='instagram'?igStyle:''">
            {{ platformIcon(deal.platform) }} {{ deal.platform==='instagram'?'Instagram':'Facebook' }}
            <span v-if="deal.campaign_name"> &bull; {{ deal.campaign_name }}</span>
          </div>
          <div class="rv-d-meta" style="margin-top:2px">
            <span v-if="deal.estimated_value"><strong style="color:var(--slate)">{{ fmtK(deal.estimated_value) }}</strong> &bull; </span>
            {{ timeAgo(deal.created_at) }}
          </div>
          <div v-if="deal.mpesa_reference" class="rv-d-meta" style="margin-top:3px;color:var(--green);font-weight:800;font-size:10.5px">🔖 {{ deal.mpesa_reference }}</div>
          <div class="rv-d-vel" :class="velClass(deal.velocity)">{{ velIcon(deal.velocity) }} {{ deal.velocity }}</div>
          <div style="display:flex;gap:5px;margin-top:8px" v-if="!['won','lost'].includes(deal.stage)">
            <button class="rv-btn rv-btn-p rv-btn-xs" @click.stop="markWon(deal)" style="font-size:10px;padding:3px 8px">✅ Won</button>
            <button class="rv-btn rv-btn-d rv-btn-xs" @click.stop="markLost(deal)" style="font-size:10px;padding:3px 8px">✗ Lost</button>
          </div>
        </div>
        <div v-if="col.deals.length>3" class="rv-col-foot">{{ col.deals.length-3 }} more deals</div>
        <div v-if="col.stage==='won' && col.deals.length>0" class="rv-col-foot" style="cursor:pointer;color:var(--green)" @click="$emit('nav','history')">View all {{ col.deals.length }} →</div>
      </div>
    </div>

    <!-- Add deal modal -->
    <div v-if="showAddDeal" style="position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px" @click.self="showAddDeal=false">
      <div style="background:var(--card);border-radius:var(--r-xl);width:100%;max-width:480px;box-shadow:var(--shadow-lg);animation:fadeUp .3s ease">
        <div style="padding:20px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between">
          <span style="font-size:16px;font-weight:900">Add Pipeline Deal</span>
          <button @click="showAddDeal=false" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--slate-light);line-height:1">×</button>
        </div>
        <div style="padding:24px;display:flex;flex-direction:column;gap:0">
          <div class="rv-fg"><label class="rv-fl">Customer Name</label><input v-model="newDeal.customer_name" class="rv-fi" placeholder="e.g. Grace W."></div>
          <div class="rv-fg"><label class="rv-fl">Phone Number</label><input v-model="newDeal.customer_phone" class="rv-fi" placeholder="+254700000000"></div>
          <div class="rv-g2">
            <div class="rv-fg"><label class="rv-fl">Platform</label>
              <select v-model="newDeal.platform" class="rv-fs"><option value="facebook">Facebook</option><option value="instagram">Instagram</option><option value="messenger">Messenger</option><option value="organic">Organic</option></select>
            </div>
            <div class="rv-fg"><label class="rv-fl">Estimated Value</label><input
  :value="commaify(newDeal.estimated_value)"
  @input="e => newDeal.estimated_value = stripCommas(e.target.value)"
  class="rv-fi" inputmode="numeric" placeholder="0" autocomplete="off"></div>
          </div>
          <div class="rv-fg"><label class="rv-fl">Notes</label><textarea v-model="newDeal.notes" class="rv-ft" placeholder="Any notes about this lead..."></textarea></div>
        </div>
        <div style="padding:16px 24px;border-top:1px solid var(--border);display:flex;gap:10px;justify-content:flex-end">
          <button class="rv-btn rv-btn-s" @click="showAddDeal=false">Cancel</button>
          <button class="rv-btn rv-btn-p" @click="addDeal" :disabled="addingDeal">
            <span v-if="addingDeal" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
            <span v-else>Add Deal</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'
import { fmtK as _fmtK, fmtFull, fmtNum } from '@/utils/format'
import relativeTime from 'dayjs/plugin/relativeTime'
dayjs.extend(relativeTime)

const emit = defineEmits(['nav','toast'])
const auth = useAuthStore()
const deals = ref([])
const platformFilter = ref('')
const showAddDeal = ref(false)
const addingDeal  = ref(false)
const newDeal     = ref({ customer_name:'', customer_phone:'', platform:'facebook', estimated_value:'', notes:'' })

const COLS = [
  { stage:'new_click',   label:'New Click',   color:'var(--blue)' },
  { stage:'contacted',   label:'Contacted',   color:'var(--amber)' },
  { stage:'interested',  label:'Interested',  color:'var(--purple)' },
  { stage:'negotiating', label:'Negotiating', color:'#DB2777' },
  { stage:'won',         label:'Won',         color:'#16a34a' },
  { stage:'lost',        label:'Lost',        color:'var(--red)' },
]

const filtered = computed(() => platformFilter.value ? deals.value.filter(d=>d.platform===platformFilter.value) : deals.value)
const columns  = computed(() => COLS.map(c => ({ ...c, deals: filtered.value.filter(d=>d.stage===c.stage) })))
const summary  = computed(() => ({
  value:   deals.value.filter(d=>!['won','lost'].includes(d.stage)).reduce((s,d)=>s+(d.estimated_value||0),0),
  open:    deals.value.filter(d=>!['won','lost'].includes(d.stage)).length,
  hot:     deals.value.filter(d=>d.velocity==='hot').length,
  won:     deals.value.filter(d=>d.stage==='won').length,
  winRate: deals.value.length ? Math.round((deals.value.filter(d=>d.stage==='won').length / Math.max(deals.value.filter(d=>['won','lost'].includes(d.stage)).length,1))*100) : 0,
}))

const igStyle = 'background:linear-gradient(135deg,var(--ig1),var(--ig3));-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800'
function platformIcon(p) { return p==='instagram'?'📸':'📘' }
function velClass(v) { return v==='hot'?'vel-hot':v==='warm'?'vel-warm':'vel-cold' }
function velIcon(v)  { return v==='hot'?'🔥 Hot':v==='warm'?'🟡 Warm':'❄️ Cold' }
function timeAgo(dt) { return dt ? dayjs(dt).fromNow() : '' }
function fmtK(v, cur) {
  return _fmtK(v, cur || auth.tenant?.currency || 'KES')
}

async function loadDeals() {
  try { const r = await api.get('/pipeline/deals/'); deals.value = r.data.results || r.data || [] } catch(e) {}
}
function openDeal(deal) { emit('toast', `Deal: ${deal.customer_name||'Anonymous'} — ${deal.stage}`, 'slate') }
async function markWon(deal) {
  try { await api.patch(`/pipeline/deals/${deal.id}/`, { stage:'won' }); deal.stage='won'; emit('toast','Deal marked as Won — log the sale!','green') } catch(e) {}
}
async function markLost(deal) {
  try { await api.patch(`/pipeline/deals/${deal.id}/`, { stage:'lost' }); deal.stage='lost'; emit('toast','Deal marked as Lost','red') } catch(e) {}
}
async function addDeal() {
  addingDeal.value = true
  try {
    const r = await api.post('/pipeline/deals/', { ...newDeal.value, source:'manual', platform: newDeal.value.platform })
    deals.value.unshift(r.data)
    showAddDeal.value = false
    newDeal.value = { customer_name:'', customer_phone:'', platform:'facebook', estimated_value:'', notes:'' }
    emit('toast','Deal added to pipeline','green')
  } catch(e) { emit('toast','Failed to add deal','red') }
  addingDeal.value = false
}
async function deleteDeal(deal) {
  if (!confirm(`Delete deal for ${deal.customer_name || 'this contact'}?
Stage: ${deal.stage}
This cannot be undone.`)) return
  try {
    await api.delete(`/pipeline/deals/${deal.id}/`)
    deals.value = deals.value.filter(d => d.id !== deal.id)
  } catch(e) {}
}

useAutoRefresh(loadDeals, 45000)
</script>
