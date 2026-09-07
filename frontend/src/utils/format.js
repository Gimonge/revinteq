/**
 * Revinteq v3 — Global Formatting Utilities
 * Pure functions — no store dependency. Currency passed explicitly or defaults to 'KES'.
 */
import dayjs from 'dayjs'

const LOCALE = 'en-KE'

/** Smart format — commas always, abbreviates M/B only */
export function fmtK(value, currency = 'KES') {
  const c = currency || 'KES'
  const n = Number(value)
  if (isNaN(n) || (!value && value !== 0)) return `${c} 0`
  if (n >= 1_000_000_000) return `${c} ${(n/1_000_000_000).toFixed(1).replace(/\.0$/,'')}B`
  if (n >= 1_000_000)     return `${c} ${(n/1_000_000).toFixed(1).replace(/\.0$/,'')}M`
  return `${c} ${n.toLocaleString(LOCALE, {minimumFractionDigits:0, maximumFractionDigits:0})}`
}

/** Always full comma-separated — for tables, totals */
export function fmtFull(value, currency = 'KES') {
  const c = currency || 'KES'
  const n = Number(value)
  if (isNaN(n) || (!value && value !== 0)) return `${c} 0`
  return `${c} ${n.toLocaleString(LOCALE, {minimumFractionDigits:0, maximumFractionDigits:0})}`
}

/** Plain number with commas, no currency symbol */
export function fmtNum(value) {
  const n = Number(value)
  if (isNaN(n) || (!value && value !== 0)) return '0'
  if (n >= 1_000_000) return `${(n/1_000_000).toFixed(1).replace(/\.0$/,'')}M`
  return n.toLocaleString(LOCALE, {minimumFractionDigits:0, maximumFractionDigits:0})
}

export function fmtPct(value, decimals = 1) {
  const n = Number(value)
  return isNaN(n) ? '0%' : `${n.toFixed(decimals)}%`
}

export function fmtDate(value, fmt = 'D MMM YYYY') {
  return value ? dayjs(value).format(fmt) : '—'
}

/** Add commas to a numeric string for display in inputs */
export function commaify(value) {
  if (!value && value !== 0) return ''
  const str = String(value).replace(/[^0-9.]/g, '')
  const [int, dec] = str.split('.')
  const formatted = int.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return dec !== undefined ? `${formatted}.${dec}` : formatted
}

/** Strip commas to get raw number string */
export function stripCommas(value) {
  return String(value).replace(/,/g, '')
}
