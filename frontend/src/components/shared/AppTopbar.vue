<template>
  <header class="h-14 bg-white border-b border-border flex items-center justify-between px-6 sticky top-0 z-40 shadow-card">
    <div class="text-[17px] font-black text-slate tracking-tight">{{ title }}</div>
    <div class="flex items-center gap-3">
      <!-- Impersonation banner -->
      <div v-if="auth.isImpersonating" class="flex items-center gap-2 bg-amber text-white text-xs font-black px-3.5 py-1.5 rounded-full">
        <span><i class="ti ti-eye" aria-hidden="true"></i> Viewing as: <strong>{{ auth.tenantName }}</strong></span>
        <button @click="stopImpersonate" class="bg-white/25 hover:bg-white/40 rounded-full px-2 py-0.5 transition-colors">Exit</button>
      </div>
      <span class="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-black bg-green-light text-green">
        {{ auth.currency }}
      </span>
      <button @click="auth.logout().then(() => router.push('/login'))"
        class="text-xs font-bold text-slate-light hover:text-slate transition-colors">
        Logout
      </button>
    </div>
  </header>
</template>

<script setup>
import { useAuthStore } from '@/stores'
import { useRouter } from 'vue-router'
import { tenants } from '@/api'

const props  = defineProps({ title: { type: String, default: '' } })
const auth   = useAuthStore()
const router = useRouter()

async function stopImpersonate() {
  await tenants.stopImpersonate()
  auth.stopImpersonating()
  router.push('/admin')
}
</script>
