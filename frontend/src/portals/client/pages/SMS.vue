<template>
  <div style="display:flex;flex-direction:column;gap:18px">
    <div style="display:flex;align-items:flex-start;justify-content:space-between" class="fade-up">
      <div><div style="font-size:21px;font-weight:900;letter-spacing:-.4px">SMS</div><div style="font-size:13px;color:var(--slate-light);font-weight:600;margin-top:3px">Send messages via Africa's Talking</div></div>
      <button class="rv-btn rv-btn-p rv-btn-sm" @click="showCompose=true">✉️ New Message</button>
    </div>

    <div v-if="!smsConfigured" class="rv-al rv-al-a card-reveal">⚠️ SMS is not configured for your account. Contact your Gimsc admin to set up Africa's Talking credentials.</div>

    <div v-else>
      <!-- Stats -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px">
        <div class="rv-sc card-reveal"><div class="rv-sc-label">Sent This Month</div><div class="rv-sc-value">{{ stats.sent }}</div></div>
        <div class="rv-sc b card-reveal" style="animation-delay:.05s"><div class="rv-sc-label">Delivered</div><div class="rv-sc-value">{{ stats.delivered }}</div></div>
        <div class="rv-sc r card-reveal" style="animation-delay:.1s"><div class="rv-sc-label">Failed</div><div class="rv-sc-value">{{ stats.failed }}</div></div>
        <div class="rv-sc a card-reveal" style="animation-delay:.15s"><div class="rv-sc-label">AT Credit Balance</div><div class="rv-sc-value">{{ stats.balance }}</div></div>
      </div>

      <!-- Message history -->
      <div class="rv-card card-reveal" style="animation-delay:.2s">
        <div class="rv-ch"><div class="rv-ct">Message History</div></div>
        <div v-if="loading" style="padding:32px;text-align:center"><span class="rv-spin"></span></div>
        <div v-else class="rv-tw">
          <table class="rv-table">
            <thead><tr><th>Recipient</th><th>Message</th><th>Type</th><th>Status</th><th>Cost</th><th>Sent</th></tr></thead>
            <tbody>
              <tr v-for="m in messages" :key="m.id">
                <td>{{ m.recipient_number }}</td>
                <td style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ m.message }}</td>
                <td><span class="rv-badge rv-bgy">{{ m.source }}</span></td>
                <td><span class="rv-badge" :class="statusBadge(m.status)">{{ m.status }}</span></td>
                <td>KES {{ m.cost || '0' }}</td>
                <td style="white-space:nowrap">{{ formatDate(m.created_at) }}</td>
              </tr>
              <tr v-if="messages.length===0"><td colspan="6" style="text-align:center;color:var(--slate-light);padding:32px">No messages sent yet</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Compose modal -->
    <div v-if="showCompose" style="position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px" @click.self="showCompose=false">
      <div style="background:var(--card);border-radius:var(--r-xl);width:100%;max-width:480px;box-shadow:var(--shadow-lg);animation:fadeUp .3s ease">
        <div style="padding:20px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between">
          <span style="font-size:16px;font-weight:900">Send SMS</span>
          <button @click="showCompose=false" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--slate-light)">×</button>
        </div>
        <div style="padding:24px">
          <div class="rv-fg"><label class="rv-fl">Recipient Number *</label><input v-model="compose.recipient" class="rv-fi" placeholder="+254700000000"></div>
          <div class="rv-fg"><label class="rv-fl">Message *</label><textarea v-model="compose.message" class="rv-ft" style="min-height:100px" placeholder="Type your message..."></textarea><div style="font-size:11px;color:var(--slate-light);margin-top:4px;font-weight:600;text-align:right">{{ compose.message.length }}/160 chars</div></div>
          <div v-if="sendError" class="rv-al rv-al-r">{{ sendError }}</div>
        </div>
        <div style="padding:16px 24px;border-top:1px solid var(--border);display:flex;gap:10px;justify-content:flex-end">
          <button class="rv-btn rv-btn-s" @click="showCompose=false">Cancel</button>
          <button class="rv-btn rv-btn-p" @click="sendSMS" :disabled="sending">
            <span v-if="sending" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
            <span v-else>📱 Send</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import dayjs from 'dayjs'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

const emit = defineEmits(['toast'])
const messages = ref([]), loading = ref(true)
const smsConfigured = ref(true), showCompose = ref(false), sending = ref(false)
const sendError = ref('')
const compose = ref({ recipient:'', message:'' })
const stats = ref({ sent:0, delivered:0, failed:0, balance:'KES —' })

function statusBadge(s) { return { sent:'rv-bg', delivered:'rv-bg', failed:'rv-br', queued:'rv-bgy' }[s]||'rv-bgy' }
function formatDate(d) { return d ? dayjs(d).format('D MMM h:mm A') : '—' }

async function loadData() {
  loading.value = true
  try {
    const r = await api.get('/sms/messages/')
    messages.value = r.data.results || r.data || []
    stats.value.sent      = messages.value.filter(m=>m.status!=='failed').length
    stats.value.delivered = messages.value.filter(m=>m.status==='delivered').length
    stats.value.failed    = messages.value.filter(m=>m.status==='failed').length
  } catch(e) {}
  try { const r = await api.get('/sms/config/'); if (r.data?.credit_balance) stats.value.balance = `KES ${r.data.credit_balance}` } catch(e) { smsConfigured.value = false }
  loading.value = false
}
async function sendSMS() {
  if (!compose.value.recipient || !compose.value.message) { sendError.value = 'Recipient and message are required.'; return }
  sending.value = true; sendError.value = ''
  try {
    await api.post('/sms/send/', compose.value)
    emit('toast','SMS sent!','green')
    showCompose.value = false
    compose.value = { recipient:'', message:'' }
    loadData()
  } catch(e) { sendError.value = e.response?.data?.message || 'Failed to send SMS.' }
  sending.value = false
}
useAutoRefresh(loadData, 60000)
</script>
