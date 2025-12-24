<template>
  <div class="animate-pulse rounded-xl bg-slate-200/70" :style="{ height, width }" />
</template>

<script setup>
defineProps({
  height: { type: String, default: '12px' },
  width: { type: String, default: '100%' },
})
</script>


