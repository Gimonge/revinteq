<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="fixed inset-0 bg-slate/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl w-full max-w-[460px] shadow-lg">
          <div class="flex items-center justify-between px-6 py-5 border-b border-border">
            <div class="text-[15px] font-black text-slate">Add Pipeline Deal</div>
            <button @click="$emit('close')" class="text-slate-light hover:text-slate text-xl">×</button>
          </div>
          <div class="px-6 py-5 space-y-4">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="rv-label">Customer Name</label>
                <input v-model="form.customer_name" class="rv-input" placeholder="Optional">
              </div>
              <div>
                <label class="rv-label">Customer Phone</label>
                <input v-model="form.customer_phone" class="rv-input" placeholder="+254...">
              </div>
            </div>
            <div>
              <label class="rv-label">Channel / Platform *</label>
              <select v-model="form.platform" class="rv-input">
                <option value="facebook">Facebook (Click to WhatsApp / Messenger)</option>
                <option value="instagram">Instagram (Click to IG DM)</option>
                <option value="messenger">Facebook Messenger DM</option>
                <option value="organic">Organic / Walk-in / Referral</option>
              </select>
            </div>
            <div>
              <label class="rv-label">Source Ad (optional)</label>
              <select v-model="form.campaign_id" class="rv-input">
                <option value="">— Select campaign —</option>
                <option v-for="c in campaigns" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="rv-label">Estimated Value (KES)</label>
                <input v-model="form.estimated_value" type="number" class="rv-input" placeholder="Optional">
              </div>
              <div>
                <label class="rv-label">Initial Stage</label>
                <select v-model="form.stage" class="rv-input">
                  <option value="new_click">New Click</option>
                  <option value="contacted">Contacted</option>
                </select>
              </div>
            </div>
            <div>
              <label class="rv-label">Notes</label>
              <textarea v-model="form.notes" class="rv-input" rows="2" placeholder="Any context..."></textarea>
            </div>
            <div v-if="error" class="text-sm font-bold text-red-500 bg-red-light rounded-lg px-4 py-2.5">{{ error }}</div>
          </div>
          <div class="px-6 py-4 border-t border-border flex gap-3 justify-end">
            <button @click="$emit('close')" class="rv-btn-secondary">Cancel</button>
            <button @click="submit" :disabled="loading" class="rv-btn-primary">
              <span v-if="loading" class="rv-spinner mr-1.5"></span>
              Add Deal
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { pipeline as pipelineApi, meta as metaApi } from '@/api'
import { useUIStore } from '@/stores'

defineProps({ show: { type: Boolean, default: false } })
const emit = defineEmits(['close', 'created'])

const ui       = useUIStore()
const loading  = ref(false)
const error    = ref('')
const campaigns = ref([])

const form = ref({
  customer_name:   '',
  customer_phone:  '',
  platform:        'facebook',
  campaign_id:     '',
  estimated_value: '',
  stage:           'new_click',
  notes:           '',
  source:          'manual',
})

async function submit() {
  loading.value = true
  error.value   = ''
  try {
    await pipelineApi.create({
      ...form.value,
      estimated_value: form.value.estimated_value || null,
      campaign:        form.value.campaign_id || null,
    })
    ui.success('Pipeline deal created. M-Pesa reference generated.')
    emit('created')
    emit('close')
  } catch (e) {
    error.value = e.response?.data?.message || 'Failed to create deal.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await metaApi.campaigns()
    campaigns.value = data
  } catch { /* not critical */ }
})
</script>
