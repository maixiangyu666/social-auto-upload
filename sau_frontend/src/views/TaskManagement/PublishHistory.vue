<template>
  <div class="space-y-4">
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div class="text-lg font-semibold text-slate-900">发布历史</div>
        <div class="text-xs text-slate-600">当前基于任务表筛选（成功/失败）作为历史视图</div>
      </div>
      <button
        type="button"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50"
        @click="reload"
      >
        刷新
      </button>
    </header>

    <section class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">平台</div>
          <select v-model="filters.platform_type" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">
            <option :value="null">全部</option>
            <option v-for="p in platforms" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </label>

        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">结果</div>
          <select v-model="filters.status" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">
            <option :value="null">全部</option>
            <option :value="2">成功</option>
            <option :value="3">失败</option>
          </select>
        </label>

        <div class="flex items-end gap-2">
          <button class="flex-1 rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800" @click="reload">
            应用
          </button>
          <button class="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50" @click="reset">
            重置
          </button>
        </div>
      </div>
    </section>

    <section class="rounded-2xl border border-slate-200 bg-white">
      <div class="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
        历史（{{ total }}）
      </div>
      <div class="p-4">
        <div v-if="loading" class="text-sm text-slate-500">加载中...</div>
        <div v-else-if="items.length === 0" class="text-sm text-slate-500">暂无数据</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-xs text-slate-500">
              <tr>
                <th class="py-2 pr-4">ID</th>
                <th class="py-2 pr-4">标题</th>
                <th class="py-2 pr-4">平台</th>
                <th class="py-2 pr-4">账号</th>
                <th class="py-2 pr-4">结果</th>
                <th class="py-2 pr-4">发布时间</th>
                <th class="py-2">错误</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="t in items" :key="t.id" class="hover:bg-slate-50">
                <td class="py-3 pr-4 text-slate-700">{{ t.id }}</td>
                <td class="py-3 pr-4">
                  <div class="max-w-[320px] truncate font-medium text-slate-900">{{ t.title }}</div>
                </td>
                <td class="py-3 pr-4 text-slate-700">{{ platformName(t.platform_type) }}</td>
                <td class="py-3 pr-4 text-slate-700">{{ t.account_id }}</td>
                <td class="py-3 pr-4">
                  <span class="inline-flex rounded-full px-2 py-1 text-xs" :class="t.status === 2 ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'">
                    {{ t.status === 2 ? '成功' : '失败' }}
                  </span>
                </td>
                <td class="py-3 pr-4 text-slate-600">{{ t.publish_time || '-' }}</td>
                <td class="py-3 text-slate-600">
                  <span class="line-clamp-2 max-w-[340px] whitespace-pre-wrap">{{ t.error_message || '-' }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div class="text-xs text-slate-600">
            第 {{ page }} / {{ Math.max(1, Math.ceil(total / pageSize)) }} 页
          </div>
          <div class="flex items-center gap-2">
            <select v-model.number="pageSize" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm" @change="page = 1; reload()">
              <option :value="10">10 / 页</option>
              <option :value="20">20 / 页</option>
              <option :value="50">50 / 页</option>
              <option :value="100">100 / 页</option>
            </select>
            <button
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="page <= 1"
              @click="page = Math.max(1, page - 1); reload()"
            >
              上一页
            </button>
            <button
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="page >= Math.max(1, Math.ceil(total / pageSize))"
              @click="page = page + 1; reload()"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { taskApi } from '@/api/task'
import { toast } from '@/utils/toast'

const platforms = [
  { value: 1, label: '小红书' },
  { value: 2, label: '视频号' },
  { value: 3, label: '抖音' },
  { value: 4, label: '快手' },
]

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

const filters = reactive({
  platform_type: null,
  status: null,
})

const loading = ref(false)
const items = ref([])
const total = ref(0)
const pageSize = ref(20)
const page = ref(1)

const reload = async () => {
  loading.value = true
  try {
    const params = { limit: pageSize.value, offset: (page.value - 1) * pageSize.value }
    if (filters.platform_type !== null) params.platform_type = filters.platform_type
    if (filters.status !== null) {
      params.status = filters.status
    } else {
      // 不选时仅拉成功/失败作为“历史视图”
      params.status_in = '2,3'
    }
    const res = await taskApi.listTasks(params)
    if (res?.code !== 200) {
      toast.error(res?.msg || '加载失败')
      items.value = []
      total.value = 0
      return
    }
    items.value = res.data?.items ?? []
    total.value = res.data?.total ?? items.value.length
  } catch (e) {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

const reset = async () => {
  filters.platform_type = null
  filters.status = null
  page.value = 1
  await reload()
}

onMounted(reload)
</script>


