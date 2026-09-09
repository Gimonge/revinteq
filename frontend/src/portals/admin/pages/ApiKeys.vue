<template>
  <div style="display:flex;flex-direction:column;gap:20px" class="fade-up">
    <div class="rv-page-header">
      <div>
        <div class="rv-page-title">API Keys</div>
        <div class="rv-page-sub">Third-party integration keys managed per client</div>
      </div>
    </div>

    <div class="rv-card card-reveal">
      <div class="rv-ch">
        <div class="rv-ct">All API Keys</div>
        <button class="rv-btn rv-btn-p rv-btn-sm" @click="showCreate=true">+ Create Key</button>
      </div>
      <div v-if="loading" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else class="rv-tw">
        <table class="rv-table">
          <thead>
            <tr>
              <th>Client</th><th>Key Name</th><th>Key</th>
              <th>Permissions</th><th>Last Used</th><th>Status</th><th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="k in keys" :key="k.id">
              <td><strong>{{ k.tenant_name }}</strong></td>
              <td>{{ k.name }}</td>
              <td>
                <code style="font-size:11px;background:var(--bg);padding:3px 8px;border-radius:4px;font-family:monospace">
                  {{ k.key.slice(0,18) }}...
                </code>
              </td>
              <td>
                <span v-if="k.can_create_sales" class="rv-badge rv-bg" style="margin-right:3px">Sales</span>
                <span v-if="k.can_read_metrics" class="rv-badge rv-bp">Metrics</span>
              </td>
              <td style="white-space:nowrap">{{ k.last_used_at ? formatDate(k.last_used_at) : 'Never' }}</td>
              <td>
                <span class="rv-badge" :class="k.is_active?'rv-bg':'rv-bgy'">
                  {{ k.is_active ? 'Active' : 'Revoked' }}
                </span>
              </td>
              <td>
                <button
                  v-if="k.is_active"
                  class="rv-btn rv-btn-d rv-btn-xs"
                  @click="revokeKey(k)"
                  :disabled="revoking===k.id">
                  Revoke
                </button>
                <span v-else style="color:var(--slate-light);font-size:12px;font-weight:600">Revoked</span>
              </td>
            </tr>
            <tr v-if="keys.length===0">
              <td colspan="7" style="text-align:center;color:var(--slate-light);padding:32px">
                No API keys yet
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create key modal -->
    <div v-if="showCreate" style="position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px" @click.self="showCreate=false">
      <div style="background:var(--card);border-radius:var(--r-xl);width:100%;max-width:460px;box-shadow:var(--shadow-lg);animation:fadeUp .3s ease">
        <div style="padding:20px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between">
          <span style="font-size:16px;font-weight:900">Create API Key</span>
          <button @click="showCreate=false" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--slate-light)">×</button>
        </div>
        <div style="padding:24px">
          <div class="rv-fg">
            <label class="rv-fl">Client</label>
            <select v-model="newKey.tenant_id" class="rv-fs">
              <option value="">Select a client...</option>
              <option v-for="t in tenants" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </div>
          <div class="rv-fg">
            <label class="rv-fl">Key Name</label>
            <input v-model="newKey.name" class="rv-fi" placeholder="e.g. POS System, Website">
          </div>
          <div style="display:flex;flex-direction:column;gap:10px;padding:14px;background:var(--bg);border-radius:var(--r-md)">
            <label style="font-size:11.5px;font-weight:800;color:var(--slate-mid);text-transform:uppercase;letter-spacing:.5px">Permissions</label>
            <label style="display:flex;align-items:center;gap:10px;cursor:pointer;font-size:13px;font-weight:700">
              <input type="checkbox" v-model="newKey.can_create_sales" style="accent-color:var(--green)">
              Sales — create sales via API
            </label>
            <label style="display:flex;align-items:center;gap:10px;cursor:pointer;font-size:13px;font-weight:700">
              <input type="checkbox" v-model="newKey.can_read_metrics" style="accent-color:var(--green)">
              Metrics — read dashboard data
            </label>
          </div>
          <div v-if="createdKey" class="rv-al rv-al-g" style="margin-top:14px">
            <div>
              <div style="font-weight:900;margin-bottom:6px"><i class="ti ti-circle-check" aria-hidden="true"></i> Key created — copy it now, it won't be shown again</div>
              <div class="rv-api-key">{{ createdKey }}</div>
            </div>
          </div>
          <div v-if="createError" class="rv-al rv-al-r" style="margin-top:14px">{{ createError }}</div>
        </div>
        <div style="padding:16px 24px;border-top:1px solid var(--border);display:flex;gap:10px;justify-content:flex-end">
          <button class="rv-btn rv-btn-s" @click="closeCreate">{{ createdKey ? 'Done' : 'Cancel' }}</button>
          <button v-if="!createdKey" class="rv-btn rv-btn-p" @click="createKey" :disabled="creating">
            <span v-if="creating" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
            <span v-else>Generate Key</span>
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
const keys     = ref([])
const tenants  = ref([])
const loading  = ref(true)
const revoking = ref(null)
const showCreate = ref(false)
const creating   = ref(false)
const createdKey = ref('')
const createError = ref('')
const newKey = ref({ tenant_id:'', name:'', can_create_sales:true, can_read_metrics:false })

function formatDate(d) {
  if (!d) return 'Never'
  const dt = dayjs(d)
  return dt.isToday ? `Today ${dt.format('HH:mm')}` : dt.format('D MMM HH:mm')
}

async function loadData() {
  loading.value = true
  try {
    const [keysRes, tenantsRes] = await Promise.all([
      api.get('/external/api-keys/'),
      api.get('/tenants/'),
    ])
    keys.value    = keysRes.data.results || keysRes.data || []
    tenants.value = tenantsRes.data.results || tenantsRes.data || []
  } catch(e) {}
  loading.value = false
}

async function revokeKey(k) {
  revoking.value = k.id
  try {
    await api.patch(`/external/api-keys/${k.id}/`, { is_active: false })
    k.is_active = false
    emit('toast', `Key "${k.name}" revoked`, 'green')
  } catch(e) {
    emit('toast', 'Failed to revoke key', 'red')
  }
  revoking.value = null
}

async function createKey() {
  if (!newKey.value.tenant_id || !newKey.value.name) {
    createError.value = 'Client and key name are required.'
    return
  }
  creating.value = true; createError.value = ''
  try {
    const r = await api.post('/external/api-keys/', newKey.value)
    createdKey.value = r.data.key
    keys.value.unshift(r.data)
    emit('toast', 'API key created', 'green')
  } catch(e) {
    createError.value = e.response?.data?.detail || 'Failed to create key.'
  }
  creating.value = false
}

function closeCreate() {
  showCreate.value = false
  createdKey.value = ''
  createError.value = ''
  newKey.value = { tenant_id:'', name:'', can_create_sales:true, can_read_metrics:false }
}

useAutoRefresh(loadData, 120000)
</script>
