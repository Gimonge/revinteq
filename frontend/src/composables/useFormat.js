/**
 * Revinteq v3 — Formatting Composable
 * Currency, dates, percentages — used everywhere.
 */
import { computed } from 'vue'
import { useAuthStore } from '@/stores'
import dayjs from 'dayjs'

export function useFormat() {
  const auth = useAuthStore()

  function fmtMoney(value, currency) {
    const c = currency || auth.currency || 'KES'
    if (value === null || value === undefined) return '—'
    const n = Number(value)
    if (isNaN(n)) return '—'
    return `${c} ${n.toLocaleString('en-KE', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
  }

  function fmtNumber(value) {
    if (value === null || value === undefined) return '—'
    return Number(value).toLocaleString('en-KE')
  }

  function fmtPct(value, decimals = 1) {
    if (value === null || value === undefined) return '—'
    return `${Number(value).toFixed(decimals)}%`
  }

  function fmtDate(value, format = 'DD MMM YYYY') {
    if (!value) return '—'
    return dayjs(value).format(format)
  }

  function fmtDateTime(value) {
    if (!value) return '—'
    return dayjs(value).format('DD MMM YYYY, HH:mm')
  }

  function fmtRelative(value) {
    if (!value) return '—'
    const d = dayjs(value)
    const now = dayjs()
    const diffH = now.diff(d, 'hour')
    if (diffH < 1)  return 'Just now'
    if (diffH < 24) return `${diffH}h ago`
    const diffD = now.diff(d, 'day')
    if (diffD < 7)  return `${diffD}d ago`
    return d.format('DD MMM')
  }

  function fmtROI(value) {
    if (value === null || value === undefined) return '—'
    const n = Number(value)
    const color = n >= 300 ? 'text-green' : n >= 100 ? 'text-blue' : n >= 0 ? 'text-amber' : 'text-red'
    return { value: `${n.toFixed(1)}%`, color }
  }

  function todayISO() {
    return dayjs().format('YYYY-MM-DD')
  }

  function monthISO() {
    return dayjs().format('YYYY-MM')
  }

  return { fmtMoney, fmtNumber, fmtPct, fmtDate, fmtDateTime, fmtRelative, fmtROI, todayISO, monthISO }
}
