<template>
  <div style="display:flex;flex-direction:column;gap:20px" class="fade-up">
    <div class="rv-page-header">
      <div>
        <div class="rv-page-title">{{ tenant?.name || 'Client Detail' }}</div>
        <div class="rv-page-sub">{{ tenant?.location || '' }}{{ tenant?.industry ? ' &bull; ' + tenant.industry : '' }}</div>
      </div>
      <div style="display:flex;gap:10px">
        <button v-if="tenant?.status==='active'" class="rv-btn rv-btn-a" @click="$emit('impersonate',tenant)"><i class="ti ti-eye" aria-hidden="true"></i> View as Client</button>
        <button class="rv-btn rv-btn-s" @click="$emit('nav','clients')"><i class="ti ti-arrow-left" aria-hidden="true"></i> Back</button>
      </div>
    </div>

    <div class="rv-g2">
      <!-- Business Info -->
      <div class="rv-card card-reveal">
        <div class="rv-ch">
          <div class="rv-ct">Business Info</div>
          <button class="rv-btn rv-btn-s rv-btn-sm" @click="editMode=!editMode"><i class="ti ti-pencil" aria-hidden="true"></i> {{ editMode?'Cancel':'Edit' }}</button>
        </div>
        <div class="rv-cb">
          <div v-if="!editMode">
            <table class="rv-info-table"><tbody>
              <tr><td>Business Name</td><td>{{ tenant?.name }}</td></tr>
              <tr><td>Status</td><td><span class="rv-badge" :class="tenant?.status==='active'?'rv-bg':'rv-bgy'">{{ tenant?.status }}</span></td></tr>
              <tr><td>Currency</td><td>{{ tenant?.currency || 'KES' }}</td></tr>
              <tr><td>Contact</td><td>{{ tenant?.contact_name || '—' }}</td></tr>
              <tr><td>Email</td><td>{{ tenant?.contact_email || '—' }}</td></tr>
              <tr><td>Phone</td><td>{{ tenant?.contact_phone || '—' }}</td></tr>
              <tr><td>Budget Cap</td><td>{{ tenant?.budget_increase_cap_percent || 20 }}%</td></tr>
              <tr><td>Facebook</td><td><span :style="{color:tenant?.meta_fb_connected?'var(--green)':'var(--red)',fontWeight:800}"><i :class="['ti', tenant?.meta_fb_connected?'ti-check':'ti-x']" aria-hidden="true"></i> {{ tenant?.meta_fb_connected?'Connected':'Not connected' }}</span></td></tr>
              <tr><td>Instagram</td><td><span :style="{color:tenant?.meta_ig_connected?'var(--green)':'var(--red)',fontWeight:800}"><i :class="['ti', tenant?.meta_ig_connected?'ti-check':'ti-x']" aria-hidden="true"></i> {{ tenant?.meta_ig_connected?'Connected':'Not connected' }}</span></td></tr>
            </tbody></table>

            <!-- Archive / Restore -->
            <div style="margin-top:14px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <button v-if="tenant?.status==='active'" class="rv-btn rv-btn-d rv-btn-sm" @click="archiveClient" :disabled="archiving">
                <span v-if="archiving" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
                <span v-else><i class="ti ti-archive" aria-hidden="true"></i> Archive Client</span>
              </button>
              <button v-else class="rv-btn rv-btn-p rv-btn-sm" @click="restoreClient" :disabled="archiving">
                <span v-if="archiving" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
                <span v-else><i class="ti ti-circle-check" aria-hidden="true"></i> Restore to Active</span>
              </button>
              <span v-if="tenant?.status==='inactive'" class="rv-badge rv-bgy">Archived — data preserved</span>
            </div>

            <!-- Ad Account Assignment -->
            <div style="margin-top:20px;border-top:1px solid var(--border);padding-top:16px">
              <div style="font-size:11px;font-weight:900;color:var(--slate-mid);text-transform:uppercase;letter-spacing:.6px;margin-bottom:10px"><i class="ti ti-chart-bar" aria-hidden="true"></i> Assigned Ad Accounts</div>
              <div v-if="loadingAdAccounts" style="color:var(--slate-light);font-size:12px">Loading...</div>
              <div v-else>
                <div v-if="!assignedAccounts.length" style="font-size:12px;color:var(--slate-light);margin-bottom:8px">No ad accounts assigned yet.</div>
                <div v-for="acc in assignedAccounts" :key="acc.id"
                  style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:var(--green-light);border-radius:var(--r-md);margin-bottom:6px;font-size:12px">
                  <div>
                    <strong>{{ acc.account_name }}</strong>
                    <span style="color:var(--slate-mid);margin-left:8px;font-size:11px">{{ acc.meta_account_id }}</span>
                    <span class="rv-badge rv-bg" style="font-size:10px;margin-left:6px">{{ acc.platform }}</span>
                    <span style="font-size:11px;color:var(--slate-mid);margin-left:4px">owned by {{ acc.owner_tenant }}</span>
                  </div>
                  <button class="rv-btn rv-btn-d rv-btn-xs" @click="unassignAccount(acc)">Remove</button>
                </div>
                <div style="margin-top:10px">
                  <select v-model="accountToAssign" class="rv-fs" style="font-size:12px;width:100%;margin-bottom:8px">
                    <option value="">— Assign an ad account —</option>
                    <option v-for="acc in unassignedAccounts" :key="acc.id" :value="acc.id">
                      {{ acc.account_name }} · {{ acc.meta_account_id }} ({{ acc.owner_tenant }})
                    </option>
                  </select>
                  <button class="rv-btn rv-btn-p rv-btn-xs" @click="assignAccount" :disabled="!accountToAssign||assigningAccount">
                    <span v-if="assigningAccount" class="rv-spin" style="width:10px;height:10px;border-width:2px"></span>
                    <span v-else><i class="ti ti-plus" aria-hidden="true"></i> Assign Ad Account</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-else>
            <div class="rv-fg"><label class="rv-fl">Business Name</label><input v-model="editForm.name" class="rv-fi"></div>
            <div class="rv-g2">
              <div class="rv-fg"><label class="rv-fl">Contact Name</label><input v-model="editForm.contact_name" class="rv-fi"></div>
              <div class="rv-fg"><label class="rv-fl">Contact Email</label><input v-model="editForm.contact_email" class="rv-fi" type="email"></div>
            </div>
            <div class="rv-g2">
              <div class="rv-fg"><label class="rv-fl">Phone</label><input v-model="editForm.contact_phone" class="rv-fi"></div>
              <div class="rv-fg"><label class="rv-fl">Currency</label>
                <select v-model="editForm.currency" class="rv-fs"><option>KES</option><option>UGX</option><option>TZS</option><option>USD</option></select>
              </div>
            </div>
            <div class="rv-g2">
              <div class="rv-fg"><label class="rv-fl">Industry</label><input v-model="editForm.industry" class="rv-fi"></div>
              <div class="rv-fg"><label class="rv-fl">Location</label><input v-model="editForm.location" class="rv-fi"></div>
            </div>
            <div style="display:flex;gap:10px">
              <button class="rv-btn rv-btn-p" @click="saveEdit"><i class="ti ti-device-floppy" aria-hidden="true"></i> Save Changes</button>
              <button class="rv-btn rv-btn-s" @click="editMode=false">Cancel</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Client Access -->
      <div class="rv-card card-reveal" style="animation-delay:.08s">
        <div class="rv-ch"><div class="rv-ct">Client Access &amp; Invitations</div></div>
        <div class="rv-cb">
          <div class="rv-fg"><label class="rv-fl">Invite Email</label><input v-model="inviteEmail" class="rv-fi" placeholder="client@business.co.ke" type="email"></div>
          <div class="rv-fg"><label class="rv-fl">Role</label>
            <select v-model="inviteRole" class="rv-fs">
              <option value="CLIENT">Client (standard)</option>
              <option value="ADMIN">Admin (limited admin)</option>
            </select>
          </div>
          <button class="rv-btn rv-btn-p" @click="sendInvite" :disabled="inviting">
            <span v-if="inviting" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
            <span v-else><i class="ti ti-mail" aria-hidden="true"></i> Send Invitation</span>
          </button>
          <div v-if="inviteSuccess" class="rv-al rv-al-g" style="margin-top:12px"><i class="ti ti-circle-check" aria-hidden="true"></i> Invitation sent to {{ inviteEmail }}</div>
          <div class="rv-divider" style="margin:16px 0"></div>
          <div class="rv-sec-lbl">Existing Members</div>
          <div v-for="m in members" :key="m.id" style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--border)">
            <div style="width:32px;height:32px;border-radius:50%;background:var(--green-light);display:flex;align-items:center;justify-content:center;font-weight:900;color:var(--green);font-size:13px">{{ m.user_email?.[0]?.toUpperCase() }}</div>
            <div style="flex:1"><div style="font-size:13px;font-weight:800">{{ m.user_email }}</div><div style="font-size:11px;color:var(--slate-light);font-weight:600">{{ m.role }} &bull; Joined {{ m.joined_at }}</div></div>
            <span class="rv-badge" :class="m.is_active?'rv-bg':'rv-bgy'">{{ m.is_active?'active':'inactive' }}</span>
          </div>
          <div v-if="members.length===0" style="color:var(--slate-light);font-size:13px;font-weight:600;padding:10px 0">No members yet. Send an invitation above.</div>
        </div>
      </div>
    </div>

    <div class="rv-g2">
      <!-- M-Pesa Config -->
      <div class="rv-card card-reveal" style="animation-delay:.12s">
        <div class="rv-ch"><div><div class="rv-ct"><i class="ti ti-heart" aria-hidden="true"></i> M-Pesa Configuration</div><div class="rv-cst">Daraja API credentials (encrypted at rest)</div></div></div>
        <div class="rv-cb">
          <div class="rv-fg"><label class="rv-fl">Environment</label>
            <select v-model="mpesa.environment" class="rv-fs"><option value="sandbox">Sandbox (testing)</option><option value="production">Production (live)</option></select>
          </div>
          <div class="rv-fg"><label class="rv-fl">Shortcode Type</label>
            <select v-model="mpesa.shortcode_type" class="rv-fs"><option value="till">Buy Goods (Till Number)</option><option value="paybill">Pay Bill</option></select>
          </div>
          <div class="rv-fg"><label class="rv-fl">{{ mpesa.shortcode_type==='paybill'?'Paybill Number':'Till Number' }}</label>
            <input v-model="mpesa.shortcode" class="rv-fi" placeholder="e.g. 5501234">
          </div>
          <div class="rv-fg"><label class="rv-fl">Consumer Key</label><input v-model="mpesa.consumer_key" class="rv-fi" type="password"></div>
          <div class="rv-fg"><label class="rv-fl">Consumer Secret</label><input v-model="mpesa.consumer_secret" class="rv-fi" type="password"></div>
          <div class="rv-fg"><label class="rv-fl">Passkey</label><input v-model="mpesa.passkey" class="rv-fi" type="password"></div>
          <button class="rv-btn rv-btn-p" @click="saveMpesa" :disabled="savingMpesa">
            <span v-if="savingMpesa" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
            <span v-else><i class="ti ti-device-floppy" aria-hidden="true"></i> Save &amp; Register URLs</span>
          </button>
          <div v-if="mpesaSuccess" class="rv-al rv-al-g" style="margin-top:12px"><i class="ti ti-circle-check" aria-hidden="true"></i> M-Pesa config saved!</div>
        </div>
      </div>

      <!-- SMS Config -->
      <div class="rv-card card-reveal" style="animation-delay:.16s">
        <div class="rv-ch"><div><div class="rv-ct"><i class="ti ti-device-mobile" aria-hidden="true"></i> SMS Configuration</div><div class="rv-cst">Africa's Talking credentials (encrypted)</div></div></div>
        <div class="rv-cb">
          <div class="rv-fg"><label class="rv-fl">AT Username</label><input v-model="sms.username" class="rv-fi"></div>
          <div class="rv-fg"><label class="rv-fl">API Key</label><input v-model="sms.api_key" class="rv-fi" type="password"></div>
          <div class="rv-fg"><label class="rv-fl">Sender ID (optional)</label><input v-model="sms.sender_id" class="rv-fi"></div>
          <button class="rv-btn rv-btn-p" @click="saveSms" :disabled="savingSms">
            <span v-if="savingSms" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
            <span v-else><i class="ti ti-device-floppy" aria-hidden="true"></i> Save SMS Config</span>
          </button>
          <div v-if="smsSuccess" class="rv-al rv-al-g" style="margin-top:12px"><i class="ti ti-circle-check" aria-hidden="true"></i> SMS config saved!</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/api'

const props = defineProps({ tenant: Object })
const emit  = defineEmits(['nav','impersonate','toast'])

const editMode      = ref(false)
const editForm      = ref({})
const inviteEmail   = ref('')
const inviteRole    = ref('CLIENT')
const inviting      = ref(false)
const inviteSuccess = ref(false)
const members       = ref([])
const archiving     = ref(false)
const mpesa = ref({ environment:'sandbox', shortcode_type:'till', shortcode:'', consumer_key:'', consumer_secret:'', passkey:'' })
const sms   = ref({ username:'', api_key:'', sender_id:'' })
const savingMpesa  = ref(false)
const savingSms    = ref(false)
const mpesaSuccess = ref(false)
const smsSuccess   = ref(false)

// Ad account assignment
const allAdAccounts    = ref([])
const loadingAdAccounts = ref(false)
const accountToAssign  = ref('')
const assigningAccount = ref(false)

const assignedAccounts = computed(() => {
  if (!allAdAccounts.value?.length || !props.tenant?.id) return []
  const tid = String(props.tenant.id)
  return allAdAccounts.value.filter(a => a.assigned_tenant_id && String(a.assigned_tenant_id) === tid)
})

const unassignedAccounts = computed(() => {
  if (!allAdAccounts.value?.length) return []
  return allAdAccounts.value.filter(a => !a.assigned_tenant_id)
})

onMounted(loadAdAccounts)

watch(() => props.tenant, (t) => {
  if (!t) return
  editForm.value = { name:t.name, contact_name:t.contact_name, contact_email:t.contact_email, contact_phone:t.contact_phone, currency:t.currency, industry:t.industry, location:t.location }
  loadMembers()
  loadConfigs()
}, { immediate: true })

async function loadAdAccounts() {
  loadingAdAccounts.value = true
  try {
    const r = await api.get('/meta/admin/accounts/')
    allAdAccounts.value = r.data || []
  } catch(e) { allAdAccounts.value = [] }
  loadingAdAccounts.value = false
}

async function assignAccount() {
  if (!accountToAssign.value) return
  assigningAccount.value = true
  try {
    await api.post(`/meta/admin/accounts/${accountToAssign.value}/assign/`, { tenant_id: props.tenant.id })
    await loadAdAccounts()
    accountToAssign.value = ''
    emit('toast', 'Ad account assigned <i class="ti ti-check" aria-hidden="true"></i>', 'green')
  } catch(e) { emit('toast', 'Failed to assign', 'red') }
  assigningAccount.value = false
}

async function unassignAccount(acc) {
  try {
    await api.post(`/meta/admin/accounts/${acc.id}/assign/`, { tenant_id: null })
    await loadAdAccounts()
    emit('toast', 'Ad account removed', 'green')
  } catch(e) {}
}

async function archiveClient() {
  if (!confirm(`Archive ${props.tenant.name}? All data is preserved and can be restored.`)) return
  archiving.value = true
  try {
    await api.patch(`/tenants/${props.tenant.id}/`, { status: 'inactive' })
    props.tenant.status = 'inactive'
    emit('toast', `${props.tenant.name} archived`, 'green')
  } catch(e) { emit('toast', 'Failed to archive', 'red') }
  archiving.value = false
}

async function restoreClient() {
  archiving.value = true
  try {
    await api.patch(`/tenants/${props.tenant.id}/`, { status: 'active' })
    props.tenant.status = 'active'
    emit('toast', `${props.tenant.name} restored to active`, 'green')
  } catch(e) { emit('toast', 'Failed to restore', 'red') }
  archiving.value = false
}

async function loadMembers() {
  if (!props.tenant?.id) return
  try { const r = await api.get(`/tenants/${props.tenant.id}/members/`); members.value = r.data || [] } catch(e) {}
}

async function loadConfigs() {
  if (!props.tenant?.id) return
  try { const r = await api.get(`/mpesa/config/?tenant=${props.tenant.id}`); if (r.data) Object.assign(mpesa.value, r.data) } catch(e) {}
  try { const r = await api.get(`/sms/config/?tenant=${props.tenant.id}`); if (r.data) Object.assign(sms.value, r.data) } catch(e) {}
}

async function saveEdit() {
  try { await api.patch(`/tenants/${props.tenant.id}/`, editForm.value); editMode.value=false; emit('toast','Business info saved','green') } catch(e) { emit('toast','Failed to save','red') }
}

async function sendInvite() {
  if (!inviteEmail.value) return
  inviting.value=true; inviteSuccess.value=false
  try { await api.post(`/tenants/${props.tenant.id}/invite/`, { email:inviteEmail.value, role:inviteRole.value }); inviteSuccess.value=true; loadMembers() } catch(e) { emit('toast','Failed to send invite','red') }
  inviting.value=false
}

async function saveMpesa() {
  savingMpesa.value=true; mpesaSuccess.value=false
  try { await api.post('/mpesa/config/', { ...mpesa.value, tenant:props.tenant.id }); mpesaSuccess.value=true } catch(e) { emit('toast','Failed to save M-Pesa config','red') }
  savingMpesa.value=false
}

async function saveSms() {
  savingSms.value=true; smsSuccess.value=false
  try { await api.post('/sms/config/', { ...sms.value, tenant:props.tenant.id }); smsSuccess.value=true } catch(e) { emit('toast','Failed to save SMS config','red') }
  savingSms.value=false
}
</script>