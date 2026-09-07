import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  const sidebarOpen  = ref(true)
  const toasts       = ref([])
  let   toastCounter = 0

  function toast(message, type = 'success', duration = 3200) {
    const id = ++toastCounter
    toasts.value.push({ id, message, type })
    setTimeout(() => dismiss(id), duration)
  }
  function dismiss(id) {
    const idx = toasts.value.findIndex(t => t.id === id)
    if (idx !== -1) toasts.value.splice(idx, 1)
  }
  function success(msg) { toast(msg, 'success') }
  function error(msg)   { toast(msg, 'error', 4500) }
  function warn(msg)    { toast(msg, 'warn', 4000) }

  return { sidebarOpen, toasts, success, error, warn, dismiss }
})
