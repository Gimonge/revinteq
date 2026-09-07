<template>
  <div style="min-height:100vh;background:var(--bg-client);display:flex;align-items:center;justify-content:center;font-family:var(--font)">
    <div style="background:var(--card);border-radius:var(--r-xl);border:1px solid var(--border);box-shadow:var(--shadow-lg);padding:40px;width:100%;max-width:400px">
      <div style="text-align:center;margin-bottom:28px">
        <div class="rv-logo-mark" style="font-size:26px;justify-content:center;display:flex">
          <span>Revinteq</span>
        </div>
        <div style="font-size:13px;color:var(--slate-light);margin-top:8px;font-weight:600">Client Portal — Sign In</div>
      </div>
      <div v-if="error" class="rv-al rv-al-r" style="margin-bottom:16px">{{ error }}</div>
      <div class="rv-fg"><label class="rv-fl">Email</label><input v-model="email" class="rv-fi" type="email" placeholder="you@business.co.ke" @keyup.enter="login"></div>
      <div class="rv-fg"><label class="rv-fl">Password</label><input v-model="password" class="rv-fi" type="password" placeholder="••••••••" @keyup.enter="login"></div>
      <button class="rv-btn rv-btn-p" style="width:100%;justify-content:center;margin-top:4px" @click="login" :disabled="loading">
        <span v-if="loading" class="rv-spin" style="width:16px;height:16px;border-width:2px"></span>
        <span v-else>🔐 Sign In</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits(['success'])
const auth = useAuthStore()
const email = ref(''), password = ref(''), loading = ref(false), error = ref('')

async function login() {
  if (!email.value || !password.value) { error.value = 'Email and password required.'; return }
  loading.value = true; error.value = ''
  const ok = await auth.login(email.value, password.value)
  if (ok) emit('success')
  else error.value = 'Invalid email or password.'
  loading.value = false
}
</script>
