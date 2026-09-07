<template>
  <div>
    <AdminApp v-if="showAdmin" />
    <ClientApp v-else />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AdminApp from './portals/admin/AdminApp.vue'
import ClientApp from './portals/client/ClientApp.vue'

const auth = useAuthStore()

// Show admin portal if:
// 1. Hostname is admin.revinteq.com (production subdomain), OR
// 2. URL path starts with /admin (local dev), OR
// 3. User is logged in with admin role
const hostname    = window.location.hostname
const isAdminHost = hostname.startsWith('admin.')
const isAdminPath = ref(isAdminHost || window.location.pathname.startsWith('/admin'))

const showAdmin = computed(() =>
  isAdminPath.value ||
  auth.user?.role === 'SUPER_ADMIN' ||
  auth.user?.role === 'ADMIN'
)

onMounted(() => {
  if (auth.user?.role === 'SUPER_ADMIN' || auth.user?.role === 'ADMIN') {
    isAdminPath.value = true
  }
})
</script>
