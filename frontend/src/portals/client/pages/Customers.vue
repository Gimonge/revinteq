<template>
  <div style="display:flex;flex-direction:column;gap:18px">
    <div style="display:flex;align-items:flex-start;justify-content:space-between" class="fade-up">
      <div><div style="font-size:21px;font-weight:900;letter-spacing:-.4px">Customers</div><div style="font-size:13px;color:var(--slate-light);font-weight:600;margin-top:3px">{{ customers.length }} customers in your CRM</div></div>
      <input v-model="search" class="rv-fi" placeholder="🔍 Search customers..." style="width:220px;padding:7px 12px;font-size:12.5px">
    </div>

    <div class="rv-card card-reveal">
      <div v-if="loading" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else-if="filtered.length===0" class="rv-empty">
        <div class="rv-empty-icon">👥</div>
        <div class="rv-empty-title">{{ search ? 'No customers found' : 'No customers yet' }}</div>
        <div class="rv-empty-sub">{{ search ? 'Try a different search' : 'Customers appear automatically when sales are logged' }}</div>
      </div>
      <div v-else class="rv-tw">
        <table class="rv-table">
          <thead><tr><th>Customer</th><th>Phone</th><th>Source</th><th>Purchases</th><th>Total Spend</th><th>Last Contact</th><th>SMS</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="c in filtered" :key="c.id">
              <td>
                <div style="display:flex;align-items:center;gap:10px">
                  <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,var(--green),var(--blue));display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;color:#fff;flex-shrink:0">{{ (c.name||'?')[0].toUpperCase() }}</div>
                  <div>
                    <div style="font-weight:800">{{ c.name || '—' }}</div>
                    <div style="font-size:11px;color:var(--slate-light);font-weight:600">{{ c.email||'' }}</div>
                  </div>
                </div>
              </td>
              <td>{{ c.phone_number||'—' }}</td>
              <td><span class="rv-badge" :class="c.source_platform==='instagram'?'rv-big':'rv-bb'">{{ c.source_platform }}</span></td>
              <td>{{ c.total_purchases||0 }}</td>
              <td><strong>{{ fmtK(c.total_spend) }}</strong></td>
              <td>{{ formatDate(c.last_contact_date) }}</td>
              <td><span class="rv-badge" :class="c.sms_opt_in?'rv-bg':'rv-bgy'">{{ c.sms_opt_in?'✓ In':'Opt-out' }}</span></td>
              <td @click.stop>
                <div style="display:flex;gap:4px">
                  <button class="rv-btn rv-btn-b rv-btn-xs" @click="openEdit(c)">✏️</button>
                  <button class="rv-btn rv-btn-d rv-btn-xs" @click="deleteCustomer(c)">🗑️</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
  <!-- Edit Customer Modal -->
  <div v-if="editCustomer" style="position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;display:flex;align-items:center;justify-content:center;padding:16px">
    <div class="rv-card" style="width:100%;max-width:480px">
      <div class="rv-ch">
        <div class="rv-ct">Edit Customer</div>
        <button @click="editCustomer=null" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--slate-light)">✕</button>
      </div>
      <div class="rv-cb" style="display:flex;flex-direction:column;gap:12px">
        <div class="rv-fg" style="margin:0"><label class="rv-fl">Name</label><input v-model="editForm.name" class="rv-fi"></div>
        <div class="rv-fg" style="margin:0"><label class="rv-fl">Phone</label><input v-model="editForm.phone_number" class="rv-fi"></div>
        <div class="rv-fg" style="margin:0"><label class="rv-fl">Email</label><input v-model="editForm.email" class="rv-fi" type="email"></div>
        <div class="rv-fg" style="margin:0"><label class="rv-fl">Tags (comma separated)</label><input v-model="editForm.tags" class="rv-fi" placeholder="VIP, Wholesale, Repeat"></div>
        <div style="display:flex;align-items:center;gap:10px">
          <label class="rv-fl" style="margin:0">SMS Opt-in</label>
          <input type="checkbox" v-model="editForm.sms_opt_in" style="width:16px;height:16px">
        </div>
        <div style="display:flex;gap:8px;margin-top:4px">
          <button class="rv-btn rv-btn-p" @click="saveEdit" :disabled="saving">
            <span v-if="saving" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
            <span v-else>💾 Save</span>
          </button>
          <button class="rv-btn rv-btn-s" @click="editCustomer=null">Cancel</button>
        </div>
      </div>
    </div>
  </div>

</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'
import { fmtK as _fmtK, fmtFull, fmtNum } from '@/utils/format'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

const auth = useAuthStore()
const customers = ref([]), loading = ref(true), search = ref('')
const currency = computed(() => auth.tenant?.currency||'KES')
const filtered = computed(() => { if(!search.value) return customers.value; const q=search.value.toLowerCase(); return customers.value.filter(c=>(c.name||'').toLowerCase().includes(q)||(c.phone_number||'').includes(q)) })
function fmtK(v, cur) {
  return _fmtK(v, cur || auth.tenant?.currency || 'KES')
}
function formatDate(d) { return d ? dayjs(d).format('D MMM YYYY') : '—' }

async function loadData() {
  loading.value = true
  try { const r = await api.get('/customers/'); customers.value = r.data.results || r.data || [] } catch(e) {}
  loading.value = false
}
const editCustomer = ref(null)
const editForm     = ref({})
const saving       = ref(false)

function openEdit(c) {
  editCustomer.value = c
  editForm.value = { name: c.name, phone_number: c.phone_number, email: c.email||'', tags: c.tags||'', sms_opt_in: c.sms_opt_in }
}
async function saveEdit() {
  saving.value = true
  try {
    await api.patch(`/customers/${editCustomer.value.id}/`, editForm.value)
    Object.assign(editCustomer.value, editForm.value)
    editCustomer.value = null
  } catch(e) {}
  saving.value = false
}
async function deleteCustomer(c) {
  if (!confirm(`Delete ${c.name || 'this customer'}? This cannot be undone.`)) return
  try {
    await api.delete(`/customers/${c.id}/`)
    customers.value = customers.value.filter(x => x.id !== c.id)
  } catch(e) {}
}

useAutoRefresh(loadData, 45000)
</script>
