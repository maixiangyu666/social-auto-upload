<template>
  <div
    class="rounded-[20px] border border-white/15 bg-white/85 backdrop-blur-md shadow-md transition-all duration-200 hover:shadow-2xl hover:shadow-slate-300/60 hover:-translate-y-[2px]"
    :class="padded ? 'p-4' : ''"
  >
    <slot />
  </div>
</template>

<script setup>
defineProps({
  padded: { type: Boolean, default: true },
})
</script>


