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
          />
        </div>
        <div class="text-xs text-slate-500">
          {{ filtered.length }} / {{ accounts.length }}
        </div>
      </div>
    </section>

    <section class="rounded-2xl border border-slate-200 bg-white">
      <div class="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
        账号列表
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
      </div>
    </section>

    <LoginModal v-model:open="loginOpen" :mode="loginMode" :account="loginAccount" @success="onLoginSuccess" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { accountApi } from '@/api/account'
import { toast } from '@/utils/toast'
import LoginModal from '@/components/account/LoginModal.vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'

const loading = ref(false)
const accounts = ref([])
const keyword = ref('')

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
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return accounts.value
  return accounts.value.filter((a) => {
    const s = `${a.id} ${platformName(a.type)} ${a.userName} ${a.filePath}`.toLowerCase()
    return s.includes(kw)
  })
})

const loadAccounts = async (validate) => {
  loading.value = true
  try {
    // 使用新接口获取账号列表
    const res = await accountApi.getAccounts()
    if (res?.code !== 200) {
      toast.error(res?.msg || '加载失败')
      return
    }
    
    // 新接口返回的是对象数组，直接使用
    accounts.value = res.data || []
    
    // 如果需要验证，批量验证所有账号
    if (validate && accounts.value.length > 0) {
      const accountIds = accounts.value.map(a => a.id)
      await accountApi.batchVerifyAccounts(accountIds)
      // 验证后重新加载列表以获取最新状态
      const res2 = await accountApi.getAccounts()
      if (res2?.code === 200) {
        accounts.value = res2.data || []
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
    await loadAccounts(false)
  } else {
    toast.error(res?.msg || '删除失败')
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


