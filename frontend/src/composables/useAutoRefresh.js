/**
 * useAutoRefresh — auto-polls a data loader on a configurable interval.
 *
 * Usage:
 *   import { useAutoRefresh } from '@/composables/useAutoRefresh'
 *
 *   async function loadData() { ... }
 *
 *   // Refresh every 30 seconds, pause when tab is hidden
 *   useAutoRefresh(loadData, 30_000)
 *
 * The composable:
 *  - Calls loadData() immediately on mount
 *  - Repeats every `intervalMs` milliseconds
 *  - Pauses when the browser tab is hidden (saves API calls)
 *  - Resumes + refreshes immediately when tab becomes visible again
 *  - Clears the timer on component unmount (no memory leaks)
 *  - Shows a subtle "last updated" timestamp
 */
import { ref, onMounted, onUnmounted } from 'vue'

export function useAutoRefresh(loadFn, intervalMs = 30_000) {
  const lastUpdated = ref(null)
  const refreshing  = ref(false)
  let timer = null

  async function refresh() {
    if (refreshing.value) return   // prevent overlapping calls
    refreshing.value = true
    try {
      await loadFn()
      lastUpdated.value = new Date()
    } catch(e) {
      // silently fail — don't break the UI on network hiccup
    } finally {
      refreshing.value = false
    }
  }

  function start() {
    stop()
    timer = setInterval(refresh, intervalMs)
  }

  function stop() {
    if (timer) { clearInterval(timer); timer = null }
  }

  // Pause when tab hidden, resume when visible
  function onVisibilityChange() {
    if (document.hidden) {
      stop()
    } else {
      refresh()   // immediate refresh on return
      start()
    }
  }

  onMounted(() => {
    refresh()   // initial load
    start()
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onUnmounted(() => {
    stop()
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return { lastUpdated, refreshing, refresh }
}
