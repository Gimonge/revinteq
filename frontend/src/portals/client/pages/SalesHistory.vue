<template>
  <div style="display:flex;flex-direction:column;gap:18px">

    <!-- Header -->
    <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:10px" class="fade-up">
      <div>
        <div style="font-size:21px;font-weight:900;letter-spacing:-.4px">Sales History</div>
        <div style="font-size:13px;color:var(--slate-light);font-weight:600;margin-top:3px">
          {{ sales.length }} sale{{ sales.length!==1?'s':'' }} shown
          <span v-if="totals.total_revenue"> · {{ currency }} {{ Number(totals.total_revenue).toLocaleString('en-KE') }} total</span>
        </div>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="rv-btn rv-btn-s rv-btn-sm" @click="printSales" title="Print filtered results">🖨️ Print</button>
        <button class="rv-btn rv-btn-s rv-btn-sm" @click="exportExcel" :disabled="exporting" title="Export to Excel">
          <span v-if="exporting" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
          <span v-else>📥 Export Excel</span>
        </button>
        <button class="rv-btn rv-btn-p rv-btn-sm" @click="$emit('nav','log')">✏️ Log Sale</button>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="rv-card card-reveal">
      <div class="rv-ch">
        <span class="rv-ct">Filters</span>
        <button v-if="hasActiveFilters" class="rv-btn rv-btn-s rv-btn-xs" @click="clearFilters">✕ Clear all</button>
      </div>
      <div class="rv-cb" style="display:flex;flex-direction:column;gap:12px">
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
          <!-- Search -->
          <div class="rv-fg" style="margin:0">
            <label class="rv-fl">Search</label>
            <input v-model="filters.search" class="rv-fi" placeholder="Product, customer, reference...">
          </div>
          <!-- Platform -->
          <div class="rv-fg" style="margin:0">
            <label class="rv-fl">Platform</label>
            <select v-model="filters.platform" class="rv-fs">
              <option value="">All Platforms</option>
              <option value="facebook">Facebook</option>
              <option value="instagram">Instagram</option>
              <option value="messenger">Messenger</option>
              <option value="organic">Organic / Walk-in</option>
              <option value="referral">Referral</option>
              <option value="other">Other</option>
            </select>
          </div>
          <!-- Payment method -->
          <div class="rv-fg" style="margin:0">
            <label class="rv-fl">Payment Method</label>
            <select v-model="filters.payment_method" class="rv-fs">
              <option value="">All Methods</option>
              <option value="cash">Cash</option>
              <option value="mpesa_manual">M-Pesa</option>
              <option value="mpesa_auto">M-Pesa (Auto)</option>
              <option value="bank_deposit">Bank Deposit</option>
              <option value="eft">EFT</option>
              <option value="rtgs">RTGS</option>
              <option value="standing_order">Standing Order</option>
              <option value="cheque">Cheque</option>
              <option value="card">Card</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
          <!-- Date from -->
          <div class="rv-fg" style="margin:0">
            <label class="rv-fl">Date From</label>
            <input v-model="filters.date_from" class="rv-fi" type="date">
          </div>
          <!-- Date to -->
          <div class="rv-fg" style="margin:0">
            <label class="rv-fl">Date To</label>
            <input v-model="filters.date_to" class="rv-fi" type="date">
          </div>
          <!-- Quick date presets -->
          <div class="rv-fg" style="margin:0">
            <label class="rv-fl">Quick Range</label>
            <div style="display:flex;gap:5px;flex-wrap:wrap;padding-top:2px">
              <button v-for="p in presets" :key="p.label"
                class="rv-btn rv-btn-s rv-btn-xs"
                :style="activePreset===p.label?{background:'var(--green)',color:'#fff'}:{}"
                @click="applyPreset(p)">
                {{ p.label }}
              </button>
            </div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
          <button class="rv-btn rv-btn-p rv-btn-sm" @click="applyFilters" :disabled="loading">
            <span v-if="loading" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
            <span v-else>🔍 Apply Filters</span>
          </button>
          <span v-if="hasActiveFilters" style="font-size:12px;color:var(--slate-mid);font-weight:600">
            Showing filtered results
          </span>
        </div>
      </div>
    </div>

    <!-- Summary tiles (when filtered) -->
    <div v-if="totals.total_sales > 0" class="rv-aov card-reveal">
      <div class="rv-aov-cell">
        <div class="rv-aov-label">Total Sales</div>
        <div class="rv-aov-value">{{ totals.total_sales }}</div>
      </div>
      <div class="rv-aov-cell">
        <div class="rv-aov-label">Total Revenue</div>
        <div class="rv-aov-value">{{ fmtK(totals.total_revenue) }}</div>
      </div>
      <div class="rv-aov-cell">
        <div class="rv-aov-label">Avg. Order Value</div>
        <div class="rv-aov-value">{{ fmtK(totals.avg_order_value) }}</div>
      </div>
      <div class="rv-aov-cell">
        <div class="rv-aov-label">M-Pesa</div>
        <div class="rv-aov-value">{{ fmtK(totals.mpesa_total) }}</div>
      </div>
      <div class="rv-aov-cell">
        <div class="rv-aov-label">Cash</div>
        <div class="rv-aov-value">{{ fmtK(totals.cash_total) }}</div>
      </div>
    </div>

    <!-- Results table -->
    <div class="rv-card card-reveal" id="sales-print-area">
      <!-- Print header (only visible when printing) -->
      <div class="rv-print-header" v-show="showPrintHeader">
        <div style="font-size:18px;font-weight:900">{{ auth.tenant?.name }} — Sales Report</div>
        <div style="font-size:12px;color:#666;margin-top:4px">
          {{ printDateRange }} · Printed {{ printDate }}
        </div>
      </div>

      <div v-if="loading" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else class="rv-tw">
        <table class="rv-table" id="sales-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Customer</th>
              <th>Product / Service</th>
              <th>Amount</th>
              <th>Platform</th>
              <th>Payment</th>
              <th>Reference</th>
              <th>Notes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in sales" :key="s.id">
              <td style="white-space:nowrap">{{ formatDate(s.sale_date) }}</td>
              <td>
                <div v-if="s.customer_name" style="font-weight:700;font-size:12.5px">{{ s.customer_name }}</div>
                <div v-if="s.customer_phone" style="font-size:11.5px;color:var(--slate-mid)">{{ s.customer_phone }}</div>
                <span v-if="!s.customer_name && !s.customer_phone" style="color:var(--slate-light);font-size:12px">—</span>
              </td>
              <td><strong>{{ s.product_name }}</strong></td>
              <td style="white-space:nowrap">
                <strong>{{ currency }} {{ Number(s.amount).toLocaleString('en-KE') }}</strong>
              </td>
              <td>
                <span class="rv-badge"
                  :class="s.platform_source==='instagram'?'rv-big':s.platform_source==='facebook'?'rv-bb':s.platform_source==='organic'?'rv-bg':'rv-bgy'"
                  style="font-size:10px">
                  {{ platformLabel(s.platform_source) }}
                </span>
              </td>
              <td style="white-space:nowrap">
                <span class="rv-badge rv-bgy" style="font-size:10px">{{ payLabel(s.payment_method) }}</span>
              </td>
              <td style="font-family:monospace;font-size:11.5px;color:var(--slate-mid)">
                {{ s.payment_reference || '—' }}
              </td>
              <td style="font-size:12px;color:var(--slate-mid);max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                {{ s.notes || '—' }}
              </td>
              <td style="white-space:nowrap" @click.stop>
                <div style="display:flex;gap:4px">
                  <button class="rv-btn rv-btn-b rv-btn-xs" @click="openEditSale(s)" title="Edit">✏️</button>
                  <button class="rv-btn rv-btn-d rv-btn-xs" @click="deleteSale(s)" title="Delete">🗑️</button>
                </div>
              </td>
            </tr>
            <tr v-if="sales.length===0">
              <td colspan="8" style="text-align:center;color:var(--slate-light);padding:48px">
                <div style="font-size:32px;margin-bottom:12px">📋</div>
                <div style="font-weight:800;font-size:14px;margin-bottom:4px">No sales found</div>
                <div style="font-size:12.5px">{{ hasActiveFilters ? 'Try adjusting your filters' : 'Log your first sale to get started' }}</div>
              </td>
            </tr>
          </tbody>
          <tfoot v-if="sales.length > 0">
            <tr>
              <td colspan="3"><strong>Total — {{ sales.length }} sale{{ sales.length!==1?'s':'' }}</strong></td>
              <td><strong>{{ currency }} {{ Number(totals.total_revenue||0).toLocaleString('en-KE') }}</strong></td>
              <td colspan="4"></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

  </div>
  <!-- Edit Sale Modal -->
  <div v-if="editSale" style="position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;display:flex;align-items:center;justify-content:center;padding:16px">
    <div class="rv-card" style="width:100%;max-width:520px;max-height:90vh;overflow-y:auto">
      <div class="rv-ch">
        <div class="rv-ct">Edit Sale</div>
        <button @click="editSale=null" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--slate-light)">✕</button>
      </div>
      <div class="rv-cb" style="display:flex;flex-direction:column;gap:12px">
        <div class="rv-fg" style="margin:0"><label class="rv-fl">Customer Name</label><input v-model="editForm.customer_name" class="rv-fi"></div>
        <div class="rv-fg" style="margin:0"><label class="rv-fl">Customer Phone</label><input v-model="editForm.customer_phone" class="rv-fi"></div>
        <div class="rv-fg" style="margin:0"><label class="rv-fl">Product / Service *</label><input v-model="editForm.product_name" class="rv-fi"></div>
        <div class="rv-g2">
          <div class="rv-fg" style="margin:0"><label class="rv-fl">Amount *</label>
            <input :value="commaify(editForm.amount)" @input="e=>editForm.amount=stripCommas(e.target.value)" class="rv-fi" inputmode="numeric">
          </div>
          <div class="rv-fg" style="margin:0"><label class="rv-fl">Sale Date *</label><input v-model="editForm.sale_date" class="rv-fi" type="date"></div>
        </div>
        <div class="rv-g2">
          <div class="rv-fg" style="margin:0"><label class="rv-fl">Payment Method</label>
            <select v-model="editForm.payment_method" class="rv-fs">
              <option value="cash">Cash</option><option value="mpesa_manual">M-Pesa</option>
              <option value="bank_deposit">Bank Deposit</option><option value="eft">EFT</option>
              <option value="rtgs">RTGS</option><option value="standing_order">Standing Order</option>
              <option value="cheque">Cheque</option><option value="card">Card</option><option value="other">Other</option>
            </select>
          </div>
          <div class="rv-fg" style="margin:0"><label class="rv-fl">Platform</label>
            <select v-model="editForm.platform_source" class="rv-fs">
              <option value="facebook">Facebook</option><option value="instagram">Instagram</option>
              <option value="organic">Organic</option><option value="referral">Referral</option><option value="other">Other</option>
            </select>
          </div>
        </div>
        <div class="rv-fg" style="margin:0"><label class="rv-fl">Reference</label><input v-model="editForm.payment_reference" class="rv-fi"></div>
        <div class="rv-fg" style="margin:0"><label class="rv-fl">Notes</label><input v-model="editForm.notes" class="rv-fi"></div>
        <div style="display:flex;gap:8px;margin-top:4px">
          <button class="rv-btn rv-btn-p" @click="saveEditSale" :disabled="savingEdit">
            <span v-if="savingEdit" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
            <span v-else>💾 Save Changes</span>
          </button>
          <button class="rv-btn rv-btn-s" @click="editSale=null">Cancel</button>
        </div>
      </div>
    </div>
  </div>

</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import api from '@/api'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'
import { fmtK as _fmtK, fmtFull, fmtNum, commaify, stripCommas } from '@/utils/format'

const emit     = defineEmits(['nav', 'toast'])
const auth     = useAuthStore()
const currency = computed(() => auth.tenant?.currency || 'KES')

const sales    = ref([])
const loading  = ref(true)
const exporting        = ref(false)
const showPrintHeader  = ref(false)
const totals   = ref({})

const filters = ref({
  search:         '',
  platform:       '',
  payment_method: '',
  date_from:      '',
  date_to:        '',
})

const activePreset = ref('')

const presets = [
  { label:'Today',      from: dayjs().format('YYYY-MM-DD'),                   to: dayjs().format('YYYY-MM-DD') },
  { label:'This Week',  from: dayjs().startOf('week').format('YYYY-MM-DD'),   to: dayjs().format('YYYY-MM-DD') },
  { label:'This Month', from: dayjs().startOf('month').format('YYYY-MM-DD'),  to: dayjs().format('YYYY-MM-DD') },
  { label:'Last Month', from: dayjs().subtract(1,'month').startOf('month').format('YYYY-MM-DD'), to: dayjs().subtract(1,'month').endOf('month').format('YYYY-MM-DD') },
  { label:'Last 7d',    from: dayjs().subtract(6,'days').format('YYYY-MM-DD'), to: dayjs().format('YYYY-MM-DD') },
  { label:'Last 30d',   from: dayjs().subtract(29,'days').format('YYYY-MM-DD'),to: dayjs().format('YYYY-MM-DD') },
]

function applyPreset(p) {
  filters.value.date_from = p.from
  filters.value.date_to   = p.to
  activePreset.value       = p.label
  applyFilters()
}

const hasActiveFilters = computed(() =>
  filters.value.search || filters.value.platform ||
  filters.value.payment_method || filters.value.date_from || filters.value.date_to
)

const printDateRange = computed(() => {
  if (filters.value.date_from && filters.value.date_to)
    return `${dayjs(filters.value.date_from).format('D MMM YYYY')} – ${dayjs(filters.value.date_to).format('D MMM YYYY')}`
  if (filters.value.date_from) return `From ${dayjs(filters.value.date_from).format('D MMM YYYY')}`
  return 'All time'
})
const printDate = computed(() => dayjs().format('D MMM YYYY h:mm A'))

function fmtK(v, cur) {
  return _fmtK(v, cur || auth.tenant?.currency || 'KES')
}
function payLabel(m) {
  return {
    mpesa_manual:'M-Pesa', mpesa_auto:'M-Pesa (Auto)',
    cash:'Cash', bank_deposit:'Bank', eft:'EFT', rtgs:'RTGS',
    standing_order:'Standing Order', cheque:'Cheque', card:'Card', other:'Other'
  }[m] || m
}
function platformLabel(p) {
  return { facebook:'Facebook', instagram:'Instagram', messenger:'Messenger', organic:'Organic', referral:'Referral', other:'Other' }[p] || p
}
function formatDate(d) { return d ? dayjs(d).format('D MMM YYYY') : '—' }

function clearFilters() {
  filters.value = { search:'', platform:'', payment_method:'', date_from:'', date_to:'' }
  activePreset.value = ''
  loadSales()
}

async function applyFilters() { await loadSales() }

async function loadSales() {
  loading.value = true
  try {
    const p = new URLSearchParams()
    if (filters.value.search)         p.set('search',         filters.value.search)
    if (filters.value.platform)       p.set('platform',       filters.value.platform)
    if (filters.value.payment_method) p.set('payment_method', filters.value.payment_method)
    if (filters.value.date_from)      p.set('date_from',      filters.value.date_from)
    if (filters.value.date_to)        p.set('date_to',        filters.value.date_to)
    const r = await api.get(`/sales/?${p}&page_size=500`)
    sales.value  = r.data.results || r.data || []
    totals.value = r.data.totals  || {}
  } catch(e) {}
  loading.value = false
}

// ── Print ─────────────────────────────────────────────────────
async function printSales() {
  showPrintHeader.value = true
  await nextTick()               // Wait for Vue to render the header
  window.print()
  showPrintHeader.value = false  // Reset after print dialog closes
}

// ── Export Excel ──────────────────────────────────────────────
async function exportExcel() {
  exporting.value = true
  try {
    // Build CSV content (opens in Excel)
    const headers = ['Date','Customer Name','Customer Phone','Product / Service','Amount','Platform','Payment Method','Reference','Notes']
    const rows = sales.value.map(s => [
      formatDate(s.sale_date),
      s.customer_name  || '',
      s.customer_phone || '',
      s.product_name,
      Number(s.amount),
      platformLabel(s.platform_source),
      payLabel(s.payment_method),
      s.payment_reference || '',
      (s.notes || '').replace(/,/g, ' '),
    ])

    // Add totals row
    rows.push([])
    rows.push(['TOTAL','','','',Number(totals.value.total_revenue||0),'','','',''])

    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${String(cell).replace(/"/g,'""')}"`).join(','))
      .join('\n')

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')

    const tenant = auth.tenant?.name?.replace(/\s+/g,'-') || 'Sales'
    const dateStr = filters.value.date_from && filters.value.date_to
      ? `${filters.value.date_from}_to_${filters.value.date_to}`
      : dayjs().format('YYYY-MM-DD')
    a.href     = url
    a.download = `${tenant}-Sales-${dateStr}.csv`
    a.click()
    URL.revokeObjectURL(url)
    emit('toast', `Exported ${sales.value.length} sales to Excel`, 'green')
  } catch(e) {
    emit('toast', 'Export failed', 'red')
  }
  exporting.value = false
}

// ── Edit / Delete ─────────────────────────────────────────────
const editSale   = ref(null)
const editForm   = ref({})
const savingEdit = ref(false)

function openEditSale(s) {
  editSale.value = s
  editForm.value = {
    customer_name:     s.customer_name || '',
    customer_phone:    s.customer_phone || '',
    product_name:      s.product_name,
    amount:            s.amount,
    sale_date:         s.sale_date,
    payment_method:    s.payment_method,
    payment_reference: s.payment_reference || '',
    platform_source:   s.platform_source,
    notes:             s.notes || '',
  }
}

async function saveEditSale() {
  if (!editForm.value.product_name || !editForm.value.amount) return
  savingEdit.value = true
  try {
    await api.patch(`/sales/${editSale.value.id}/`, editForm.value)
    emit('toast', 'Sale updated', 'green')
    editSale.value = null
    await loadSales()
  } catch(e) { emit('toast', 'Failed to update', 'red') }
  savingEdit.value = false
}

async function deleteSale(s) {
  if (!confirm(`Delete this sale?
${s.product_name} — ${currency.value} ${Number(s.amount).toLocaleString()}
This cannot be undone.`)) return
  try {
    await api.delete(`/sales/${s.id}/`)
    sales.value = sales.value.filter(x => x.id !== s.id)
    emit('toast', 'Sale deleted', 'green')
  } catch(e) { emit('toast', 'Failed to delete', 'red') }
}

useAutoRefresh(loadSales, 60000)
</script>

<style>
@media print {
  /* Hide navigation and UI chrome */
  .rv-sidebar,
  .rv-topbar,
  .rv-burger,
  .rv-toast      { display: none !important; }

  /* Remove main margin (sidebar is hidden) */
  .rv-main       { margin-left: 0 !important; }

  /* Hide everything on the page EXCEPT the print area card */
  .rv-scroll > *                  { display: none !important; }
  .rv-scroll > #sales-print-area  { display: block !important; }

  /* Table styles for print */
  #sales-print-area  { box-shadow: none !important; border: 1px solid #ccc !important; }
  .rv-print-header   { margin-bottom: 14px; padding-bottom: 10px; border-bottom: 2px solid #222; }
  .rv-tw             { overflow: visible !important; }
  .rv-table          { font-size: 10.5px !important; width: 100% !important; min-width: 0 !important; }
  .rv-table thead th {
    background: #f0f0f0 !important; color: #333 !important;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  .rv-table tfoot td {
    background: #e8f5ee !important;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  .rv-badge { border: 1px solid #999 !important; background: none !important; color: #333 !important; }
  @page { margin: 12mm; size: A4 landscape; }
}
</style>
