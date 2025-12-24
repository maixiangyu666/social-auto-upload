<template>
  <span class="inline-flex items-center rounded-full px-2 py-1 text-xs" :class="colorClass">
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tone: { type: String, default: 'neutral' }, // neutral | success | warning | danger | info
})

const colorClass = computed(() => {
  switch (props.tone) {
    case 'success':
      return 'bg-emerald-50 text-emerald-700'
    case 'warning':
      return 'bg-amber-50 text-amber-700'
    case 'danger':
      return 'bg-rose-50 text-rose-700'
    case 'info':
      return 'bg-sky-50 text-sky-700'
    case 'neutral':
    default:
      return 'bg-slate-100 text-slate-700'
  }
})
</script>


