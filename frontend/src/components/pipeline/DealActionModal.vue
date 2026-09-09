<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="fixed inset-0 bg-slate/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl w-full max-w-[500px] max-h-[90vh] overflow-y-auto shadow-lg">

          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-5 border-b border-border">
            <div>
              <div class="text-[16px] font-black text-slate">{{ deal?.customer_name || 'Anonymous' }}</div>
              <div class="text-[12px] text-slate-light font-semibold mt-0.5">
                {{ deal?.platform }} · {{ deal?.ad_name || '—' }}
              </div>
            </div>
            <button @click="$emit('close')" class="text-slate-light hover:text-slate text-xl leading-none">×</button>
          </div>

          <!-- Body -->
          <div class="px-6 py-5 space-y-4">

            <!-- M-Pesa Reference display -->
            <div v-if="deal?.mpesa_reference" class="bg-green-light border border-green/20 rounded-xl px-4 py-3.5">
              <div class="text-[10px] font-black text-green/60 uppercase tracking-wider mb-1.5">M-Pesa Payment Reference</div>
              <div class="flex items-center justify-between gap-3">
                <div class="text-[22px] font-black text-green tracking-widest">{{ deal.mpesa_reference }}</div>
                <button @click="copyRef" class="flex items-center gap-1.5 bg-green text-white text-xs font-black px-3 py-2 rounded-lg hover:bg-green-dark transition-colors">
                  <i :class="['ti', refCopied ? 'ti-check' : 'ti-clipboard-list']" aria-hidden="true"></i> {{ refCopied ? 'Copied!' : 'Copy' }}
                </button>
              </div>
              <div class="text-[11px] text-green/70 font-semibold mt-2">
                Tell customer: Pay to <strong>{{ deal?.tenant_shortcode || 'your till' }}</strong>, Ref: <strong>{{ deal.mpesa_reference }}</strong>
              </div>
            </div>

            <!-- Payment instructions generator -->
            <div class="border border-border rounded-xl p-4">
              <div class="text-[11px] font-black text-slate-mid uppercase tracking-wide mb-2.5"><i class="ti ti-upload" aria-hidden="true"></i> Send Payment Instructions</div>
              <div class="bg-surface rounded-lg p-3 text-[12.5px] text-slate leading-relaxed mb-3 font-semibold">
                {{ paymentMessage }}
              </div>
              <div class="flex gap-2">
                <button @click="copyInstructions" class="flex-1 text-xs font-black bg-slate text-white py-2 rounded-lg hover:bg-slate/80 transition-colors">
                  <i :class="['ti', instrCopied ? 'ti-check' : 'ti-clipboard-list']" aria-hidden="true"></i> {{ instrCopied ? 'Copied!' : 'Copy Message' }}
                </button>
                <button @click="whatsappShare" class="flex-1 text-xs font-black bg-green text-white py-2 rounded-lg hover:bg-green-dark transition-colors">
                  <i class="ti ti-message-circle" aria-hidden="true"></i> WhatsApp
                </button>
              </div>
            </div>

            <!-- Action selection -->
            <div>
              <label class="block text-[11px] font-black text-slate-mid uppercase tracking-wide mb-2">Action</label>
              <select v-model="action" class="rv-input">
                <option value="won">Mark as Won</option>
                <option value="lost">Mark as Lost</option>
                <option value="contacted">Move to Contacted</option>
                <option value="interested">Move to Interested</option>
                <option value="negotiating">Move to Negotiating</option>
              </select>
            </div>

            <!-- Lost reason -->
            <div v-if="action === 'lost'">
              <label class="block text-[11px] font-black text-slate-mid uppercase tracking-wide mb-2">Reason for Loss</label>
              <input v-model="lostReason" class="rv-input" placeholder="e.g. Price too high, bought elsewhere">
            </div>

            <!-- Won note -->
            <div v-if="action === 'won'" class="bg-green-light border border-green/20 rounded-xl p-4">
              <div class="text-[12px] font-black text-green"><i class="ti ti-circle-check" aria-hidden="true"></i> The sale will sync automatically once this deal is marked Won in Kommo too.</div>
            </div>

            <!-- Notes -->
            <div>
              <label class="rv-label">Notes (optional)</label>
              <textarea v-model="notes" class="rv-input" rows="2" placeholder="Any notes..."></textarea>
            </div>

            <!-- Error -->
            <div v-if="error" class="text-sm font-bold text-red-500 bg-red-light rounded-lg px-4 py-2.5">{{ error }}</div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-border flex gap-3 justify-end">
            <button @click="$emit('close')" class="rv-btn-secondary">Cancel</button>
            <button @click="submit" :disabled="loading" class="rv-btn-primary">
              <span v-if="loading" class="rv-spinner mr-1.5"></span>
              {{ loading ? 'Saving...' : 'Submit' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore, useUIStore } from '@/stores'
import { pipeline as pipelineApi } from '@/api'

const props = defineProps({
  show:      { type: Boolean, default: false },
  deal:      { type: Object, default: null },
  shortcode: { type: String, default: '' },
})

const emit = defineEmits(['close', 'updated'])

const auth    = useAuthStore()
const ui      = useUIStore()

const action        = ref('won')
const lostReason    = ref('')
const notes         = ref('')
const saleAmount    = ref('')
const loading       = ref(false)
const error         = ref('')
const refCopied     = ref(false)
const instrCopied   = ref(false)

// Reset when deal changes
watch(() => props.deal, (d) => {
  if (!d) return
  action.value     = 'won'
  lostReason.value = ''
  notes.value      = ''
  saleAmount.value = d.estimated_value || ''
  error.value      = ''
})

const paymentMessage = computed(() => {
  if (!props.deal) return ''
  const ref  = props.deal.mpesa_reference || '—'
  const till = props.shortcode || 'our till'
  const amt  = saleAmount.value ? ` KES ${Number(saleAmount.value).toLocaleString()}` : ''
  return `Hi! To complete your order, please pay${amt} to ${till}.\nAccount/Reference: ${ref}\n\nOnce paid, we'll confirm immediately. Thank you! <i class="ti ti-mood-smile" aria-hidden="true"></i>`
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const isSimple = ['won', 'lost'].includes(action.value)
    const body = { notes: notes.value }

    if (isSimple) {
      body.action = action.value
      if (action.value === 'lost') body.lost_reason = lostReason.value
      await pipelineApi.action(props.deal.id, body)
    } else {
      body.stage = action.value
      await pipelineApi.advance(props.deal.id, body)
    }

    ui.success(`Deal updated: ${action.value}`)
    emit('updated')
    emit('close')
  } catch (e) {
    error.value = e.response?.data?.message || 'Something went wrong.'
  } finally {
    loading.value = false
  }
}

async function copyRef() {
  await navigator.clipboard.writeText(props.deal?.mpesa_reference || '')
  refCopied.value = true
  setTimeout(() => { refCopied.value = false }, 2000)
}

async function copyInstructions() {
  await navigator.clipboard.writeText(paymentMessage.value)
  instrCopied.value = true
  setTimeout(() => { instrCopied.value = false }, 2000)
}

function whatsappShare() {
  const msg = encodeURIComponent(paymentMessage.value)
  const phone = props.deal?.customer_phone?.replace(/\D/g, '') || ''
  window.open(`https://wa.me/${phone}?text=${msg}`, '_blank')
}
</script>
