<template>
  <div class="overflow-x-auto">
    <table class="min-w-full text-left text-sm">
      <thead class="text-[11px] text-slate-500 uppercase tracking-[0.12em]">
        <tr>
          <th v-for="col in columns" :key="col.key" class="py-2 pr-4" :style="col.width ? { width: col.width } : undefined">
            {{ col.header }}
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100">
        <tr v-for="row in rows" :key="rowKey ? row[rowKey] : row.id" class="hover:bg-slate-50/80 transition-colors">
          <td v-for="col in columns" :key="col.key" class="py-2.5 pr-4">
            <slot :name="`cell:${col.key}`" :row="row">
              <span class="text-slate-700">{{ row[col.key] }}</span>
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  columns: { type: Array, default: () => [] }, // [{key, header, width?}]
  rows: { type: Array, default: () => [] },
  rowKey: { type: String, default: '' },
})
</script>


