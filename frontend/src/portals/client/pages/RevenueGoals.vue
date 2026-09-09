<template>
  <div style="display:flex;flex-direction:column;gap:18px">
    <div class="rv-page-header fade-up">
      <div><div style="font-size:21px;font-weight:900;letter-spacing:-.4px">Revenue Goals</div><div style="font-size:13px;color:var(--slate-light);font-weight:600;margin-top:3px">Set monthly targets to activate the GPS tracker</div></div>
      <button class="rv-btn rv-btn-p" @click="showNew=true">+ Set Goal</button>
    </div>

    <!-- Current month GPS -->
    <div v-if="currentGoal" class="rv-gps card-reveal" :class="gpsClass">
      <div>
        <div class="rv-gps-lbl">Revenue GPS — {{ monthLabel }}</div>
        <div class="rv-gps-status"><i :class="['ti', gpsIcon]" aria-hidden="true"></i> {{ gpsTitle }}</div>
        <div class="rv-gps-sub">Target: {{ fmtK(currentGoal.target_amount) }} &bull; Achieved: {{ fmtK(achieved) }}</div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div class="rv-gps-pct">{{ pct }}%</div>
        <div class="rv-gps-pct-lbl">Goal progress</div>
      </div>
    </div>
    <div v-else class="rv-al rv-al-b card-reveal"><i class="ti ti-bulb" aria-hidden="true"></i> No goal set for this month. Click "Set Goal" to activate the Revenue GPS tracker.</div>

    <!-- Goals table -->
    <div class="rv-card card-reveal" style="animation-delay:.1s">
      <div class="rv-ch"><div class="rv-ct">Monthly Goals History</div></div>
      <div v-if="loading" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else class="rv-tw">
        <table class="rv-table">
          <thead><tr><th>Month</th><th>Target</th><th>Achieved</th><th>Progress</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="g in goals" :key="g.id">
              <td><strong>{{ formatMonth(g.month) }}</strong></td>
              <td>{{ fmtK(g.target_amount) }}</td>
              <td>{{ fmtK(g.achieved||0) }}</td>
              <td>
                <div style="display:flex;align-items:center;gap:8px">
                  <div style="flex:1;background:var(--bg);border-radius:4px;height:8px;overflow:hidden">
                    <div :style="{width:Math.min((g.achieved||0)/g.target_amount*100,100)+'%',height:'100%',background:'var(--green)',borderRadius:'4px'}"></div>
                  </div>
                  <span style="font-size:12px;font-weight:800;min-width:36px">{{ Math.round((g.achieved||0)/g.target_amount*100) }}%</span>
                </div>
              </td>
              <td><span class="rv-badge" :class="goalBadge(g)">{{ goalStatus(g) }}</span></td>
              <td @click.stop>
                <div style="display:flex;gap:4px">
                  <button class="rv-btn rv-btn-b rv-btn-xs" @click="openEditGoal(g)"><i class="ti ti-pencil" aria-hidden="true"></i></button>
                  <button class="rv-btn rv-btn-d rv-btn-xs" @click="deleteGoal(g)"><i class="ti ti-trash" aria-hidden="true"></i></button>
                </div>
              </td>
            </tr>
            <tr v-if="goals.length===0"><td colspan="6" style="text-align:center;color:var(--slate-light);padding:32px">No goals set yet</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- New goal modal -->
    <div v-if="showNew" style="position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px" @click.self="showNew=false">
      <div style="background:var(--card);border-radius:var(--r-xl);width:100%;max-width:420px;box-shadow:var(--shadow-lg);animation:fadeUp .3s ease">
        <div style="padding:20px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between">
          <span style="font-size:16px;font-weight:900">Set Monthly Goal</span>
          <button @click="showNew=false" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--slate-light)">×</button>
        </div>
        <div style="padding:24px">
          <div class="rv-fg"><label class="rv-fl">Month</label><input v-model="newGoal.month" class="rv-fi" type="month"></div>
          <div class="rv-fg"><label class="rv-fl">Target Amount ({{ currency }})</label><input v-model="newGoal.target_amount" class="rv-fi" type="number" placeholder="e.g. 400000" min="1"></div>
          <div class="rv-fg"><label class="rv-fl">Notes (optional)</label><input v-model="newGoal.notes" class="rv-fi" placeholder="e.g. Target for summer campaign"></div>
        </div>
        <div style="padding:16px 24px;border-top:1px solid var(--border);display:flex;gap:10px;justify-content:flex-end">
          <button class="rv-btn rv-btn-s" @click="showNew=false">Cancel</button>
          <button class="rv-btn rv-btn-p" @click="createGoal" :disabled="saving">
            <span v-if="saving" class="rv-spin" style="width:14px;height:14px;border-width:2px"></span>
            <span v-else>Set Goal</span>
          </button>
        </div>
      </div>
    </div>
  </div>
  <!-- Edit Goal Modal -->
  <div v-if="editGoal" style="position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;display:flex;align-items:center;justify-content:center;padding:16px">
    <div class="rv-card" style="width:100%;max-width:400px">
      <div class="rv-ch">
        <div class="rv-ct">Edit Goal — {{ editForm.month }}</div>
        <button @click="editGoal=null" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--slate-light)"><i class="ti ti-x" aria-hidden="true"></i></button>
      </div>
      <div class="rv-cb" style="display:flex;flex-direction:column;gap:12px">
        <div class="rv-fg" style="margin:0">
          <label class="rv-fl">Target Amount ({{ currency }})</label>
          <input :value="commaify(editForm.target_amount)" @input="e=>editForm.target_amount=stripCommas(e.target.value)" class="rv-fi" inputmode="numeric">
        </div>
        <div style="display:flex;gap:8px">
          <button class="rv-btn rv-btn-p" @click="saveGoal" :disabled="savingGoal">
            <span v-if="savingGoal" class="rv-spin" style="width:12px;height:12px;border-width:2px"></span>
            <span v-else><i class="ti ti-device-floppy" aria-hidden="true"></i> Save</span>
          </button>
          <button class="rv-btn rv-btn-s" @click="editGoal=null">Cancel</button>
        </div>
      </div>
    </div>
  </div>

</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'
import { fmtK as _fmtK, fmtFull, fmtNum, commaify, stripCommas } from '@/utils/format'

const emit = defineEmits(['toast'])
const auth = useAuthStore()
const goals = ref([]), loading = ref(true), showNew = ref(false), saving = ref(false)
const achieved = ref(0)
const newGoal = ref({ month: dayjs().format('YYYY-MM'), target_amount:'', notes:'' })
const currency = computed(() => auth.tenant?.currency || 'KES')
const monthLabel = computed(() => dayjs().format('MMMM YYYY'))
const currentGoal = computed(() => goals.value.find(g => g.month?.startsWith(dayjs().format('YYYY-MM'))))
const pct = computed(() => currentGoal.value ? Math.round((achieved.value/currentGoal.value.target_amount)*100) : 0)
const gpsClass = computed(() => pct.value>=100?'ahead':pct.value>=60?'on_track':pct.value>0?'behind':'no_goal')
const gpsIcon  = computed(() => ({ahead:'ti-rocket',on_track:'ti-circle-check',behind:'ti-alert-triangle',no_goal:'ti-map-pin'})[gpsClass.value])
const gpsTitle = computed(() => ({ahead:'Ahead of Goal',on_track:'On Track',behind:'Behind Goal',no_goal:'No Goal'})[gpsClass.value])

function fmtK(v, cur) {
  return _fmtK(v, cur || auth.tenant?.currency || 'KES')
}
function formatMonth(m) { return m ? dayjs(m).format('MMMM YYYY') : '—' }
function goalStatus(g) { const p=(g.achieved||0)/g.target_amount*100; return p>=100?'Achieved':p>=80?'Near':p>=50?'Progress':'Behind' }
function goalBadge(g)  { const p=(g.achieved||0)/g.target_amount*100; return p>=100?'rv-bg':p>=50?'rv-bb':'rv-ba' }

async function loadGoals() {
  loading.value = true
  try { const r = await api.get('/revenue-goals/'); goals.value = r.data.results || r.data || [] } catch(e) {}
  try { const r = await api.get('/metrics/snapshot/'); achieved.value = r.data?.total_revenue || 0 } catch(e) {}
  loading.value = false
}
async function createGoal() {
  if (!newGoal.value.target_amount) return
  saving.value = true
  try {
    const r = await api.post('/revenue-goals/', { ...newGoal.value, month: newGoal.value.month + '-01' })
    goals.value.unshift(r.data)
    showNew.value = false
    emit('toast','Revenue goal set!','green')
  } catch(e) { emit('toast','Failed to set goal','red') }
  saving.value = false
}
const editGoal   = ref(null)
const editForm   = ref({})
const savingGoal = ref(false)

function openEditGoal(g) {
  editGoal.value = g
  editForm.value = { target_amount: g.target_amount, month: formatMonth(g.month) }
}
async function saveGoal() {
  savingGoal.value = true
  try {
    await api.patch(`/revenue-goals/${editGoal.value.id}/`, { target_amount: editForm.value.target_amount })
    editGoal.value.target_amount = editForm.value.target_amount
    editGoal.value = null
  } catch(e) {}
  savingGoal.value = false
}
async function deleteGoal(g) {
  if (!confirm(`Delete goal for ${formatMonth(g.month)}? This cannot be undone.`)) return
  try {
    await api.delete(`/revenue-goals/${g.id}/`)
    goals.value = goals.value.filter(x => x.id !== g.id)
  } catch(e) {}
}

useAutoRefresh(loadGoals, 60000)
</script>
