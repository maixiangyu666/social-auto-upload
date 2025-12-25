<template>
  <div class="space-y-4">
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div class="text-lg font-semibold text-slate-900">发布中心</div>
        <div class="text-xs text-slate-600">选择平台/账号/素材，一键创建发布任务（后台异步执行）</div>
          </div>
      <div class="flex gap-2">
        <button
          type="button"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50"
          @click="reloadAll"
        >
          刷新数据
        </button>
        </div>
    </header>

    <!-- Step 1: basic -->
    <section class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">平台</div>
          <select v-model.number="form.type" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">
            <option v-for="p in platformOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </label>

        <label class="space-y-1 md:col-span-2">
          <div class="text-xs font-medium text-slate-600">标题</div>
          <input v-model.trim="form.title" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="例如：今天的剪辑作品" />
        </label>
            </div>
            
      <div class="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
        <label class="space-y-1 md:col-span-2">
          <div class="text-xs font-medium text-slate-600">标签（逗号分隔，不带 #）</div>
          <input v-model.trim="tagsText" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm" placeholder="生活,剪辑,日常" />
        </label>

        <label class="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
          <input v-model="form.enableTimer" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
          开启定时发布（简化版）
        </label>
            </div>

      <div v-if="form.enableTimer" class="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">每天发布数量</div>
          <input v-model.number="form.videosPerDay" type="number" min="1" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm" />
        </label>
        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">每天时间点（HH:MM）</div>
          <div class="flex flex-wrap gap-2">
            <input
              v-for="(t, i) in form.dailyTimes"
              :key="i"
              v-model="form.dailyTimes[i]"
              class="w-28 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            />
            <button
              type="button"
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50"
              @click="form.dailyTimes.push('10:00')"
            >
              + 时间
            </button>
                </div>
        </label>
        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">从第几天开始（0=明天）</div>
          <input v-model.number="form.startDays" type="number" min="0" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm" />
        </label>
              </div>
    </section>

    <!-- Step 2: accounts -->
    <section class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="flex items-center justify-between">
        <div>
          <div class="text-sm font-semibold text-slate-900">选择账号</div>
          <div class="text-xs text-slate-600">建议先在账号管理里校验有效性</div>
              </div>
        <div class="text-xs text-slate-500">已选 {{ selectedAccounts.size }}</div>
                        </div>

      <div class="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
        <label
          v-for="a in accounts"
          :key="a.id"
          class="flex cursor-pointer items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 hover:bg-white"
        >
          <div class="min-w-0">
            <div class="truncate text-sm font-medium text-slate-900">{{ a.userName }}</div>
            <div class="truncate text-xs text-slate-600">{{ platformName(a.type) }} · {{ a.filePath }}</div>
              </div>
          <input
            type="checkbox"
            class="h-4 w-4 rounded border-slate-300"
            :checked="selectedAccounts.has(a.filePath)"
            @change="toggleAccount(a.filePath)"
          />
        </label>
          </div>
    </section>

    <!-- Step 3: materials -->
    <section class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="flex items-center justify-between">
        <div>
          <div class="text-sm font-semibold text-slate-900">选择素材</div>
          <div class="text-xs text-slate-600">多选会为每个账号×素材创建任务</div>
          </div>
        <div class="text-xs text-slate-500">已选 {{ selectedFiles.size }}</div>
          </div>

      <div class="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
        <label
          v-for="m in materials"
          :key="m.id"
          class="flex cursor-pointer items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 hover:bg-white"
        >
          <div class="min-w-0">
            <div class="truncate text-sm font-medium text-slate-900">{{ m.filename }}</div>
            <div class="truncate text-xs text-slate-600">{{ m.file_path }}</div>
              </div>
          <input
            type="checkbox"
            class="h-4 w-4 rounded border-slate-300"
            :checked="selectedFiles.has(m.file_path)"
            @change="toggleFile(m.file_path)"
          />
        </label>
          </div>
    </section>

    <!-- Submit -->
    <section class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div class="text-xs text-slate-600">
          将创建 <span class="font-semibold text-slate-900">{{ taskCount }}</span> 个任务
                </div>
        <button
          type="button"
          class="rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          :disabled="submitting || !canSubmit"
          @click="submit"
        >
          {{ submitting ? '提交中...' : '创建任务并开始执行' }}
        </button>
                </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { accountApi } from '@/api/account'
import { materialApi } from '@/api/material'
import { toast } from '@/utils/toast'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'

const platformOptions = [
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

const accounts = ref([])
const materials = ref([])

const selectedAccounts = ref(new Set())
const selectedFiles = ref(new Set())

const form = reactive({
  type: 3,
  title: '',
  enableTimer: false,
  videosPerDay: 1,
  dailyTimes: ['10:00'],
  startDays: 0,
})

const tagsText = ref('')
const submitting = ref(false)

const tags = computed(() =>
  tagsText.value
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean)
)

const taskCount = computed(() => selectedAccounts.value.size * selectedFiles.value.size)
const canSubmit = computed(() => form.title && selectedAccounts.value.size > 0 && selectedFiles.value.size > 0)

const toggleAccount = (filePath) => {
  const s = new Set(selectedAccounts.value)
  if (s.has(filePath)) s.delete(filePath)
  else s.add(filePath)
  selectedAccounts.value = s
}

const toggleFile = (filePath) => {
  const s = new Set(selectedFiles.value)
  if (s.has(filePath)) s.delete(filePath)
  else s.add(filePath)
  selectedFiles.value = s
}

const loadAccounts = async () => {
  // 发布中心用于选择账号，这里先取较大页（避免一次性全量造成卡顿）
  const res = await accountApi.getAccounts({ limit: 2000, offset: 0 })
  if (res?.code !== 200) return []
  // 新接口返回的是对象数组，直接使用
  return (res.data?.items ?? []).map((r) => ({ 
    id: r.id, 
    type: r.type, 
    filePath: r.filePath, 
    userName: r.userName, 
    status: r.status 
  }))
}

const loadMaterials = async () => {
  // 发布中心用于选择素材，这里先取较大页（避免一次性全量造成卡顿）
  const res = await materialApi.getAllMaterials({ limit: 1000, offset: 0 })
  if (res?.code !== 200) return []
  return res.data?.items ?? []
}

const reloadAll = async () => {
  try {
    accounts.value = await loadAccounts()
    materials.value = await loadMaterials()
  } catch (e) {
    toast.error('加载数据失败')
  }
}

const submit = async () => {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    const payload = {
      fileList: Array.from(selectedFiles.value),
      accountList: Array.from(selectedAccounts.value),
      type: form.type,
      title: form.title,
      tags: tags.value,
      category: 0,
      enableTimer: form.enableTimer,
      videosPerDay: form.videosPerDay,
      dailyTimes: form.dailyTimes,
      startDays: form.startDays,
    }

    const res = await fetch(`${apiBaseUrl}/postVideo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then((r) => r.json())

    if (res?.code === 200) {
      toast.success(`已创建任务：${res?.data?.total_tasks ?? ''}`)
      // 清空选择（保留表单）
      selectedAccounts.value = new Set()
      selectedFiles.value = new Set()
    } else {
      toast.error(res?.msg || '创建任务失败')
    }
  } catch (e) {
    toast.error('创建任务失败')
  } finally {
    submitting.value = false
  }
}

onMounted(reloadAll)
</script>


