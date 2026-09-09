/**
 * Revinteq v3 — Vue Router
 * Client portal routes + admin portal routes.
 * Auth guard redirects unauthenticated users to login.
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores'

// ── Client Portal Pages ────────────────────────────────────────
const Dashboard     = () => import('@/portals/client/pages/Dashboard.vue')
const Analytics     = () => import('@/portals/client/pages/Analytics.vue')
const Pipeline      = () => import('@/portals/client/pages/Pipeline.vue')
const SalesHistory  = () => import('@/portals/client/pages/SalesHistory.vue')
const FacebookAds   = () => import('@/portals/client/pages/FacebookAds.vue')
const InstagramAds  = () => import('@/portals/client/pages/InstagramAds.vue')
const RevenueGoals  = () => import('@/portals/client/pages/RevenueGoals.vue')
const SMS           = () => import('@/portals/client/pages/SMS.vue')
const Customers     = () => import('@/portals/client/pages/Customers.vue')
const Settings      = () => import('@/portals/client/pages/Settings.vue')
const ClientLogin   = () => import('@/portals/client/pages/Login.vue')

// ── Admin Portal Pages ─────────────────────────────────────────
const AdminOverview      = () => import('@/portals/admin/pages/Overview.vue')
const AdminClients       = () => import('@/portals/admin/pages/Clients.vue')
const AdminClientDetail  = () => import('@/portals/admin/pages/ClientDetail.vue')
const AdminAnalytics     = () => import('@/portals/admin/pages/Analytics.vue')
const AdminRecommendations = () => import('@/portals/admin/pages/Recommendations.vue')
const AdminLogin         = () => import('@/portals/admin/pages/Login.vue')

const routes = [
  // ── Auth ──────────────────────────────────────────────────
  { path: '/login',         name: 'client-login', component: ClientLogin,  meta: { public: true } },
  { path: '/admin/login',   name: 'admin-login',  component: AdminLogin,   meta: { public: true } },

  // ── Client Portal ─────────────────────────────────────────
  { path: '/',              name: 'dashboard',    component: Dashboard,    meta: { role: 'client' } },
  { path: '/analytics',     name: 'analytics',    component: Analytics,    meta: { role: 'client' } },
  { path: '/pipeline',      name: 'pipeline',     component: Pipeline,     meta: { role: 'client' } },
  { path: '/sales',         name: 'sales',        component: SalesHistory, meta: { role: 'client' } },
  { path: '/facebook-ads',  name: 'facebook-ads', component: FacebookAds,  meta: { role: 'client' } },
  { path: '/instagram-ads', name: 'instagram-ads',component: InstagramAds, meta: { role: 'client' } },
  { path: '/goals',         name: 'goals',        component: RevenueGoals, meta: { role: 'client' } },
  { path: '/sms',           name: 'sms',          component: SMS,          meta: { role: 'client' } },
  { path: '/customers',     name: 'customers',    component: Customers,    meta: { role: 'client' } },
  { path: '/settings',      name: 'settings',     component: Settings,     meta: { role: 'client' } },

  // ── Admin Portal ──────────────────────────────────────────
  { path: '/admin',                     name: 'admin-overview', component: AdminOverview,       meta: { role: 'admin' } },
  { path: '/admin/clients',             name: 'admin-clients',  component: AdminClients,        meta: { role: 'admin' } },
  { path: '/admin/clients/:id',         name: 'admin-client',   component: AdminClientDetail,   meta: { role: 'admin' } },
  { path: '/admin/analytics',           name: 'admin-analytics',component: AdminAnalytics,      meta: { role: 'admin' } },
  { path: '/admin/recommendations',     name: 'admin-recs',     component: AdminRecommendations,meta: { role: 'admin' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// ── Navigation Guard ─────────────────────────────────────────
router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.public) return true

  if (!auth.isAuthenticated) {
    return to.meta.role === 'admin'
      ? { name: 'admin-login' }
      : { name: 'client-login' }
  }

  if (to.meta.role === 'admin' && !auth.isAdmin) {
    return { name: 'dashboard' }
  }

  if (to.meta.role === 'client' && auth.isAdmin && !auth.isImpersonating) {
    return { name: 'admin-overview' }
  }

  return true
})

export default router
