<template>
  <div class="bg-white rounded-xl border border-border shadow-card overflow-hidden">
    <div v-if="$slots.header || title" class="px-5 py-4 border-b border-border flex items-center justify-between">
      <div>
        <div v-if="title" class="text-[14.5px] font-black text-slate">{{ title }}</div>
        <div v-if="subtitle" class="text-[12px] text-slate-light font-semibold mt-0.5">{{ subtitle }}</div>
      </div>
      <slot name="header" />
    </div>
    <div :class="bodyClass"><slot /></div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ title: String, subtitle: String, noPad: Boolean })
const bodyClass = computed(() => props.noPad ? '' : 'p-5')
</script>
