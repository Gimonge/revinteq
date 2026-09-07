<template>
  <span
    class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-black"
    :class="classes"
  >{{ label }}</span>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ platform: { type: String, default: '' } })
const MAP = {
  facebook:  { label: 'Facebook',  cls: 'bg-blue-light text-blue' },
  instagram: { label: 'Instagram', cls: 'bg-gradient-to-r from-ig1/20 to-ig3/20 text-ig2' },
  messenger: { label: 'Messenger', cls: 'bg-blue-light text-blue-dark' },
  whatsapp:  { label: 'WhatsApp',  cls: 'bg-green-light text-green' },
  organic:   { label: 'Organic',   cls: 'bg-slate-light/20 text-slate-mid' },
}
const entry   = computed(() => MAP[props.platform] || { label: props.platform, cls: 'bg-surface text-slate-mid' })
const label   = computed(() => entry.value.label)
const classes = computed(() => entry.value.cls)
</script>
