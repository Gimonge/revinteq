<template>
  <div
    class="bg-white rounded-lg border border-border shadow-card p-3 mb-2 cursor-pointer transition-all duration-150 hover:shadow-md hover:-translate-y-px"
    :class="borderClass"
    @click="$emit('open', deal)"
  >
    <!-- Customer & platform -->
    <div class="flex items-start justify-between gap-2 mb-1.5">
      <div class="font-black text-[12.5px] text-slate truncate">
        {{ deal.customer_name || 'Anonymous' }}
      </div>
      <PlatformBadge :platform="deal.platform" class="flex-shrink-0" />
    </div>

    <!-- Ad name -->
    <div v-if="deal.ad_name" class="text-[11px] text-slate-light font-semibold truncate mb-1">
      {{ deal.ad_name }}
    </div>

    <!-- Time ago -->
    <div class="text-[11px] text-slate-light font-semibold mb-2">
      {{ relativeTime }}
    </div>

    <!-- Estimated value -->
    <div v-if="deal.estimated_value" class="text-[12px] font-black text-slate mb-2">
      {{ fmtMoney(deal.estimated_value) }}
    </div>

    <!-- Synced sale from Kommo -->
    <div v-if="deal.has_sale" class="inline-flex items-center gap-1 text-[10px] font-black text-green bg-green-light rounded-full px-2 py-0.5 mb-2">
      <i class="ti ti-circle-check" aria-hidden="true"></i> Synced Sale
    </div>

    <!-- ══ M-PESA BILL REFERENCE ══════════════════════════ -->
    <div
      v-if="deal.mpesa_reference && isOpen"
      class="flex items-center gap-2 bg-green-light border border-green/20 rounded-lg px-3 py-2 mb-2"
    >
      <div class="flex-1 min-w-0">
        <div class="text-[9px] font-black text-green/70 uppercase tracking-wide mb-0.5">M-Pesa Ref</div>
        <div class="text-[14px] font-black text-green tracking-wider">{{ deal.mpesa_reference }}</div>
      </div>
      <button
        @click.stop="copyRef"
        class="flex-shrink-0 flex items-center gap-1.5 bg-green text-white text-[11px] font-black px-2.5 py-1.5 rounded-md hover:bg-green-dark transition-colors"
        :class="copied ? 'bg-green-dark' : ''"
      >
        <span><i :class="['ti', copied ? 'ti-check' : 'ti-clipboard-list']" aria-hidden="true"></i> {{ copied ? 'Copied' : 'Copy' }}</span>
      </button>
    </div>

    <!-- Send payment instructions button (for any channel) -->
    <div v-if="deal.mpesa_reference && isOpen" class="mb-2">
      <button
        @click.stop="$emit('sendInstructions', deal)"
        class="w-full text-[11px] font-bold text-slate-mid border border-border rounded-md py-1.5 hover:bg-surface transition-colors"
      >
        <i class="ti ti-upload" aria-hidden="true"></i> Send Payment Instructions
      </button>
    </div>

    <!-- Velocity badge -->
    <div class="flex items-center justify-between">
      <span
        class="inline-flex items-center text-[10px] font-black px-2 py-0.5 rounded-full"
        :class="velocityClass"
      >
        <i :class="['ti', velocityIcon]" :style="{color: velocityIconColor}" aria-hidden="true"></i> {{ velocityLabel }}
      </span>
      <span v-if="deal.days_in_current_stage > 0" class="text-[10px] text-slate-light font-semibold">
        {{ deal.days_in_current_stage }}d here
      </span>
    </div>

    <!-- Quick Won/Lost — only on open deals -->
    <div v-if="isOpen" class="flex gap-1.5 mt-2.5">
      <button
        @click.stop="$emit('quickWon', deal)"
        class="flex-1 text-[11px] font-black bg-green text-white rounded-md py-1.5 hover:bg-green-dark transition-colors shadow-green"
      >
        <i class="ti ti-circle-check" aria-hidden="true"></i> Won
      </button>
      <button
        @click.stop="$emit('quickLost', deal)"
        class="flex-1 text-[11px] font-black bg-red-light text-red-500 rounded-md py-1.5 hover:bg-red-500 hover:text-white transition-colors"
      >
        <i class="ti ti-x" aria-hidden="true"></i> Lost
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFormat } from '@/composables/useFormat'
import PlatformBadge from '@/components/shared/PlatformBadge.vue'
import dayjs from 'dayjs'

const props = defineProps({
  deal: { type: Object, required: true }
})

const emit = defineEmits(['open', 'quickWon', 'quickLost', 'sendInstructions'])

const { fmtMoney } = useFormat()
const copied = ref(false)

const OPEN_STAGES = ['new_click', 'contacted', 'interested', 'negotiating']

const isOpen = computed(() => OPEN_STAGES.includes(props.deal.stage))

const borderClass = computed(() => ({
  'border-l-[3px] border-l-blue':   props.deal.stage === 'new_click',
  'border-l-[3px] border-l-amber':  props.deal.stage === 'contacted',
  'border-l-[3px] border-l-purple': props.deal.stage === 'interested',
  'border-l-[3px] border-l-pink-600': props.deal.stage === 'negotiating',
  'border-l-[3px] border-l-green':  props.deal.stage === 'won',
  'border-l-[3px] border-l-red-400 opacity-60': props.deal.stage === 'lost',
}))

const velocityClass = computed(() => ({
  'bg-red-50 text-red-500':   props.deal.velocity === 'hot',
  'bg-amber-light text-amber': props.deal.velocity === 'warm',
  'bg-blue-light text-blue':   props.deal.velocity === 'cold',
}))

const velocityIcon = computed(() => ({
  hot: 'ti-flame', warm: 'ti-circle-filled', cold: 'ti-snowflake',
}[props.deal.velocity] || ''))
const velocityIconColor = computed(() => ({
  hot: '#dc2626', warm: '#d97706', cold: '#2563eb',
}[props.deal.velocity] || ''))
const velocityLabel = computed(() => ({
  hot: 'Hot', warm: 'Warm', cold: 'Cold',
}[props.deal.velocity] || '—'))

const relativeTime = computed(() => {
  const t = props.deal.new_click_at
  if (!t) return ''
  const h = dayjs().diff(dayjs(t), 'hour')
  if (h < 1)  return 'Just now'
  if (h < 24) return `${h}h ago`
  const d = dayjs().diff(dayjs(t), 'day')
  return `${d}d ago`
})

async function copyRef() {
  try {
    await navigator.clipboard.writeText(props.deal.mpesa_reference)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Fallback for older mobile browsers
    const el = document.createElement('textarea')
    el.value = props.deal.mpesa_reference
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}
</script>
