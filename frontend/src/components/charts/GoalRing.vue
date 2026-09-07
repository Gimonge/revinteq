<template>
  <div class="flex flex-col items-center justify-center gap-3">
    <div class="relative" :style="{ width: size + 'px', height: size + 'px' }">
      <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`" class="-rotate-90">
        <!-- Background ring -->
        <circle
          :cx="size/2" :cy="size/2" :r="radius"
          fill="none" :stroke="trackColor"
          :stroke-width="strokeWidth"
        />
        <!-- Progress ring -->
        <circle
          :cx="size/2" :cy="size/2" :r="radius"
          fill="none" :stroke="ringColor"
          :stroke-width="strokeWidth"
          stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="dashOffset"
          style="transition: stroke-dashoffset .8s ease"
        />
      </svg>
      <!-- Center text -->
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <div class="text-[24px] font-black text-slate tracking-tight">{{ pct }}%</div>
        <div class="text-[10px] font-black text-slate-light uppercase tracking-wide">Progress</div>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <span
        class="inline-flex items-center px-3 py-1 rounded-full text-xs font-black"
        :class="statusClass"
      >{{ statusLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  progress: { type: Number, default: 0 },
  status:   { type: String, default: 'NO_GOAL' },
  size:     { type: Number, default: 140 },
  strokeWidth: { type: Number, default: 12 },
})

const radius      = computed(() => (props.size / 2) - props.strokeWidth)
const circumference = computed(() => 2 * Math.PI * radius.value)
const pct         = computed(() => Math.min(Math.round(props.progress || 0), 100))
const dashOffset  = computed(() => circumference.value * (1 - pct.value / 100))

const STATUS_COLORS = {
  AHEAD:    '#1F7A4C',
  ON_TRACK: '#2563EB',
  BEHIND:   '#D97706',
  NO_GOAL:  '#CBD5E1',
}
const ringColor  = computed(() => STATUS_COLORS[props.status] || '#CBD5E1')
const trackColor = computed(() => ringColor.value + '20')

const statusClass = computed(() => ({
  'bg-green-light text-green':  props.status === 'AHEAD',
  'bg-blue-light text-blue':    props.status === 'ON_TRACK',
  'bg-amber-light text-amber':  props.status === 'BEHIND',
  'bg-surface text-slate-light':props.status === 'NO_GOAL',
}))

const statusLabel = computed(() => ({
  AHEAD:    '🚀 Ahead',
  ON_TRACK: '✅ On Track',
  BEHIND:   '⚠️ Behind',
  NO_GOAL:  'No Goal Set',
}[props.status] || '—'))
</script>
