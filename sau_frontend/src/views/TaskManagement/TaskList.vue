<template>
  <div class="space-y-4">
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div class="text-lg font-semibold text-slate-900">任务列表</div>
        <div class="text-xs text-slate-600">监控任务状态，失败可重试，进行中可取消</div>
      </div>
      <div class="flex gap-2">
        <button
          type="button"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50"
          @click="reload"
        >
          刷新
        </button>
      </div>
    </header>

    <!-- Filters -->
    <section class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-4">
        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">平台</div>
          <select v-model="filters.platform_type" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">
            <option :value="null">全部</option>
            <option v-for="p in platforms" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </label>

        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">状态</div>
          <select v-model="filters.status" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">
            <option :value="null">全部</option>
            <option v-for="s in statuses" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </label>

        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">账号ID</div>
          <input
            v-model.trim="filters.account_id"
            placeholder="例如 1"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
          />
        </label>

        <div class="flex items-end gap-2">
          <button
            type="button"
            class="flex-1 rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
            @click="apply"
          >
            筛选
          </button>
          <button
            type="button"
            class="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50"
            @click="reset"
          >
            重置
          </button>
        </div>
      </div>
    </section>

    <!-- Table -->
    <section class="rounded-2xl border border-slate-200 bg-white">
      <div class="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
        任务（{{ total }}）
      </div>
      <div class="p-4">
        <div v-if="loading" class="text-sm text-slate-500">加载中...</div>
        <div v-else-if="tasks.length === 0" class="text-sm text-slate-500">暂无数据</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-xs text-slate-500">
              <tr>
                <th class="py-2 pr-4">ID</th>
                <th class="py-2 pr-4">标题</th>
                <th class="py-2 pr-4">平台</th>
                <th class="py-2 pr-4">账号</th>
                <th class="py-2 pr-4">状态</th>
                <th class="py-2 pr-4">重试</th>
                <th class="py-2 pr-4">创建时间</th>
                <th class="py-2">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="t in tasks" :key="t.id" class="hover:bg-slate-50">
                <td class="py-3 pr-4 text-slate-700">{{ t.id }}</td>
                <td class="py-3 pr-4">
                  <div class="max-w-[320px] truncate font-medium text-slate-900">{{ t.title }}</div>
                </td>
                <td class="py-3 pr-4">
                  <span class="inline-flex rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">
                    {{ platformName(t.platform_type) }}
                  </span>
                </td>
                <td class="py-3 pr-4 text-slate-700">{{ t.account_id }}</td>
                <td class="py-3 pr-4">
                  <span class="inline-flex rounded-full px-2 py-1 text-xs" :class="statusPill(t.status)">
                    {{ statusName(t.status) }}
                  </span>
                </td>
                <td class="py-3 pr-4 text-slate-600">{{ t.retry_count ?? 0 }}</td>
                <td class="py-3 pr-4 text-slate-600">{{ t.create_time }}</td>
                <td class="py-3">
                  <button class="text-xs font-medium text-slate-700 hover:text-slate-900" @click="goDetail(t.id)">
                    查看
                  </button>
                  <button
                    v-if="t.status === 0 || t.status === 1"
                    class="ml-3 text-xs font-medium text-rose-700 hover:text-rose-900"
                    @click="cancelTask(t)"
                  >
                    取消
                  </button>
                  <button
                    v-if="t.status === 3"
                    class="ml-3 text-xs font-medium text-indigo-700 hover:text-indigo-900"
                    @click="retryTask(t)"
                  >
                    重试
                  </button>
                  <button
                    class="ml-3 text-xs font-medium text-rose-700 hover:text-rose-900"
                    @click="deleteTask(t)"
                  >
                    删除
                  </button>
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
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { taskApi } from '@/api/task'
import { toast } from '@/utils/toast'

const router = useRouter()

const platforms = [
  { value: 1, label: '小红书' },
  { value: 2, label: '视频号' },
  { value: 3, label: '抖音' },
  { value: 4, label: '快手' },
]

const statuses = [
  { value: 0, label: '待发布' },
  { value: 1, label: '发布中' },
  { value: 2, label: '成功' },
  { value: 3, label: '失败' },
  { value: 4, label: '已取消' },
]

const filters = reactive({
  platform_type: null,
  status: null,
  account_id: '',
})

const loading = ref(false)
const tasks = ref([])
const total = ref(0)
const pageSize = ref(20)
const page = ref(1)

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

const statusName = (s) =>
  ({
    0: '待发布',
    1: '发布中',
    2: '成功',
    3: '失败',
    4: '已取消',
  })[s] || '未知'

const statusPill = (s) => {
  if (s === 2) return 'bg-emerald-50 text-emerald-700'
  if (s === 1) return 'bg-amber-50 text-amber-700'
  if (s === 0) return 'bg-slate-100 text-slate-700'
  if (s === 3) return 'bg-rose-50 text-rose-700'
  return 'bg-slate-50 text-slate-500'
}

const buildParams = () => {
  const params = {
    limit: pageSize.value,
    offset: (page.value - 1) * pageSize.value,
  }
  if (filters.platform_type !== null) params.platform_type = filters.platform_type
  if (filters.status !== null) params.status = filters.status
  if (filters.account_id) params.account_id = Number(filters.account_id)
  return params
}

const reload = async () => {
  loading.value = true
  try {
    const res = await taskApi.listTasks(buildParams())
    if (res?.code !== 200) {
      toast.error(res?.msg || '加载失败')
      tasks.value = []
      total.value = 0
      return
    }
    const data = res.data || {}
    tasks.value = data.items ?? []
    total.value = data.total ?? tasks.value.length
  } catch (e) {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

const apply = async () => reload()
const reset = async () => {
  filters.platform_type = null
  filters.status = null
  filters.account_id = ''
  page.value = 1
  await reload()
}

const goDetail = (id) => router.push(`/task-management/${id}`)

const cancelTask = async (t) => {
  if (!confirm(`确定取消任务「${t.title}」吗？`)) return
  const res = await taskApi.cancelTask(t.id)
  if (res?.code === 200) {
    toast.success('已取消')
    await reload()
  } else {
    toast.error(res?.msg || '取消失败')
  }
}

const retryTask = async (t) => {
  if (!confirm(`确定重试任务「${t.title}」吗？`)) return
  const res = await taskApi.retryTask(t.id)
  if (res?.code === 200) {
    toast.success('已重新执行')
    await reload()
  } else {
    toast.error(res?.msg || '重试失败')
  }
}

const deleteTask = async (t) => {
  if (!confirm(`确定删除任务「${t.title}」吗？`)) return
  const res = await taskApi.deleteTask(t.id)
  if (res?.code === 200) {
    toast.success('已删除')
    // 如果删除导致当前页空了，自动回退一页
    const maxPage = Math.max(1, Math.ceil((total.value - 1) / pageSize.value))
    if (page.value > maxPage) page.value = maxPage
    await reload()
  } else {
    toast.error(res?.msg || '删除失败')
  }
}

let timer = null
onMounted(async () => {
  await reload()
  timer = setInterval(reload, 15000)
})
onUnmounted(() => timer && clearInterval(timer))
</script>


