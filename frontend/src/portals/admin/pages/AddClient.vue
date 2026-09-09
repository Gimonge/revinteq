<template>
  <div style="display:flex;flex-direction:column;gap:20px" class="fade-up">
    <div class="rv-page-header">
      <div>
        <div class="rv-page-title">Add New Client</div>
        <div class="rv-page-sub">Create a new tenant account on Revinteq</div>
      </div>
    </div>

    <div class="rv-card card-reveal" style="max-width:640px">
      <div class="rv-ch"><div class="rv-ct">Client Details</div></div>
      <div class="rv-cb">
        <div v-if="error"   class="rv-al rv-al-r" style="margin-bottom:16px">{{ error }}</div>
        <div v-if="success" class="rv-al rv-al-g" style="margin-bottom:16px"><i class="ti ti-circle-check" aria-hidden="true"></i> {{ success }}</div>

        <!-- Business Info -->
        <div class="rv-sec-lbl">Business Information</div>
        <div class="rv-fg">
          <label class="rv-fl">Business Name *</label>
          <input v-model="form.name" class="rv-fi" placeholder="e.g. Amari Boutique Nairobi">
        </div>
        <div class="rv-g2">
          <div class="rv-fg">
            <label class="rv-fl">Contact Name</label>
            <input v-model="form.contact_name" class="rv-fi" placeholder="Full name">
          </div>
          <div class="rv-fg">
            <label class="rv-fl">Contact Email</label>
            <input v-model="form.contact_email" class="rv-fi" type="email" placeholder="owner@business.co.ke">
          </div>
        </div>
        <div class="rv-g2">
          <div class="rv-fg">
            <label class="rv-fl">Phone Number</label>
            <input v-model="form.contact_phone" class="rv-fi" placeholder="+254710843401">
          </div>
          <div class="rv-fg">
            <label class="rv-fl">Currency</label>
            <select v-model="form.currency" class="rv-fs">
              <option value="KES">KES — Kenyan Shilling</option>
              <option value="UGX">UGX — Ugandan Shilling</option>
              <option value="TZS">TZS — Tanzanian Shilling</option>
              <option value="USD">USD — US Dollar</option>
            </select>
          </div>
        </div>
        <div class="rv-g2">
          <div class="rv-fg">
            <label class="rv-fl">Industry</label>
            <input v-model="form.industry" class="rv-fi" placeholder="e.g. Fashion, Beauty, Food">
          </div>
          <div class="rv-fg">
            <label class="rv-fl">Location</label>
            <input v-model="form.location" class="rv-fi" placeholder="e.g. Nairobi, Kenya">
          </div>
        </div>
        <div class="rv-fg">
          <label class="rv-fl">Internal Notes</label>
          <textarea v-model="form.notes" class="rv-ft" placeholder="Notes visible only to Gimsc admin..."></textarea>
        </div>

        <!-- Client Login Credentials -->
        <div class="rv-sec-lbl" style="margin-top:8px">Client Portal Access</div>
        <div class="rv-al rv-al-b" style="margin-bottom:16px">
          <i class="ti ti-lock" aria-hidden="true"></i> Set login credentials so the client can access their portal immediately. Leave blank to invite them later via the Client Detail page.
        </div>
        <div class="rv-g2">
          <div class="rv-fg">
            <label class="rv-fl">Client Email (Username)</label>
            <input v-model="form.client_email" class="rv-fi" type="email" placeholder="client@business.co.ke">
          </div>
          <div class="rv-fg">
            <label class="rv-fl">Password</label>
            <div style="position:relative">
              <input
                v-model="form.client_password"
                class="rv-fi"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Min 8 characters"
                style="padding-right:44px">
              <button
                @click="showPassword=!showPassword"
                type="button"
                style="position:absolute;right:12px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--slate-light);font-size:15px">
                <i :class="['ti', showPassword ? 'ti-eye-off' : 'ti-eye']" aria-hidden="true"></i>
              </button>
            </div>
          </div>
        </div>
        <div v-if="form.client_email || form.client_password" class="rv-g2">
          <div style="font-size:12px;color:var(--slate-mid);font-weight:600;padding:8px 12px;background:var(--bg);border-radius:var(--r-md)">
            <div style="font-weight:800;margin-bottom:4px">Login details to share with client:</div>
            <div>URL: <strong>http://localhost:5173</strong></div>
            <div>Email: <strong>{{ form.client_email || '—' }}</strong></div>
            <div>Password: <strong>{{ form.client_password ? '••••••••' : '—' }}</strong></div>
          </div>
        </div>

        <div style="display:flex;gap:12px;margin-top:20px">
          <button class="rv-btn rv-btn-p" @click="create" :disabled="saving">
            <span v-if="saving" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
            <span v-else><i class="ti ti-circle-check" aria-hidden="true"></i> Create Client Account</span>
          </button>
          <button class="rv-btn rv-btn-s" @click="$emit('nav','clients')">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api'

const emit = defineEmits(['nav', 'toast'])
const saving      = ref(false)
const error       = ref('')
const success     = ref('')
const showPassword = ref(false)

const form = ref({
  name: '', contact_name: '', contact_email: '', contact_phone: '',
  currency: 'KES', industry: '', location: '', notes: '',
  client_email: '', client_password: '',
})

async function create() {
  error.value = ''; success.value = ''

  if (!form.value.name.trim()) {
    error.value = 'Business name is required.'
    return
  }
  if (form.value.client_email && !form.value.client_password) {
    error.value = 'Please provide a password for the client login.'
    return
  }
  if (form.value.client_password && form.value.client_password.length < 8) {
    error.value = 'Password must be at least 8 characters.'
    return
  }

  saving.value = true
  try {
    const payload = { ...form.value }
    // Strip credentials if not provided
    if (!payload.client_email)    delete payload.client_email
    if (!payload.client_password) delete payload.client_password

    await api.post('/tenants/', payload)

    const hasCredentials = form.value.client_email && form.value.client_password
    success.value = hasCredentials
      ? `${form.value.name} created! Client can log in at localhost:5173 with ${form.value.client_email}`
      : `${form.value.name} created! Use Client Detail to set up their access.`

    emit('toast', `${form.value.name} created successfully!`, 'green')

    // Reset form
    form.value = { name:'', contact_name:'', contact_email:'', contact_phone:'', currency:'KES', industry:'', location:'', notes:'', client_email:'', client_password:'' }

    setTimeout(() => emit('nav', 'clients'), 2000)

  } catch(e) {
    const data = e.response?.data
    if (data?.name) error.value = `Business name: ${data.name[0]}`
    else if (data?.client_email) error.value = `Client email: ${data.client_email[0]}`
    else if (data?.detail) error.value = data.detail
    else error.value = 'Failed to create client. Please check all fields and try again.'
  }
  saving.value = false
}
</script>
