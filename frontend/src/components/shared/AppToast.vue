<template>
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="visible" class="rv-toast" :class="type">
        <span><i :class="['ti', icon]" aria-hidden="true"></i></span> {{ message }}
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({
  message: String,
  type: { type: String, default: 'slate' }, // green | red | slate
  show: Boolean,
})
const visible = ref(false)
const icon = { green: 'ti-circle-check', red: 'ti-circle-x', slate: 'ti-info-circle' }[props.type] || 'ti-info-circle'
let timer
watch(() => props.show, (v) => {
  if (v) {
    visible.value = true
    clearTimeout(timer)
    timer = setTimeout(() => { visible.value = false }, 3200)
  }
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all .3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(20px); }
</style>
