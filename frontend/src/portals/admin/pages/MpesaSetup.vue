<template>
  <div style="display:flex;flex-direction:column;gap:20px" class="fade-up">
    <div class="rv-page-header">
      <div>
        <div class="rv-page-title">M-Pesa Setup</div>
        <div class="rv-page-sub">Configure Daraja API credentials per client</div>
      </div>
    </div>

    <div class="rv-al rv-al-b card-reveal">
      ℹ️ Select a client from the Clients page to configure their M-Pesa credentials, or use the Client Detail page directly.
    </div>

    <div class="rv-card card-reveal">
      <div class="rv-ch"><div class="rv-ct">M-Pesa Status by Client</div></div>
      <div v-if="loading" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else class="rv-tw">
        <table class="rv-table">
          <thead>
            <tr>
              <th>Client</th><th>Environment</th><th>Type</th>
              <th>Shortcode</th><th>C2B URLs</th><th>Status</th><th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in tenants" :key="t.id">
              <td><strong>{{ t.name }}</strong></td>
              <td>
                <span v-if="t.mpesa_config" class="rv-badge" :class="t.mpesa_config.environment==='production'?'rv-bg':'rv-ba'">
                  {{ t.mpesa_config.environment==='production' ? 'Production' : 'Sandbox' }}
                </span>
                <span v-else style="color:var(--slate-light)">—</span>
              </td>
              <td>{{ t.mpesa_config ? (t.mpesa_config.shortcode_type==='till' ? 'Till' : 'Paybill') : '—' }}</td>
              <td>
                <span v-if="t.mpesa_config?.shortcode">{{ t.mpesa_config.shortcode }}</span>
                <span v-else style="color:var(--slate-light)">Not configured</span>
              </td>
              <td>
                <span v-if="t.mpesa_config && t.mpesa_config.c2b_registered" style="color:var(--green);font-weight:800">✓ Registered</span>
                <span v-else-if="t.mpesa_config" style="color:var(--amber);font-weight:800">⏳ Pending</span>
                <span v-else style="color:var(--slate-light)">—</span>
              </td>
              <td>
                <span v-if="t.mpesa_config && t.mpesa_config.is_active" class="rv-badge rv-bg">Active</span>
                <span v-else-if="t.mpesa_config && t.mpesa_config.environment==='sandbox'" class="rv-badge rv-ba">Testing</span>
                <span v-else-if="t.mpesa_config" class="rv-badge rv-bgy">Inactive</span>
                <span v-else class="rv-badge rv-bgy">Not set up</span>
              </td>
              <td>
                <button class="rv-btn rv-btn-s rv-btn-xs" @click="$emit('open-client', t)">Configure →</button>
              </td>
            </tr>
            <tr v-if="tenants.length===0">
              <td colspan="7" style="text-align:center;color:var(--slate-light);padding:32px">No clients yet</td>
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
        const mc = await api.get(`/mpesa/config/?tenant=${t.id}`)
        t.mpesa_config = mc.data || null
      } catch(e) {
        t.mpesa_config = null
      }
    }
    tenants.value = list
  } catch(e) {}
  loading.value = false
}
useAutoRefresh(loadData, 120000)
</script>
