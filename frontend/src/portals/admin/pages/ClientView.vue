<template>
  <div>
    <!-- Client portal tabs bar -->
    <div style="display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap;align-items:center;padding:12px 16px;background:var(--card);border-radius:var(--r-lg);border:2px solid var(--amber)">
      <div style="font-size:12px;font-weight:800;color:var(--amber);margin-right:8px">👁️ ACTING AS CLIENT:</div>
      <button v-for="t in tabs" :key="t.key"
        @click="activeTab=t.key"
        class="rv-btn rv-btn-sm"
        :class="activeTab===t.key ? 'rv-btn-p' : 'rv-btn-s'"
        style="font-size:12px"
      >{{ t.label }}</button>
      <button @click="$emit('exit')" class="rv-btn rv-btn-sm" style="margin-left:auto;background:var(--amber);color:#000;font-weight:800">✕ Exit Client View</button>
    </div>

    <!-- Render the appropriate client page -->
    <Dashboard     v-if="activeTab==='dashboard'"  />
    <Pipeline      v-if="activeTab==='pipeline'"   />
    <LogSale       v-if="activeTab==='log-sale'"   />
    <SalesHistory  v-if="activeTab==='sales'"      />
    <Customers     v-if="activeTab==='customers'"  />
    <RevenueGoals  v-if="activeTab==='goals'"      />
    <SMS           v-if="activeTab==='sms'"        />
    <BulkUpload    v-if="activeTab==='bulk'"       />
    <Settings      v-if="activeTab==='settings'"  />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Dashboard    from '@/portals/client/pages/Dashboard.vue'
import Pipeline     from '@/portals/client/pages/Pipeline.vue'
import LogSale      from '@/portals/client/pages/LogSale.vue'
import SalesHistory from '@/portals/client/pages/SalesHistory.vue'
import Customers    from '@/portals/client/pages/Customers.vue'
import RevenueGoals from '@/portals/client/pages/RevenueGoals.vue'
import SMS          from '@/portals/client/pages/SMS.vue'
import BulkUpload   from '@/portals/client/pages/BulkUpload.vue'
import Settings     from '@/portals/client/pages/Settings.vue'

defineProps(['tenant'])
defineEmits(['exit', 'nav', 'toast'])

const activeTab = ref('dashboard')

const tabs = [
  { key: 'dashboard',  label: '📊 Dashboard' },
  { key: 'pipeline',   label: '🔥 Pipeline' },
  { key: 'log-sale',   label: '💰 Log Sale' },
  { key: 'sales',      label: '📋 Sales History' },
  { key: 'customers',  label: '👥 Customers' },
  { key: 'goals',      label: '🎯 Revenue Goals' },
  { key: 'sms',        label: '📱 SMS' },
  { key: 'bulk',       label: '📤 Bulk Upload' },
  { key: 'settings',   label: '⚙️ Settings' },
]
</script>
