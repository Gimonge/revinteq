<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="fixed inset-0 bg-slate/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl w-full max-w-[480px] shadow-lg">
          <div class="flex items-center justify-between px-6 py-5 border-b border-border">
            <div class="text-[15px] font-black text-slate">Bulk SMS — {{ selectedIds.length }} recipients</div>
            <button @click="$emit('close')" class="text-slate-light hover:text-slate text-xl">×</button>
          </div>
          <div class="px-6 py-5 space-y-4">
            <div v-if="alert.msg" class="rv-alert" :class="'rv-alert-' + alert.type">{{ alert.msg }}</div>
            <div>
              <label class="rv-label">Message <span class="float-right font-semibold text-slate-light normal-case tracking-normal">{{ message.length }}/160</span></label>
              <textarea v-model="message" maxlength="160" rows="4" class="rv-input" placeholder="Hi {name}, this is a message from Amari Boutique..."></textarea>
            </div>
            <div class="rv-alert rv-alert-blue text-[12px]">
              <i class="ti ti-pin" aria-hidden="true"></i> Only customers with SMS opt-in enabled will receive this message.
            </div>
          </div>
          <div class="px-6 py-4 border-t border-border flex gap-3 justify-end">
            <button @click="$emit('close')" class="rv-btn-secondary">Cancel</button>
            <button @click="send" :disabled="loading || !message" class="rv-btn-primary">
              <span v-if="loading" class="rv-spinner mr-2"></span><i class="ti ti-upload" aria-hidden="true"></i> Send Bulk SMS
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
<script setup>
import { ref } from 'vue'
import { sms as smsApi } from '@/api'
import { useUIStore } from '@/stores'
const props = defineProps({ show: Boolean, selectedIds: Array })
const emit  = defineEmits(['close','sent'])
const ui = useUIStore()
const message = ref('')
const loading = ref(false)
const alert   = ref({ msg: '', type: 'green' })
async function send() {
  loading.value = true
  try {
    const { data } = await smsApi.send({ recipients: props.selectedIds, message: message.value })
    ui.success(data.message); emit('sent')
  } catch (e) {
    alert.value = { msg: e.response?.data?.message || 'Send failed.', type: 'red' }
  } finally { loading.value = false }
}
</script>
