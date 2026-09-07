<template>
  <div style="display:flex;flex-direction:column;gap:20px" class="fade-up">
    <div class="rv-page-header">
      <div>
        <div class="rv-page-title">SMS Setup</div>
        <div class="rv-page-sub">Africa's Talking configuration per client</div>
      </div>
    </div>

    <div class="rv-card card-reveal">
      <div class="rv-ch"><div class="rv-ct">SMS Status by Client</div></div>
      <div v-if="loading" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else class="rv-tw">
        <table class="rv-table">
          <thead>
            <tr>
              <th>Client</th><th>AT Username</th><th>Sender ID</th>
              <th>Balance</th><th>Status</th><th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in tenants" :key="t.id">
              <td><strong>{{ t.name }}</strong></td>
              <td>
                <span v-if="t.sms_config">{{ t.sms_config.username }}</span>
                <span v-else style="color:var(--slate-light)">—</span>
              </td>
              <td>
                <span v-if="t.sms_config && t.sms_config.sender_id">{{ t.sms_config.sender_id }}</span>
                <span v-else style="color:var(--slate-light)">—</span>
              </td>
              <td>
                <span v-if="t.sms_config">KES {{ t.sms_config.credit_balance || '0.00' }}</span>
                <span v-else style="color:var(--slate-light)">—</span>
              </td>
              <td>
                <span v-if="t.sms_config && t.sms_config.is_active" class="rv-badge rv-bg">Active</span>
                <span v-else class="rv-badge rv-bgy">Not configured</span>
              </td>
              <td>
                <button class="rv-btn rv-btn-s rv-btn-xs" @click="$emit('open-client', t)">Configure →</button>
              </td>
            </tr>
            <tr v-if="tenants.length===0">
              <td colspan="6" style="text-align:center;color:var(--slate-light);padding:32px">No clients yet</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

defineEmits(['open-client'])
const tenants = ref([])
const loading = ref(true)

async function loadData() {
  loading.value = true
  try {
    const r = await api.get('/tenants/')
    const list = r.data.results || r.data || []
    for (const t of list) {
      try {
        const sc = await api.get(`/sms/config/?tenant=${t.id}`)
        t.sms_config = sc.data || null
      } catch(e) {
        t.sms_config = null
      }
    }
    tenants.value = list
  } catch(e) {}
  loading.value = false
}
useAutoRefresh(loadData, 120000)
</script>
