<template>
  <div class="bg-white rounded-xl border border-border shadow-card p-5 relative overflow-hidden hover:-translate-y-0.5 hover:shadow-md transition-all duration-200">
    <div class="absolute top-0 left-0 right-0 h-[3px] rounded-t-xl" :class="accentClass"></div>
    <div class="text-[10px] font-black text-slate-light uppercase tracking-wide mb-2">{{ label }}</div>
    <div class="text-[28px] font-black text-slate tracking-tight leading-none">{{ value ?? '—' }}</div>
    <div v-if="sub" class="text-[12px] text-slate-mid font-semibold mt-1.5">{{ sub }}</div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ label: String, value: [String, Number], sub: String, accent: { type: String, default: 'green' } })
const accentClass = computed(() => ({
  'bg-green':   props.accent === 'green',
  'bg-blue':    props.accent === 'blue',
  'bg-amber':   props.accent === 'amber',
  'bg-purple':  props.accent === 'purple',
  'bg-gradient-to-r from-ig1 via-ig2 to-ig3': props.accent === 'instagram',
}))
</script>
