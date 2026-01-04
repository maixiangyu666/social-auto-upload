<template>
  <div class="h-full">
    <div class="flex h-full text-slate-900">
      <!-- Sidebar -->
      <aside
        class="hidden h-full w-[17rem] flex-col border-r border-white/10 bg-slate-900/70 backdrop-blur-3xl md:flex shadow-xl shadow-slate-900/25"
      >
        <div class="flex h-14 items-center gap-3 px-5">
          <div class="h-9 w-9 rounded-[12px] bg-gradient-to-br from-slate-800 to-slate-600 shadow-md flex items-center justify-center">
            <div class="h-3 w-3 rounded-full border-2 border-white/40" />
          </div>
          <div class="flex flex-col leading-tight">
            <span class="text-sm font-bold tracking-tight text-white">Social Auto</span>
            <span class="text-[10px] uppercase tracking-[0.18em] text-slate-300 font-semibold">Management</span>
          </div>
        </div>

        <nav class="flex-1 overflow-y-auto px-3 py-3 scrollbar-hide">
          <div
            v-for="group in nav"
            :key="group.key"
            class="mb-4"
          >
            <div class="px-4 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400/90">
              {{ group.label }}
            </div>
            <div class="space-y-1">
              <template v-for="item in group.items" :key="item.path">
                <RouterLink
                  v-if="!item.children"
                  :to="item.path"
                  class="group relative flex items-center justify-between rounded-2xl px-4 py-2 text-sm transition-all duration-200"
                  :class="[isActive(item.path) ? 'bg-white/10 text-white shadow-md shadow-black/20 scale-105 border border-white/10' : 'text-slate-200 hover:bg-white/5 hover:text-white']"
                >
                  <span class="flex items-center gap-3 font-medium">
                    <span class="h-1 w-1 rounded-full" :class="isActive(item.path) ? 'bg-white' : 'bg-slate-400 group-hover:bg-slate-200'" />
                    {{ item.label }}
                  </span>
                </RouterLink>

                <div v-else class="rounded-lg">
                  <button
                    type="button"
                    class="group flex w-full items-center justify-between rounded-2xl px-4 py-2 text-sm text-slate-200 transition-all duration-200 hover:bg-white/5 hover:text-white"
                    :class="isActivePrefix(item.path) ? 'text-white bg-white/5' : ''"
                    @click="toggleOpen(item.path)"
                  >
                    <span class="flex items-center gap-3 font-medium">
                      <span class="h-1 w-1 rounded-full" :class="isActivePrefix(item.path) ? 'bg-white' : 'bg-slate-400 group-hover:bg-slate-200'" />
                      {{ item.label }}
                    </span>
                    <span class="text-[10px] opacity-60 transition-transform duration-300" :class="open[item.path] ? 'rotate-180' : ''">▼</span>
                  </button>
                  <div v-if="open[item.path]" class="mt-1 space-y-1 pl-2">
                    <RouterLink
                      v-for="c in item.children"
                      :key="c.path"
                      :to="c.path"
                      class="flex items-center justify-between rounded-xl px-3 py-2 text-sm transition-colors duration-200"
                      :class="isActive(c.path) ? 'bg-white/10 font-semibold text-white border border-white/10' : 'text-slate-300 hover:text-white hover:bg-white/5'"
                    >
                      <span>{{ c.label }}</span>
                    </RouterLink>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </nav>
      </aside>

      <!-- Main -->
      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-white/30 bg-white/55 px-5 backdrop-blur-xl shadow-sm">
          <div class="flex flex-col gap-0.5">
            <div class="text-[10px] font-bold uppercase tracking-wider text-slate-400/80">{{ pageContext }}</div>
            <div class="text-lg font-bold tracking-tight text-slate-900">{{ pageTitle }}</div>
          </div>
          <div class="flex items-center gap-3 text-xs text-slate-500">
            <div class="hidden sm:flex items-center gap-2 rounded-full bg-slate-900/5 px-3 py-1 border border-white/30 shadow-sm">
              <div class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span class="text-[10px] font-bold text-slate-600 uppercase tracking-tight">Online</span>
            </div>
          </div>
        </header>
        <main class="min-w-0 flex-1 overflow-y-auto p-4">
          <router-view />
        </main>
      </div>
    </div>
    <ToastHost />
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { useRoute } from 'vue-router'
import ToastHost from '@/components/ui/ToastHost.vue'

const route = useRoute()

const nav = [
  {
    key: 'prepare',
    label: '准备',
    items: [
      { path: '/', label: '工作台' },
      { path: '/account-management', label: '账号管理' },
      { path: '/material-management', label: '素材管理' },
      { path: '/proxy-management', label: '代理设置' },
    ],
  },
  {
    key: 'execute',
    label: '执行',
    items: [{ path: '/publish-center', label: '发布中心' }],
  },
  {
    key: 'monitor',
    label: '监控',
    items: [
      {
        path: '/task-management',
        label: '任务管理',
        children: [
          { path: '/task-management', label: '任务列表' },
          { path: '/task-management/history', label: '发布历史' },
        ],
      },
    ],
  },
  {
    key: 'analyze',
    label: '分析',
    items: [{ path: '/analytics', label: '数据统计' }],
  },
]

const open = reactive({
  '/task-management': true,
})

const isActive = (path) => route.path === path
const isActivePrefix = (path) => route.path === path || route.path.startsWith(path + '/')
const toggleOpen = (path) => (open[path] = !open[path])

const pageTitle = computed(() => {
  const path = route.path
  if (path === '/') return '工作台'
  if (path.startsWith('/account-management')) return '账号管理'
  if (path.startsWith('/material-management')) return '素材管理'
  if (path.startsWith('/publish-center')) return '发布中心'
  if (path.startsWith('/proxy-management')) return '代理设置'
  if (path.startsWith('/task-management')) return '任务管理'
  if (path.startsWith('/analytics')) return '数据统计'
  return '自媒体自动化运营系统'
})
</script>
