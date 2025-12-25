<template>
  <div class="space-y-4">
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div class="text-lg font-semibold text-slate-900">账号管理</div>
        <div class="text-xs text-slate-600">添加账号、校验 Cookie，有效账号才能用于发布</div>
      </div>
      <div class="flex gap-2">
        <button
          type="button"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50"
          @click="loadAccounts(false)"
        >
          快速刷新
        </button>
        <button
          type="button"
          class="rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
          @click="openAddLogin()"
        >
          添加账号
        </button>
        <button
          type="button"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50"
          @click="loadAccounts(true)"
        >
          校验账号（慢）
        </button>
      </div>
    </header>

    <section class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div class="flex-1">
          <input
            v-model.trim="keyword"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            placeholder="搜索：账号名 / 平台 / 文件"
            @keyup.enter="page = 1; loadAccounts(false)"
          />
        </div>
        <div class="text-xs text-slate-500">共 {{ total }} 条</div>
      </div>
    </section>

    <section class="rounded-2xl border border-slate-200 bg-white">
      <div class="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
        账号列表（{{ total }}）
      </div>
      <div class="p-4">
        <div v-if="loading" class="text-sm text-slate-500">加载中...</div>
        <div v-else-if="filtered.length === 0" class="text-sm text-slate-500">暂无账号</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-xs text-slate-500">
              <tr>
                <th class="py-2 pr-4">ID</th>
                <th class="py-2 pr-4">平台</th>
                <th class="py-2 pr-4">账号名</th>
                <th class="py-2 pr-4">Cookie 文件</th>
                <th class="py-2 pr-4">状态</th>
                <th class="py-2">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="a in filtered" :key="a.id" class="hover:bg-slate-50">
                <td class="py-3 pr-4 text-slate-700">{{ a.id }}</td>
                <td class="py-3 pr-4">
                  <span class="inline-flex rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">
                    {{ platformName(a.type) }}
                  </span>
                </td>
                <td class="py-3 pr-4 font-medium text-slate-900">{{ a.userName }}</td>
                <td class="py-3 pr-4 text-slate-600">{{ a.filePath }}</td>
                <td class="py-3 pr-4">
                  <span class="inline-flex rounded-full px-2 py-1 text-xs" :class="statusPill(a.status)">
                    {{ a.status === 1 ? '有效' : '无效' }}
                  </span>
                </td>
                <td class="py-3">
                  <button
                    type="button"
                    class="text-xs font-medium text-slate-700 hover:text-slate-900"
                    @click="downloadCookie(a.filePath)"
                  >
                    下载 Cookie
                  </button>
                  <button
                    type="button"
                    class="ml-3 text-xs font-medium text-slate-700 hover:text-slate-900"
                    @click="openRefreshLogin(a)"
                  >
                    刷新 Cookie
                  </button>
                  <button
                    type="button"
                    class="ml-3 text-xs font-medium text-indigo-700 hover:text-indigo-900"
                    @click="refreshCookieBackground(a)"
                  >
                    立即后台刷新
                  </button>
                  <button
                    type="button"
                    class="ml-3 text-xs font-medium text-slate-700 hover:text-slate-900"
                    @click="openSettings(a)"
                  >
                    刷新设置
                  </button>
                  <button
                    type="button"
                    class="ml-3 text-xs font-medium text-slate-700 hover:text-slate-900"
                    @click="openLogs(a)"
                  >
                    刷新日志
                  </button>
                  <button
                    type="button"
                    class="ml-3 text-xs font-medium text-rose-700 hover:text-rose-900"
                    @click="deleteAccount(a.id)"
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
            <select v-model.number="pageSize" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm" @change="page = 1; loadAccounts(false)">
              <option :value="10">10 / 页</option>
              <option :value="20">20 / 页</option>
              <option :value="50">50 / 页</option>
              <option :value="100">100 / 页</option>
            </select>
            <button
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="page <= 1"
              @click="page = Math.max(1, page - 1); loadAccounts(false)"
            >
              上一页
            </button>
            <button
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="page >= Math.max(1, Math.ceil(total / pageSize))"
              @click="page = page + 1; loadAccounts(false)"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </section>

    <LoginModal v-model:open="loginOpen" :mode="loginMode" :account="loginAccount" @success="onLoginSuccess" />

    <!-- Refresh logs -->
    <Modal :open="logsOpen" title="Cookie 刷新日志" @close="logsOpen = false">
      <div class="space-y-3">
        <div class="text-xs text-slate-600">账号：{{ logsAccount?.userName }}（ID: {{ logsAccount?.id }}）</div>
        <div v-if="logsLoading" class="text-sm text-slate-500">加载中...</div>
        <div v-else-if="logs.length === 0" class="text-sm text-slate-500">暂无日志</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-xs text-slate-500">
              <tr>
                <th class="py-2 pr-4">时间</th>
                <th class="py-2 pr-4">结果</th>
                <th class="py-2 pr-4">方式</th>
                <th class="py-2 pr-4">耗时(ms)</th>
                <th class="py-2">错误</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="r in logs" :key="r.id" class="hover:bg-slate-50">
                <td class="py-3 pr-4 text-slate-700">{{ r.verify_time }}</td>
                <td class="py-3 pr-4">
                  <span
                    class="inline-flex rounded-full px-2 py-1 text-xs"
                    :class="r.verify_result === 1 ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'"
                  >
                    {{ r.verify_result === 1 ? '成功' : '失败' }}
                  </span>
                </td>
                <td class="py-3 pr-4 text-slate-600">{{ r.verify_method }}</td>
                <td class="py-3 pr-4 text-slate-600">{{ r.duration_ms ?? '-' }}</td>
                <td class="py-3 text-slate-600">
                  <span class="line-clamp-2 max-w-[520px] whitespace-pre-wrap">{{ r.error_message || '-' }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div class="text-xs text-slate-600">第 {{ logsPage }} / {{ Math.max(1, Math.ceil(logsTotal / logsPageSize)) }} 页</div>
          <div class="flex items-center gap-2">
            <select v-model.number="logsPageSize" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm" @change="logsPage = 1; loadLogs()">
              <option :value="10">10 / 页</option>
              <option :value="20">20 / 页</option>
              <option :value="50">50 / 页</option>
              <option :value="100">100 / 页</option>
            </select>
            <button
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="logsPage <= 1"
              @click="logsPage = Math.max(1, logsPage - 1); loadLogs()"
            >
              上一页
            </button>
            <button
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="logsPage >= Math.max(1, Math.ceil(logsTotal / logsPageSize))"
              @click="logsPage = logsPage + 1; loadLogs()"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </Modal>

    <!-- Refresh settings -->
    <Modal :open="settingsOpen" title="自动刷新设置" @close="settingsOpen = false">
      <div class="space-y-4">
        <div class="text-xs text-slate-600">账号：{{ settingsAccount?.userName }}（ID: {{ settingsAccount?.id }}）</div>

        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" v-model="settingsForm.auto_refresh_enabled" />
          启用自动刷新
        </label>

        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">刷新间隔（天）</div>
          <input
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            type="number"
            min="1"
            v-model.number="settingsForm.refresh_interval_days"
            :disabled="!settingsForm.auto_refresh_enabled"
          />
          <div class="text-xs text-slate-500">当前 next_refresh_time：{{ settingsAccount?.next_refresh_time || '-' }}</div>
        </label>

        <div class="flex gap-2">
          <button class="rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800" @click="saveSettings">
            保存
          </button>
          <button class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50" @click="settingsOpen = false">
            取消
          </button>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { accountApi } from '@/api/account'
import { toast } from '@/utils/toast'
import LoginModal from '@/components/account/LoginModal.vue'
import Modal from '@/components/ui/Modal.vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'

const loading = ref(false)
const accounts = ref([])
const keyword = ref('')
const total = ref(0)
const pageSize = ref(20)
const page = ref(1)

// ---- Refresh Logs Modal ----
const logsOpen = ref(false)
const logsAccount = ref(null)
const logsLoading = ref(false)
const logs = ref([])
const logsTotal = ref(0)
const logsPageSize = ref(20)
const logsPage = ref(1)

const openLogs = async (a) => {
  logsAccount.value = a
  logsPage.value = 1
  logsOpen.value = true
  await loadLogs()
}

const loadLogs = async () => {
  if (!logsAccount.value) return
  logsLoading.value = true
  try {
    const res = await accountApi.getCookieRefreshLogs(logsAccount.value.id, {
      limit: logsPageSize.value,
      offset: (logsPage.value - 1) * logsPageSize.value,
    })
    if (res?.code !== 200) {
      toast.error(res?.msg || '加载日志失败')
      logs.value = []
      logsTotal.value = 0
      return
    }
    logs.value = res.data?.items ?? []
    logsTotal.value = res.data?.total ?? logs.value.length
  } catch (e) {
    toast.error('加载日志失败')
  } finally {
    logsLoading.value = false
  }
}

// ---- Refresh Settings Modal ----
const settingsOpen = ref(false)
const settingsAccount = ref(null)
const settingsForm = ref({ auto_refresh_enabled: 1, refresh_interval_days: 7 })

const openSettings = (a) => {
  settingsAccount.value = a
  settingsForm.value = {
    auto_refresh_enabled: a.auto_refresh_enabled ?? 1,
    refresh_interval_days: a.refresh_interval_days ?? 7,
  }
  settingsOpen.value = true
}

const saveSettings = async () => {
  if (!settingsAccount.value) return
  const days = Number(settingsForm.value.refresh_interval_days)
  if (settingsForm.value.auto_refresh_enabled && (!days || days <= 0)) {
    toast.error('刷新间隔天数必须 > 0')
    return
  }
  const res = await accountApi.updateAccount(settingsAccount.value.id, {
    auto_refresh_enabled: settingsForm.value.auto_refresh_enabled ? 1 : 0,
    refresh_interval_days: days,
  })
  if (res?.code === 200) {
    toast.success('已保存')
    settingsOpen.value = false
    await loadAccounts(false)
  } else {
    toast.error(res?.msg || '保存失败')
  }
}

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

const statusPill = (s) => (s === 1 ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700')

const filtered = computed(() => {
  return accounts.value
})

const loadAccounts = async (validate) => {
  loading.value = true
  try {
    // 使用新接口获取账号列表
    const res = await accountApi.getAccounts({
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
      keyword: keyword.value.trim() || undefined,
    })
    if (res?.code !== 200) {
      toast.error(res?.msg || '加载失败')
      return
    }
    
    const data = res.data || {}
    accounts.value = data.items || []
    total.value = data.total ?? accounts.value.length
    
    // 如果需要验证，批量验证所有账号
    if (validate) {
      // 校验通常希望覆盖全部账号（而不是仅当前页）
      const allRes = await accountApi.getAccounts({
        limit: Math.max(2000, total.value || 2000),
        offset: 0,
        keyword: keyword.value.trim() || undefined,
      })
      const allItems = allRes?.data?.items || []
      const accountIds = allItems.map((a) => a.id)
      if (accountIds.length === 0) return
      await accountApi.batchVerifyAccounts(accountIds)
      // 验证后重新加载列表以获取最新状态
      const res2 = await accountApi.getAccounts({
        limit: pageSize.value,
        offset: (page.value - 1) * pageSize.value,
        keyword: keyword.value.trim() || undefined,
      })
      if (res2?.code === 200) {
        accounts.value = res2.data?.items || []
        total.value = res2.data?.total ?? accounts.value.length
      }
    }
  } catch (e) {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

const deleteAccount = async (id) => {
  if (!confirm('确定删除该账号吗？')) return
  const res = await accountApi.deleteAccount(id)
  if (res?.code === 200) {
    toast.success('已删除')
    const maxPage = Math.max(1, Math.ceil((total.value - 1) / pageSize.value))
    if (page.value > maxPage) page.value = maxPage
    await loadAccounts(false)
  } else {
    toast.error(res?.msg || '删除失败')
  }
}

const refreshCookieBackground = async (a) => {
  if (!confirm(`确定立即后台刷新「${a.userName}」的 Cookie 吗？`)) return
  const res = await accountApi.refreshCookie(a.id, { mode: 'background' })
  if (res?.code === 200) {
    toast.success(res?.msg || '已触发刷新')
    await loadAccounts(false)
  } else {
    toast.error(res?.msg || '刷新失败')
  }
}

const downloadCookie = (filePath) => {
  const url = `${apiBaseUrl}/downloadCookie?filePath=${encodeURIComponent(filePath)}`
  window.open(url, '_blank')
}

// ---- Login Modal ----
const loginOpen = ref(false)
const loginMode = ref('add') // add | refresh
const loginAccount = ref(null)

const openAddLogin = () => {
  loginMode.value = 'add'
  loginAccount.value = null
  loginOpen.value = true
}

const openRefreshLogin = (a) => {
  loginMode.value = 'refresh'
  loginAccount.value = { id: a.id, type: a.type, userName: a.userName }
  loginOpen.value = true
}

const onLoginSuccess = async () => {
  await loadAccounts(true)
}

loadAccounts(false)
</script>


