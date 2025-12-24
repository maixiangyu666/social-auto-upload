<template>
  <div class="space-y-4">
    <header class="flex items-center justify-between">
      <div>
        <div class="text-lg font-semibold text-slate-900">数据统计</div>
        <div class="text-xs text-slate-600">基于任务列表的实时统计（后续可接平台统计表）</div>
      </div>
      <button class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50" @click="reload">
        刷新
      </button>
    </header>

    <section class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div v-for="c in cards" :key="c.key" class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="text-xs font-medium text-slate-500">{{ c.label }}</div>
        <div class="mt-1 text-2xl font-semibold text-slate-900">{{ c.value }}</div>
        <div class="mt-2 text-xs text-slate-600">{{ c.desc }}</div>
      </div>
    </section>

    <section class="rounded-2xl border border-slate-200 bg-white">
      <div class="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">平台统计</div>
      <div class="p-4">
        <div v-if="loading" class="text-sm text-slate-500">加载中...</div>
        <div v-else-if="platformRows.length === 0" class="text-sm text-slate-500">暂无数据</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-xs text-slate-500">
              <tr>
                <th class="py-2 pr-4">平台</th>
                <th class="py-2 pr-4">总任务</th>
                <th class="py-2 pr-4">成功</th>
                <th class="py-2 pr-4">失败</th>
                <th class="py-2">成功率</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="r in platformRows" :key="r.platformType" class="hover:bg-slate-50">
                <td class="py-3 pr-4 font-medium text-slate-900">{{ r.platform }}</td>
                <td class="py-3 pr-4 text-slate-700">{{ r.total }}</td>
                <td class="py-3 pr-4 text-emerald-700">{{ r.success }}</td>
                <td class="py-3 pr-4 text-rose-700">{{ r.failed }}</td>
                <td class="py-3 text-slate-700">{{ r.successRate }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { taskApi } from '@/api/task'
import { toast } from '@/utils/toast'

const loading = ref(false)
const tasks = ref([])

const platformName = (type) =>
  ({
    1: '小红书',
    2: '视频号',
    3: '抖音',
    4: '快手',
    5: 'Bilibili',
    6: '百家号',
    7: 'TikTok',
  })[type] || '未知'

const reload = async () => {
  loading.value = true
  try {
    const res = await taskApi.listTasks({ limit: 2000, offset: 0 })
    if (res?.code !== 200) {
      toast.error(res?.msg || '加载失败')
      tasks.value = []
      return
    }
    tasks.value = res.data ?? []
  } catch (e) {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

const cards = computed(() => {
  const total = tasks.value.length
  const success = tasks.value.filter((t) => t.status === 2).length
  const failed = tasks.value.filter((t) => t.status === 3).length
  const running = tasks.value.filter((t) => t.status === 1).length
  const rate = total ? Math.round((success / total) * 100) : 0
  return [
    { key: 'total', label: '总任务数', value: total, desc: '全部任务数量' },
    { key: 'running', label: '发布中', value: running, desc: '正在执行的任务' },
    { key: 'success', label: '成功', value: success, desc: '成功发布的任务' },
    { key: 'rate', label: '成功率', value: `${rate}%`, desc: '成功/总任务' },
  ]
})

const platformRows = computed(() => {
  const map = new Map()
  for (const t of tasks.value) {
    const key = t.platform_type
    if (!map.has(key)) map.set(key, { platformType: key, platform: platformName(key), total: 0, success: 0, failed: 0 })
    const row = map.get(key)
    row.total++
    if (t.status === 2) row.success++
    if (t.status === 3) row.failed++
  }
  return Array.from(map.values()).map((r) => ({
    ...r,
    successRate: r.total ? Math.round((r.success / r.total) * 100) : 0,
  }))
})

onMounted(reload)
</script>


