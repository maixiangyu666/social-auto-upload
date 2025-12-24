<template>
  <div v-if="open" class="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4" @keydown.esc="$emit('close')">
    <div class="w-full max-w-2xl rounded-2xl bg-white shadow-xl">
      <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div class="text-sm font-semibold text-slate-900">{{ title }}</div>
        <button class="text-sm text-slate-500 hover:text-slate-900" @click="$emit('close')">✕</button>
      </div>
      <div class="p-5">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
})

defineEmits(['close'])
</script>


