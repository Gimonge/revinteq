import axios from 'axios'

// In production, API lives at api.revinteq.com
// In local dev, API is proxied via Vite at /api (localhost:8000)
const isProduction = !window.location.hostname.includes('localhost') &&
                     !window.location.hostname.includes('127.0.0.1')

const API_BASE = isProduction
  ? 'https://api.revinteq.com/api/v1'
  : '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor — attach token + impersonation header ─
api.interceptors.request.use(config => {
  const token = localStorage.getItem('rv_access')
  if (token) config.headers['Authorization'] = `Bearer ${token}`

  // If admin is impersonating a client, send tenant ID as header
  // so the backend middleware switches tenant context for this request
  const impersonateTenantId = localStorage.getItem('rv_impersonate_tenant')
  if (impersonateTenantId) {
    config.headers['X-Impersonate-Tenant'] = impersonateTenantId
  }

  return config
})

// ── Impersonation helpers (called by AdminApp.vue) ────────────
export function setImpersonateTenant(tenantId) {
  if (tenantId) localStorage.setItem('rv_impersonate_tenant', tenantId)
  else localStorage.removeItem('rv_impersonate_tenant')
}

export function getImpersonateTenant() {
  return localStorage.getItem('rv_impersonate_tenant')
}

export function clearImpersonateTenant() {
  localStorage.removeItem('rv_impersonate_tenant')
}

// ── Response interceptor — auto-refresh on 401 ───────────────
let isRefreshing = false
let failedQueue  = []

function processQueue(error, token = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token)
  })
  failedQueue = []
}

api.interceptors.response.use(
  response => response,
  async error => {
    const original = error.config

    // Only handle 401 and only retry once
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }

    const refreshToken = localStorage.getItem('rv_refresh')
    if (!refreshToken) {
      localStorage.removeItem('rv_access')
      localStorage.removeItem('rv_refresh')
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then(token => {
        original.headers['Authorization'] = `Bearer ${token}`
        return api(original)
      }).catch(err => Promise.reject(err))
    }

    original._retry = true
    isRefreshing    = true

    try {
      const r = await axios.post(`${API_BASE}/auth/token/refresh/`, {
        refresh: refreshToken,
      })

      const newAccess = r.data.access
      localStorage.setItem('rv_access', newAccess)
      api.defaults.headers.common['Authorization'] = `Bearer ${newAccess}`
      if (r.data.refresh) localStorage.setItem('rv_refresh', r.data.refresh)

      processQueue(null, newAccess)
      original.headers['Authorization'] = `Bearer ${newAccess}`
      return api(original)

    } catch (refreshError) {
      processQueue(refreshError, null)
      localStorage.removeItem('rv_access')
      localStorage.removeItem('rv_refresh')
      localStorage.removeItem('rv_impersonate_tenant')
      window.location.reload()
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default api
