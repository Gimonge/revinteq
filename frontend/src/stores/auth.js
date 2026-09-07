import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user   = ref(null)
  const tenant = ref(null)
  const accessToken  = ref(localStorage.getItem('rv_access') || '')
  const refreshToken = ref(localStorage.getItem('rv_refresh') || '')

  const isLoggedIn = computed(() => !!accessToken.value && !!user.value)

  async function login(email, password) {
    try {
      const r = await api.post('/auth/login/', { email, password })
      accessToken.value  = r.data.access
      refreshToken.value = r.data.refresh
      user.value   = r.data.user
      tenant.value = r.data.tenant
      localStorage.setItem('rv_access',  r.data.access)
      localStorage.setItem('rv_refresh', r.data.refresh)
      api.defaults.headers.common['Authorization'] = `Bearer ${r.data.access}`
      return true
    } catch(e) {
      return false
    }
  }

  async function fetchUser() {
    if (!accessToken.value) return
    const token = localStorage.getItem('rv_access') || accessToken.value
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    try {
      const r = await api.get('/auth/account/')
      user.value   = r.data
      tenant.value = r.data.tenant
      return r.data
    } catch(e) {
      if (e.response?.status === 401) logout()
    }
  }

  function logout() {
    user.value = null; tenant.value = null
    accessToken.value = ''; refreshToken.value = ''
    localStorage.removeItem('rv_access')
    localStorage.removeItem('rv_refresh')
    delete api.defaults.headers.common['Authorization']
  }

  // Re-attach token on store init
  if (accessToken.value) {
    api.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`
    fetchUser()
  }

  return { user, tenant, accessToken, isLoggedIn, login, fetchUser, logout }
})
