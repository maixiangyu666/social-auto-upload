<template>
  <label class="block space-y-1">
    <div v-if="label" class="text-xs font-medium text-slate-600">{{ label }}</div>
    <select
      class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-slate-400"
      v-bind="$attrs"
      :value="modelValue"
      @change="$emit('update:modelValue', cast($event.target.value))"
    >
      <slot />
    </select>
    <div v-if="hint" class="text-xs text-slate-500">{{ hint }}</div>
  </label>
</template>

<script setup>
const props = defineProps({
  modelValue: { type: [String, Number, null], default: null },
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
  number: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const cast = (v) => (props.number ? (v === '' ? null : Number(v)) : v)
</script>


