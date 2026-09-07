<template>
  <RouterLink
    :to="to"
    class="flex items-center gap-2.5 px-3.5 py-2.5 mx-2 rounded-md text-[13px] font-bold transition-all duration-150"
    :class="isActive
      ? 'bg-green text-white shadow-green'
      : 'text-white/55 hover:bg-white/[.07] hover:text-white/90'"
  >
    <span class="text-sm w-[18px] text-center flex-shrink-0">{{ icon }}</span>
    <span>{{ label }}</span>
    <span v-if="badge" class="ml-auto text-[10px] font-black px-2 py-0.5 rounded-full"
      :class="badgeAlert ? 'bg-red-500 text-white' : 'bg-white/15 text-white/75'"
    >{{ badge }}</span>
  </RouterLink>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  to:         { type: String, required: true },
  icon:       { type: String, required: true },
  label:      { type: String, required: true },
  badge:      { type: [String, Number], default: null },
  badgeAlert: { type: Boolean, default: false },
})

const route   = useRoute()
const isActive = computed(() => {
  if (props.to === '/') return route.path === '/'
  return route.path.startsWith(props.to)
})
</script>
