<template>
  <div style="display:flex;flex-direction:column;gap:18px">
    <div class="fade-up"><div style="font-size:21px;font-weight:900;letter-spacing:-.4px">Settings</div></div>
    <div class="rv-g2">
      <!-- Business Profile -->
      <div class="rv-card card-reveal">
        <div class="rv-ch"><span class="rv-ct">Business Profile</span></div>
        <div class="rv-cb">
          <div v-if="saved" class="rv-al rv-al-g" style="margin-bottom:14px"><i class="ti ti-circle-check" aria-hidden="true"></i> Settings saved!</div>
          <div class="rv-fg"><label class="rv-fl">Business Name</label><input v-model="form.name" class="rv-fi"></div>
          <div class="rv-fg"><label class="rv-fl">WhatsApp Number</label><input v-model="form.whatsapp_number" class="rv-fi" placeholder="+254712345678"></div>
          <div class="rv-fg"><label class="rv-fl">Default WhatsApp Message</label><textarea v-model="form.whatsapp_default_message" class="rv-ft" style="min-height:60px"></textarea></div>
          <div class="rv-fg"><label class="rv-fl">Currency</label>
            <select v-model="form.currency" class="rv-fs"><option value="KES">KES — Kenyan Shilling</option><option value="UGX">UGX</option><option value="TZS">TZS</option><option value="USD">USD</option></select>
          </div>
          <button class="rv-btn rv-btn-p" @click="saveProfile" :disabled="saving">
            <span v-if="saving" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
            <span v-else><i class="ti ti-device-floppy" aria-hidden="true"></i> Save Changes</span>
          </button>
        </div>
      </div>
      <!-- Budget Cap -->
      <div class="rv-card card-reveal" style="animation-delay:.08s">
        <div class="rv-ch"><span class="rv-ct">Budget Increase Cap</span></div>
        <div class="rv-cb">
          <p style="font-size:13px;color:var(--slate-mid);font-weight:600;line-height:1.6;margin-bottom:16px">Revinteq will never recommend increasing a campaign's daily budget by more than this percentage.</p>
          <div class="rv-fg">
            <label class="rv-fl">Max Increase: <strong style="color:var(--green)">{{ capVal }}%</strong></label>
            <input type="range" min="5" max="30" v-model="capVal" style="width:100%;height:6px;accent-color:var(--green);cursor:pointer">
            <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--slate-light);margin-top:4px;font-weight:700"><span>5% (safe)</span><span>30% (aggressive)</span></div>
          </div>
          <button class="rv-btn rv-btn-p rv-btn-sm" @click="saveCap" :disabled="savingCap"><i class="ti ti-device-floppy" aria-hidden="true"></i> Save Cap</button>
        </div>
      </div>
    </div>
    <!-- Connected accounts -->
    <div class="rv-card card-reveal" style="animation-delay:.12s">
      <div class="rv-ch"><span class="rv-ct">Connected Accounts</span></div>
      <div class="rv-cb" style="padding:0">
        <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid var(--border)">
          <div style="display:flex;align-items:center;gap:12px">
            <div style="width:38px;height:38px;border-radius:var(--r-md);background:var(--blue-light);display:flex;align-items:center;justify-content:center;font-size:20px"><i class="ti ti-brand-facebook" aria-hidden="true"></i></div>
            <div><div style="font-size:14px;font-weight:800">Facebook Ads</div><div style="font-size:12px;color:var(--slate-light);font-weight:600;margin-top:1px">{{ fbStatus }}</div></div>
          </div>
          <span class="rv-badge" :class="fbConnected?'rv-bg':'rv-bgy'"><i v-if="fbConnected" class="ti ti-check" aria-hidden="true"></i> {{ fbConnected?'Connected':'Not Connected' }}</span>
        </div>
        <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid var(--border)">
          <div style="display:flex;align-items:center;gap:12px">
            <div style="width:38px;height:38px;border-radius:var(--r-md);background:linear-gradient(135deg,var(--ig1),var(--ig3));display:flex;align-items:center;justify-content:center;font-size:20px"><i class="ti ti-camera" aria-hidden="true"></i></div>
            <div><div style="font-size:14px;font-weight:800">Instagram Ads</div><div style="font-size:12px;color:var(--slate-light);font-weight:600;margin-top:1px">via Meta Business</div></div>
          </div>
          <span class="rv-badge" :class="igConnected?'rv-big':'rv-bgy'"><i v-if="igConnected" class="ti ti-check" aria-hidden="true"></i> {{ igConnected?'Connected':'Not Connected' }}</span>
        </div>
        <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 20px">
          <div style="display:flex;align-items:center;gap:12px">
            <div style="width:38px;height:38px;border-radius:var(--r-md);background:var(--green-light);display:flex;align-items:center;justify-content:center;font-size:20px"><i class="ti ti-message-circle" aria-hidden="true"></i></div>
            <div><div style="font-size:14px;font-weight:800">WhatsApp Business API</div><div style="font-size:12px;color:var(--slate-light);font-weight:600;margin-top:1px">Auto-creates pipeline deals from ad clicks</div></div>
          </div>
          <span class="rv-badge" :class="form.whatsapp_number?'rv-bg':'rv-bgy'"><i v-if="form.whatsapp_number" class="ti ti-check" aria-hidden="true"></i> {{ form.whatsapp_number?'Active':'Not configured' }}</span>
        </div>
        <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid var(--border)">
          <div style="display:flex;align-items:center;gap:12px">
            <div style="width:38px;height:38px;border-radius:var(--r-md);background:var(--purple-light);display:flex;align-items:center;justify-content:center;font-size:20px"><i class="ti ti-layout-kanban" aria-hidden="true"></i></div>
            <div><div style="font-size:14px;font-weight:800">Kommo CRM</div><div style="font-size:12px;color:var(--slate-light);font-weight:600;margin-top:1px">{{ kommoStatusText }}</div></div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <button v-if="!kommo.connected" class="rv-btn rv-btn-p rv-btn-sm" @click="showKommoForm = !showKommoForm">
              <i class="ti ti-plug" aria-hidden="true"></i> Connect
            </button>
            <template v-else>
              <button class="rv-btn rv-btn-s rv-btn-sm" @click="syncKommo" :disabled="kommoSyncing">
                <span v-if="kommoSyncing" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
                <span v-else><i class="ti ti-refresh" aria-hidden="true"></i> Sync Now</span>
              </button>
              <button class="rv-btn rv-btn-d rv-btn-sm" @click="disconnectKommo"><i class="ti ti-plug-off" aria-hidden="true"></i></button>
              <span class="rv-badge rv-bg"><i class="ti ti-check" aria-hidden="true"></i> Connected</span>
            </template>
          </div>
        </div>
        <div v-if="showKommoForm && !kommo.connected" style="padding:16px 20px;border-bottom:1px solid var(--border);background:var(--bg)">
          <p style="font-size:12.5px;color:var(--slate-mid);font-weight:600;line-height:1.6;margin-bottom:14px">
            In your own Kommo account, go to <strong>Settings → Integrations → Create Integration</strong>. Set the Redirect URI to
            <code style="background:var(--card);padding:2px 6px;border-radius:4px;font-size:11.5px">https://api.revinteq.com/api/v1/kommo/callback/</code>
            (it won't actually be visited — Kommo just requires it to match). Save it, and on the integration's page you'll see an
            <strong>Integration ID</strong>, <strong>Secret Key</strong>, and an <strong>Authorization Code</strong> — copy all three here.
            The code expires in 20 minutes, so paste it in fairly quickly.
          </p>
          <div class="rv-fg"><label class="rv-fl">Your Kommo Subdomain</label><input v-model="kommoForm.subdomain" class="rv-fi" placeholder="yourbusiness.kommo.com"></div>
          <div class="rv-fg"><label class="rv-fl">Integration ID</label><input v-model="kommoForm.client_id" class="rv-fi"></div>
          <div class="rv-fg"><label class="rv-fl">Secret Key</label><input v-model="kommoForm.client_secret" type="password" class="rv-fi"></div>
          <div class="rv-fg"><label class="rv-fl">Authorization Code</label><input v-model="kommoForm.auth_code" class="rv-fi"></div>
          <button class="rv-btn rv-btn-p rv-btn-sm" @click="connectKommo" :disabled="kommoConnecting">
            <span v-if="kommoConnecting" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
            <span v-else><i class="ti ti-plug" aria-hidden="true"></i> Connect Kommo</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits(['toast'])
const auth = useAuthStore()
const saving = ref(false), savingCap = ref(false), saved = ref(false)
const capVal = ref(20)
const form = ref({ name:'', whatsapp_number:'', whatsapp_default_message:'', currency:'KES' })

const fbConnected = computed(() => auth.tenant?.meta_fb_connected)
const igConnected = computed(() => auth.tenant?.meta_ig_connected)
const fbStatus    = computed(() => fbConnected.value ? 'Read-only access' : 'Not connected')

const kommo = ref({ connected:false, subdomain:'', last_synced:null, last_error:'' })
const kommoConnecting = ref(false), kommoSyncing = ref(false)
const showKommoForm = ref(false)
const kommoForm = ref({ subdomain:'', client_id:'', client_secret:'', auth_code:'' })
const kommoStatusText = computed(() => {
  if (!kommo.value.connected) return 'Sales tracked here become your revenue'
  return kommo.value.subdomain + (kommo.value.last_error ? ' — sync issue, check connection' : '')
})

async function fetchKommoStatus() {
  try { const r = await api.get('/kommo/status/'); kommo.value = r.data } catch(e) {}
}
async function connectKommo() {
  kommoConnecting.value = true
  try {
    const r = await api.post('/kommo/connect/', kommoForm.value)
    kommo.value = { connected:true, subdomain:r.data.subdomain, last_synced:null, last_error:'' }
    showKommoForm.value = false
    kommoForm.value = { subdomain:'', client_id:'', client_secret:'', auth_code:'' }
    emit('toast','Kommo connected successfully!','green')
  } catch(e) {
    emit('toast', e.response?.data?.message || 'Failed to connect Kommo', 'red')
  }
  kommoConnecting.value = false
}
async function syncKommo() {
  kommoSyncing.value = true
  try { await api.post('/kommo/sync/'); emit('toast','Kommo sync started','green') }
  catch(e) { emit('toast','Failed to start sync','red') }
  kommoSyncing.value = false
}
async function disconnectKommo() {
  try { await api.post('/kommo/disconnect/'); kommo.value = { connected:false, subdomain:'', last_synced:null, last_error:'' }; emit('toast','Kommo disconnected','green') }
  catch(e) { emit('toast','Failed to disconnect','red') }
}

onMounted(() => {
  if (auth.tenant) {
    form.value.name = auth.tenant.name || ''
    form.value.whatsapp_number = auth.tenant.whatsapp_number || ''
    form.value.whatsapp_default_message = auth.tenant.whatsapp_default_message || ''
    form.value.currency = auth.tenant.currency || 'KES'
    capVal.value = auth.tenant.budget_increase_cap_percent || 20
  }
  fetchKommoStatus()
})
async function saveProfile() {
  saving.value = true; saved.value = false
  try { const r = await api.patch('/auth/account/', form.value); auth.tenant = { ...auth.tenant, ...r.data.tenant }; saved.value=true; emit('toast','Settings saved','green') } catch(e) { emit('toast','Failed to save','red') }
  saving.value = false
}
async function saveCap() {
  savingCap.value = true
  try { await api.patch('/auth/account/', { budget_increase_cap_percent: parseInt(capVal.value) }); emit('toast','Budget cap updated','green') } catch(e) { emit('toast','Failed to save','red') }
  savingCap.value = false
}
</script>
