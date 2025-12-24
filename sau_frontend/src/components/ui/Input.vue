<template>
  <label class="block space-y-1">
    <div v-if="label" class="text-xs font-medium text-slate-600">{{ label }}</div>
    <input
      class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-slate-400"
      v-bind="$attrs"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <div v-if="hint" class="text-xs text-slate-500">{{ hint }}</div>
  </label>
</template>

<script setup>
defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
})

defineEmits(['update:modelValue'])
</script>


