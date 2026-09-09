<template>
  <div style="display:flex;flex-direction:column;gap:18px">
    <div class="fade-up">
      <div style="font-size:21px;font-weight:900;letter-spacing:-.4px">Bulk Upload</div>
      <div style="font-size:13px;color:var(--slate-light);font-weight:600;margin-top:3px">Upload an Excel file to log multiple sales at once</div>
    </div>

    <!-- Step 1: Upload -->
    <div v-if="step==='upload'" class="rv-card card-reveal">
      <div class="rv-ch"><span class="rv-ct">Upload Excel File</span>
        <button class="rv-btn rv-btn-s rv-btn-sm" @click="downloadTemplate"><i class="ti ti-arrow-down" aria-hidden="true"></i> Download Template</button>
      </div>
      <div class="rv-cb">
        <div class="rv-al rv-al-b" style="margin-bottom:16px"><i class="ti ti-clipboard-list" aria-hidden="true"></i> Download the template above, fill in your sales data, then upload it here. Maximum 5MB, .xlsx format.</div>
        <div class="rv-upload-zone" @click="$refs.fileInput.click()" @dragover.prevent @drop.prevent="onDrop">
          <div style="font-size:40px;margin-bottom:12px"><i class="ti ti-upload" aria-hidden="true"></i></div>
          <div style="font-size:15px;font-weight:800;color:var(--slate);margin-bottom:6px">Click to select file or drag and drop</div>
          <div style="font-size:13px;color:var(--slate-light);font-weight:600">.xlsx files only &bull; Max 5MB</div>
          <div v-if="selectedFile" style="margin-top:12px;font-size:13px;font-weight:800;color:var(--green)"><i class="ti ti-circle-check" aria-hidden="true"></i> {{ selectedFile.name }}</div>
        </div>
        <input ref="fileInput" type="file" accept=".xlsx,.xls" style="display:none" @change="onFileSelect">
        <div v-if="uploadError" class="rv-al rv-al-r" style="margin-top:12px">{{ uploadError }}</div>
        <button v-if="selectedFile" class="rv-btn rv-btn-p" style="margin-top:14px" @click="uploadFile" :disabled="uploading">
          <span v-if="uploading" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
          <span v-else><i class="ti ti-upload" aria-hidden="true"></i> Preview Upload</span>
        </button>
      </div>
    </div>

    <!-- Step 2: Preview -->
    <div v-if="step==='preview'" style="display:flex;flex-direction:column;gap:16px">
      <div class="rv-g2">
        <div class="rv-sc card-reveal"><div class="rv-sc-label">Total Rows</div><div class="rv-sc-value">{{ preview.total_rows }}</div></div>
        <div class="rv-sc card-reveal b" style="animation-delay:.05s"><div class="rv-sc-label">Valid Rows</div><div class="rv-sc-value">{{ preview.valid_rows }}</div></div>
        <div class="rv-sc card-reveal r" style="animation-delay:.1s"><div class="rv-sc-label">Error Rows</div><div class="rv-sc-value">{{ preview.error_rows }}</div></div>
        <div class="rv-sc card-reveal a" style="animation-delay:.15s"><div class="rv-sc-label">Total Amount</div><div class="rv-sc-value">{{ fmtK(totalAmount) }}</div></div>
      </div>
      <div class="rv-card card-reveal">
        <div class="rv-ch">
          <span class="rv-ct">Preview</span>
          <div style="display:flex;gap:8px">
            <button class="rv-btn rv-btn-s rv-btn-sm" @click="step='upload';selectedFile=null"><i class="ti ti-arrow-left" aria-hidden="true"></i> Re-upload</button>
            <button class="rv-btn rv-btn-p rv-btn-sm" @click="confirmUpload" :disabled="confirming||preview.valid_rows===0">
              <span v-if="confirming" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
              <span v-else><i class="ti ti-circle-check" aria-hidden="true"></i> Confirm &amp; Save {{ preview.valid_rows }} Sales</span>
            </button>
          </div>
        </div>
        <div class="rv-tw">
          <table class="rv-table">
            <thead><tr><th>Row</th><th>Customer</th><th>Product</th><th>Amount</th><th>Payment</th><th>Platform</th><th>Date</th><th>Status</th></tr></thead>
            <tbody>
              <tr v-for="row in preview.preview" :key="row.row_num" :class="row.status==='valid'?'rv-prev-v':'rv-prev-e'">
                <td>{{ row.row_num }}</td>
                <td>
                  <div v-if="row.data?.customer_name" style="font-weight:700;font-size:12px">{{ row.data.customer_name }}</div>
                  <div v-if="row.data?.customer_phone" style="font-size:11px;color:var(--slate-mid)">{{ row.data.customer_phone }}</div>
                  <span v-if="!row.data?.customer_name && !row.data?.customer_phone" style="color:var(--slate-light)">—</span>
                </td>
                <td>{{ row.data?.product_name || '—' }}</td>
                <td>{{ row.data?.amount ? fmtK(parseFloat(row.data.amount)) : '—' }}</td>
                <td>{{ row.data?.payment_method || '—' }}</td>
                <td>{{ row.data?.platform_source || '—' }}</td>
                <td>{{ row.data?.sale_date || '—' }}</td>
                <td>
                  <span v-if="row.status==='valid'" class="rv-badge rv-bg"><i class="ti ti-check" aria-hidden="true"></i> Valid</span>
                  <span v-else class="rv-badge rv-br" :title="row.errors.join(', ')"><i class="ti ti-x" aria-hidden="true"></i> Error</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Step 3: Done -->
    <div v-if="step==='done'" class="rv-card card-reveal">
      <div class="rv-cb" style="text-align:center;padding:48px 20px">
        <div style="font-size:48px;margin-bottom:16px"><i class="ti ti-circle-check" aria-hidden="true"></i></div>
        <div style="font-size:20px;font-weight:900;margin-bottom:8px">Upload Complete!</div>
        <div style="font-size:14px;color:var(--slate-mid);font-weight:600;margin-bottom:24px">{{ result.saved_rows }} sales saved successfully. Total: {{ fmtK(result.total_amount) }}</div>
        <button class="rv-btn rv-btn-p" @click="reset">Upload Another File</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/api'
import { fmtK as _fmtK } from '@/utils/format'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits(['toast'])
const auth = useAuthStore()
const currency  = computed(() => auth.tenant?.currency || 'KES')
const step       = ref('upload')
const selectedFile = ref(null)
const uploading  = ref(false)
const confirming = ref(false)
const uploadError = ref('')
const preview    = ref({ total_rows:0, valid_rows:0, error_rows:0, preview:[] })
const result     = ref({})
const uploadId   = ref('')
async function downloadTemplate() {
  try {
    const r = await api.get('/bulk-upload/template/', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([r.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = 'revinteq-sales-template.xlsx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch(e) {
    emit('toast', 'Failed to download template', 'red')
  }
}
const totalAmount = computed(() => preview.value.preview?.filter(r=>r.status==='valid').reduce((s,r)=>s+parseFloat(r.data?.amount||0),0)||0)

function fmtK(v, cur) {
  return _fmtK(v, cur || auth.tenant?.currency || 'KES')
}
function onFileSelect(e) { selectedFile.value = e.target.files[0]; uploadError.value = '' }
function onDrop(e) { selectedFile.value = e.dataTransfer.files[0]; uploadError.value = '' }

async function uploadFile() {
  if (!selectedFile.value) return
  uploading.value = true; uploadError.value = ''
  try {
    const fd = new FormData(); fd.append('file', selectedFile.value)
    const r = await api.post('/bulk-upload/upload/', fd, { headers:{'Content-Type':'multipart/form-data'} })
    preview.value = r.data; uploadId.value = r.data.upload_id; step.value = 'preview'
  } catch(e) { uploadError.value = e.response?.data?.message || 'Upload failed. Check the file format.' }
  uploading.value = false
}
async function confirmUpload() {
  confirming.value = true
  try { const r = await api.post(`/bulk-upload/${uploadId.value}/confirm/`); result.value = r.data; step.value = 'done'; emit('toast',`${r.data.saved_rows} sales saved!`,'green') } catch(e) { emit('toast','Confirm failed','red') }
  confirming.value = false
}
function reset() { step.value='upload'; selectedFile.value=null; preview.value={total_rows:0,valid_rows:0,error_rows:0,preview:[]}; uploadId.value='' }
</script>
