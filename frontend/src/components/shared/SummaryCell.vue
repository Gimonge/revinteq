<template>
  <div class="bg-white px-4 py-3">
    <div class="text-[9.5px] font-black text-slate-light uppercase tracking-wide mb-1.5">{{ label }}</div>
    <div class="text-[18px] font-black text-slate tracking-tight">{{ value ?? '—' }}</div>
  </div>
</template>
<script setup>
defineProps({ label: String, value: [String, Number] })
</script>
