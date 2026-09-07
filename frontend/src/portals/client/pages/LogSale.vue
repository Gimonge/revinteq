<template>
  <div style="display:flex;flex-direction:column;gap:18px">
    <div class="fade-up">
      <div style="font-size:21px;font-weight:900;letter-spacing:-.4px">Log a Sale</div>
      <div style="font-size:13px;color:var(--slate-light);font-weight:600;margin-top:3px">Under 10 seconds on mobile &bull; All payment methods supported</div>
    </div>

    <div class="rv-card card-reveal" style="max-width:600px">
      <div class="rv-ch"><span class="rv-ct">New Sale</span></div>
      <div class="rv-cb">

        <div v-if="success" class="rv-al rv-al-g" style="margin-bottom:16px">
          ✅ Sale logged! {{ successMsg }}
        </div>
        <div v-if="error" class="rv-al rv-al-r" style="margin-bottom:16px">{{ error }}</div>

        <!-- Customer info -->
        <div class="rv-sec-lbl">👤 Customer (Optional)</div>
        <div class="rv-g2">
          <div class="rv-fg">
            <label class="rv-fl">Customer Name</label>
            <input v-model="form.customer_name" class="rv-fi" placeholder="e.g. Jane Wanjiku">
          </div>
          <div class="rv-fg">
            <label class="rv-fl">Phone Number</label>
            <input v-model="form.customer_phone" class="rv-fi" type="tel" placeholder="e.g. 0712345678">
          </div>
        </div>

        <!-- Sale details -->
        <div class="rv-sec-lbl">🛍️ Sale Details</div>
        <div class="rv-fg">
          <label class="rv-fl">Product / Service *</label>
          <input v-model="form.product_name" class="rv-fi" placeholder="e.g. Blue Summer Dress (Size M)">
        </div>
        <div class="rv-g2">
          <div class="rv-fg">
            <label class="rv-fl">Amount ({{ currency }}) *</label>
            <input
              :value="displayAmount"
              @input="onAmountInput"
              @blur="onAmountBlur"
              class="rv-fi"
              inputmode="numeric"
              placeholder="0"
              autocomplete="off"
            >
          </div>
          <div class="rv-fg">
            <label class="rv-fl">Sale Date *</label>
            <input v-model="form.sale_date" class="rv-fi" type="date">
          </div>
        </div>

        <!-- Payment -->
        <div class="rv-sec-lbl">💳 Payment</div>
        <div class="rv-g2">
          <div class="rv-fg">
            <label class="rv-fl">Payment Method *</label>
            <select v-model="form.payment_method" class="rv-fs" @change="onPaymentMethodChange">
              <option value="cash">Cash</option>
              <option value="mpesa_manual">M-Pesa</option>
              <option value="bank_deposit">Bank Deposit</option>
              <option value="eft">EFT</option>
              <option value="rtgs">RTGS</option>
              <option value="standing_order">Standing Order</option>
              <option value="cheque">Cheque</option>
              <option value="card">Card</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div v-if="showRef" class="rv-fg">
            <label class="rv-fl">{{ refLabel }}</label>
            <input v-model="form.payment_reference" class="rv-fi" :placeholder="refPlaceholder">
          </div>
        </div>

        <!-- Attribution -->
        <div class="rv-sec-lbl">📊 Attribution</div>
        <div class="rv-g2">
          <div class="rv-fg">
            <label class="rv-fl">Platform Source</label>
            <select v-model="form.platform_source" class="rv-fs" @change="loadCampaigns">
              <option value="facebook">Facebook</option>
              <option value="instagram">Instagram</option>
              <option value="messenger">Messenger</option>
              <option value="organic">Organic / Walk-in</option>
              <option value="referral">Referral</option>
              <option value="other">Other</option>
            </select>
          </div>
          <!-- Campaign Attribution -->
          <div class="rv-fg">
            <label class="rv-fl">Ad Campaign (optional)</label>
            <select v-model="form.campaign_id" class="rv-fs">
              <option value="">— Not from a campaign —</option>
              <option v-for="c in activeCampaigns" :key="c.id" :value="c.id">
                {{ c.name }} · {{ c.platform }} · {{ c.account_name }}
              </option>
            </select>
          </div>

          <div class="rv-fg">
            <label class="rv-fl">Notes</label>
            <input v-model="form.notes" class="rv-fi" placeholder="Optional notes">
          </div>
        </div>

        <div style="display:flex;gap:10px;margin-top:8px">
          <button class="rv-btn rv-btn-p" @click="logSale" :disabled="saving">
            <span v-if="saving" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
            <span v-else>💾 Log Sale</span>
          </button>
          <button class="rv-btn rv-btn-s" @click="clearForm">Clear</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { commaify, stripCommas } from '@/utils/format'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'

const emit     = defineEmits(['toast'])
const auth     = useAuthStore()
const currency = computed(() => auth.tenant?.currency || 'KES')
const saving          = ref(false)
const activeCampaigns = ref([])
const success  = ref(false)
const successMsg = ref('')
const error    = ref('')

const defaultForm = () => ({
  customer_name:     '',
  customer_phone:    '',
  product_name:      '',
  amount:            '',
  sale_date:         dayjs().format('YYYY-MM-DD'),
  payment_method:    'cash',
  payment_reference: '',
  platform_source:   'facebook',
  notes:             '',
})

const form = ref(defaultForm())

// ── Comma-formatted amount input ─────────────────────────────
const displayAmount = computed(() => commaify(form.value.amount))

function onAmountInput(e) {
  const raw = stripCommas(e.target.value)
  form.value.amount = raw === '' ? '' : raw
}

function onAmountBlur(e) {
  // Ensure clean number on blur
  const raw = stripCommas(e.target.value)
  if (raw && !isNaN(Number(raw))) {
    form.value.amount = raw
  }
}

const REF_MAP = {
  mpesa_manual:   ['M-Pesa Transaction Code',    'e.g. QK47XY8Z21'],
  bank_deposit:   ['Bank Reference Number',      'Enter reference'],
  eft:            ['EFT Reference',              'Enter reference'],
  rtgs:           ['RTGS Reference',             'Enter reference'],
  standing_order: ['Standing Order Reference',   'Enter reference'],
  cheque:         ['Cheque Number',              'Enter cheque number'],
  card:           ['Card Receipt Number',        'Enter receipt'],
}
const showRef        = computed(() => !!REF_MAP[form.value.payment_method])
const refLabel       = computed(() => REF_MAP[form.value.payment_method]?.[0] || '')
const refPlaceholder = computed(() => REF_MAP[form.value.payment_method]?.[1] || '')

function onPaymentMethodChange() { form.value.payment_reference = '' }

async function loadCampaigns() {
  try {
    const r = await api.get('/meta/active-campaigns/')
    activeCampaigns.value = r.data || []
  } catch(e) { activeCampaigns.value = [] }
}

onMounted(loadCampaigns)

async function logSale() {
  error.value = ''
  if (!form.value.product_name.trim()) { error.value = 'Product name is required.'; return }
  if (!form.value.amount || Number(form.value.amount) <= 0) { error.value = 'Amount must be greater than zero.'; return }
  saving.value = true
  success.value = false
  try {
    await api.post('/sales/', form.value)
    const customerInfo = form.value.customer_name ? ` for ${form.value.customer_name}` : ''
    successMsg.value = `${currency.value} ${Number(form.value.amount).toLocaleString('en-KE')} — "${form.value.product_name}"${customerInfo}`
    success.value = true
    emit('toast', 'Sale logged successfully!', 'green')
    clearForm()
  } catch(e) {
    const d = e.response?.data
    if (d && typeof d === 'object') {
      const msgs = Object.values(d).flat().join(' ')
      error.value = msgs || 'Failed to log sale.'
    } else {
      error.value = 'Failed to log sale. Please try again.'
    }
  }
  saving.value = false
}

function clearForm() {
  form.value = defaultForm()
  error.value = ''
}
</script>
