<template>
  <div class="pointer-events-none fixed right-4 top-4 z-50 flex w-[360px] flex-col gap-2">
    <div
      v-for="t in items"
      :key="t.id"
      class="pointer-events-auto rounded-xl border bg-white/90 p-3 shadow-lg backdrop-blur"
      :class="toastClass(t.type)"
    >
      <div class="text-sm font-medium leading-5">
        {{ t.message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { onToast } from '@/utils/toast'

const items = ref([])

const toastClass = (type) => {
  if (type === 'success') return 'border-emerald-200 text-emerald-900'
  if (type === 'error') return 'border-rose-200 text-rose-900'
  return 'border-slate-200 text-slate-900'
}

let off = null

onMounted(() => {
  off = onToast((t) => {
    items.value = [t, ...items.value].slice(0, 5)
    setTimeout(() => {
      items.value = items.value.filter((x) => x.id !== t.id)
    }, 2500)
  })
})

onBeforeUnmount(() => {
  if (off) off()
})
</script>


