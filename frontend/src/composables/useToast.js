import { ref } from 'vue'

const message = ref('')
const type    = ref('green')
const show    = ref(false)
let timer

export function useToast() {
  function toast(msg, t = 'green') {
    message.value = msg
    type.value    = t
    show.value    = false
    clearTimeout(timer)
    setTimeout(() => { show.value = true }, 10)
    timer = setTimeout(() => { show.value = false }, 3200)
  }
  return { message, type, show, toast }
}
