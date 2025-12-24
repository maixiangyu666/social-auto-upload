<template>
  <component
    :is="as"
    :type="as === 'button' ? type : undefined"
    :disabled="disabled || loading"
    class="inline-flex items-center justify-center gap-2 rounded-2xl font-semibold tracking-tight transition-all duration-150 active:scale-95"
    :class="[variantClass, sizeClass, (disabled || loading) ? 'opacity-40 cursor-not-allowed active:scale-100' : 'hover:brightness-[0.99] active:brightness-[0.96]']"
    v-bind="$attrs"
  >
    <span v-if="loading" class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" />
    <slot />
  </component>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  as: { type: String, default: 'button' },
  type: { type: String, default: 'button' },
  variant: { type: String, default: 'primary' }, // primary | secondary | ghost | danger | gradient
  size: { type: String, default: 'md' }, // sm | md | lg
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

const variantClass = computed(() => {
  switch (props.variant) {
    case 'secondary':
      return 'border border-slate-200 bg-white text-slate-900 hover:bg-slate-100'
    case 'ghost':
      return 'bg-transparent text-slate-700 hover:bg-slate-100'
    case 'danger':
      return 'bg-rose-500 text-white shadow-md shadow-rose-200/60 hover:bg-rose-600'
    case 'gradient':
      return 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 text-white shadow-lg shadow-slate-900/20 hover:brightness-110'
    case 'primary':
    default:
      return 'bg-slate-900 text-white shadow-lg shadow-slate-900/15 hover:bg-slate-800'
  }
})

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'px-3 py-1.5 text-xs'
    case 'lg':
      return 'px-4 py-2.5 text-base'
    case 'md':
    default:
      return 'px-3.5 py-2 text-sm'
  }
})
</script>


