<template>
  <div class="space-y-6 pb-14">
    <!-- Hero -->
    <section class="relative overflow-hidden rounded-[24px] mesh-gradient p-7 shadow-2xl shadow-indigo-100/60 border border-white/40">
      <div class="relative z-10 max-w-2xl space-y-2">
        <h1 class="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl leading-tight">
          欢迎回来，<span class="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">Creator</span>
        </h1>
        <p class="text-sm font-medium text-slate-600 leading-relaxed">
          这是你的全能社交媒体自动化中心。管理账号、分发素材、监控任务，一切尽在掌握。
        </p>
        <div class="pt-1 flex flex-wrap gap-2.5">
          <button 
            class="rounded-2xl bg-slate-900 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-slate-900/20 transition-all hover:scale-[1.01] active:scale-95"
            @click="go('/publish-center')"
          >
            立即发布素材
          </button>
          <button 
            class="rounded-2xl bg-white/85 px-4 py-2.5 text-sm font-bold text-slate-900 shadow-sm backdrop-blur-md transition-all hover:bg-white active:scale-95"
            @click="go('/account-management')"
          >
            管理我的账号
          </button>
        </div>
      </div>
      <div class="absolute -right-14 -top-14 h-64 w-64 rounded-full bg-gradient-to-br from-indigo-200/30 to-purple-200/25 blur-3xl" />
    </section>

    <!-- KPIs -->
    <section>
      <div class="mb-3 flex items-end justify-between px-1">
        <div>
          <h2 class="text-lg font-bold tracking-tight text-slate-900">实时概览</h2>
          <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Data Analytics</p>
        </div>
        <button class="text-xs font-bold text-indigo-600 hover:text-indigo-700" @click="reloadAll">刷新</button>
      </div>
      
      <div class="grid grid-cols-1 gap-3.5 md:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="card in statCards"
          :key="card.key"
          class="group rounded-[22px] bg-white p-4.5 shadow-sm border border-slate-100 transition-all duration-200 hover:shadow-2xl hover:shadow-slate-200/70 hover:-translate-y-[2px]"
        >
          <div class="flex items-start justify-between">
            <div class="flex flex-col">
              <span class="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">{{ card.label }}</span>
              <span class="mt-1 text-2xl font-black text-slate-900 tracking-tighter leading-tight">{{ card.value }}</span>
            </div>
            <div :class="[card.iconBg, 'flex h-10 w-10 items-center justify-center rounded-[16px] text-lg shadow-inner group-hover:scale-110 transition-transform duration-300']" />
          </div>
          <div class="mt-3 flex flex-wrap gap-1">
            <span
              v-for="(chip, i) in card.meta"
              :key="i"
              class="inline-flex items-center rounded-full bg-slate-50 px-2 py-1 text-[10px] font-bold text-slate-500 border border-slate-100"
            >
              {{ chip }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Quick actions -->
    <section class="rounded-[22px] border border-slate-200 bg-white p-5 shadow-sm hover:shadow-xl transition-all">
      <div class="flex items-center justify-between">
        <div class="text-sm font-semibold text-slate-900">快捷操作</div>
        <button
          type="button"
          class="text-xs font-medium text-slate-600 hover:text-slate-900"
          @click="reloadAll"
        >
          刷新数据
        </button>
      </div>
      <div class="mt-3 grid grid-cols-1 gap-2.5 md:grid-cols-2 xl:grid-cols-4">
        <button
          v-for="a in quickActions"
          :key="a.path"
          type="button"
          class="group flex items-center justify-between rounded-[18px] border border-slate-200 bg-slate-50 px-3.5 py-3 text-left hover:bg-white shadow-sm transition-all hover:shadow-lg"
          @click="go(a.path)"
        >
          <div>
            <div class="text-sm font-semibold text-slate-900">{{ a.title }}</div>
            <div class="mt-0.5 text-xs text-slate-600">{{ a.desc }}</div>
          </div>
          <div class="text-sm text-slate-400 group-hover:text-slate-700">→</div>
        </button>
      </div>
    </section>

    <!-- Recent tasks -->
    <section class="rounded-[22px] border border-slate-200 bg-white shadow-sm hover:shadow-xl transition-all">
      <div class="flex items-center justify-between border-b border-slate-200 px-5 py-3">
        <div class="text-sm font-semibold text-slate-900">最近任务</div>
        <button
          type="button"
          class="text-xs font-medium text-slate-600 hover:text-slate-900"
          @click="go('/task-management')"
        >
          查看全部
        </button>
      </div>
      <div class="p-5">
        <div v-if="loading" class="text-sm text-slate-500">加载中...</div>
        <div v-else-if="recentTasks.length === 0" class="text-sm text-slate-500">暂无任务</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-[11px] text-slate-500 uppercase tracking-[0.12em]">
              <tr>
                <th class="py-2 pr-4">标题</th>
                <th class="py-2 pr-4">平台</th>
                <th class="py-2 pr-4">账号</th>
                <th class="py-2 pr-4">创建时间</th>
                <th class="py-2 pr-4">状态</th>
                <th class="py-2">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="t in recentTasks" :key="t.id" class="hover:bg-slate-50/80 transition-colors">
                <td class="py-2.5 pr-4">
                  <div class="max-w-[340px] truncate font-medium text-slate-900">{{ t.title }}</div>
                </td>
                <td class="py-2.5 pr-4">
                  <span class="inline-flex rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">{{ t.platform }}</span>
                </td>
                <td class="py-2.5 pr-4 text-slate-700">{{ t.account }}</td>
                <td class="py-2.5 pr-4 text-slate-600">{{ t.createTime }}</td>
                <td class="py-2.5 pr-4">
                  <span class="inline-flex rounded-full px-2 py-1 text-xs" :class="statusPill(t.statusCode)">
                    {{ t.status }}
                  </span>
                </td>
                <td class="py-2.5">
                  <button class="text-xs font-medium text-slate-700 hover:text-slate-900" @click="go(`/task-management/${t.id}`)">
                    查看
                  </button>
                  <button
                    v-if="t.statusCode === 0 || t.statusCode === 1"
                    class="ml-3 text-xs font-medium text-rose-700 hover:text-rose-900"
                    @click="cancel(t)"
                  >
                    取消
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { accountApi } from '@/api/account'
import { materialApi } from '@/api/material'
import { taskApi } from '@/api/task'
import { toast } from '@/utils/toast'

const router = useRouter()

const loading = ref(false)
const accountStats = reactive({ total: 0, normal: 0, abnormal: 0 })
const contentStats = reactive({ total: 0 })
const taskStats = reactive({ total: 0, completed: 0, inProgress: 0, failed: 0 })
const recentTasks = ref([])

const quickActions = [
  { path: '/account-management', title: '账号管理', desc: '添加/验证账号、管理 Cookie' },
  { path: '/material-management', title: '素材管理', desc: '上传/预览/管理素材' },
  { path: '/publish-center', title: '发布中心', desc: '选择账号与素材，一键创建任务' },
  { path: '/task-management', title: '任务管理', desc: '监控状态、失败重试' },
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

const statCards = computed(() => [
  {
    key: 'accounts',
    label: '账号总数',
    value: accountStats.total,
    meta: [`有效 ${accountStats.normal}`, `无效 ${accountStats.abnormal}`],
    iconBg: 'bg-indigo-100',
  },
  {
    key: 'materials',
    label: '素材总数',
    value: contentStats.total,
    meta: ['视频/图片/文本'],
    iconBg: 'bg-sky-100',
  },
  {
    key: 'tasks',
    label: '任务总数',
    value: taskStats.total,
    meta: [`成功 ${taskStats.completed}`, `进行中 ${taskStats.inProgress}`, `失败 ${taskStats.failed}`],
    iconBg: 'bg-emerald-100',
  },
  {
    key: 'rate',
    label: '成功率',
    value: taskStats.total ? `${Math.round((taskStats.completed / taskStats.total) * 100)}%` : '—',
    meta: ['基于当前任务'],
    iconBg: 'bg-amber-100',
  },
])

const go = (path) => router.push(path)

const loadAccounts = async () => {
  const res = await accountApi.getAccounts({ limit: 2000, offset: 0 })
  if (res?.code !== 200) return
  const rows = res.data?.items ?? []
  accountStats.total = res.data?.total ?? rows.length
  // 新接口返回的是对象数组
  accountStats.normal = rows.filter((r) => r.status === 1).length
  accountStats.abnormal = rows.filter((r) => r.status === 0).length
}

const loadMaterials = async () => {
  const res = await materialApi.getAllMaterials({ limit: 1, offset: 0 })
  if (res?.code !== 200) return
  const items = res.data?.items ?? []
  const total = res.data?.total ?? items.length
  contentStats.total = total
}

const loadTasks = async () => {
  const res = await taskApi.listTasks({ limit: 50, offset: 0 })
  if (res?.code !== 200) return
  const items = res.data?.items ?? []
  const total = res.data?.total ?? items.length
  taskStats.total = total
  taskStats.completed = items.filter((t) => t.status === 2).length
  taskStats.inProgress = items.filter((t) => t.status === 1).length
  taskStats.failed = items.filter((t) => t.status === 3).length
  recentTasks.value = items.slice(0, 10).map((t) => ({
    id: t.id,
    title: t.title,
    platform: platformName(t.platform_type),
    account: `账号 ${t.account_id}`,
    createTime: t.create_time,
    status: statusName(t.status),
    statusCode: t.status,
  }))
}

const reloadAll = async () => {
  loading.value = true
  try {
    await Promise.all([loadAccounts(), loadMaterials(), loadTasks()])
  } catch (e) {
    toast.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const cancel = async (t) => {
  if (!confirm(`确定取消任务「${t.title}」吗？`)) return
  const res = await taskApi.cancelTask(t.id)
  if (res?.code === 200) {
    toast.success('已取消')
    await loadTasks()
  } else {
    toast.error(res?.msg || '取消失败')
  }
}

let timer = null
onMounted(async () => {
  await reloadAll()
  timer = setInterval(reloadAll, 30000)
})
onUnmounted(() => timer && clearInterval(timer))
</script>


