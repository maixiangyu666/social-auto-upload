<template>
  <div v-if="open" class="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
    <div class="w-full max-w-2xl overflow-hidden rounded-[22px] bg-white/90 shadow-2xl shadow-slate-900/10 backdrop-blur-xl">
      <div class="flex items-center justify-between border-b border-slate-200/70 px-6 py-4">
        <div class="space-y-0.5">
          <div class="text-sm font-semibold text-slate-900">{{ title }}</div>
          <div class="text-xs text-slate-600">{{ subtitle }}</div>
        </div>
        <button class="rounded-lg px-2 py-1 text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-900" @click="close">
          ✕
        </button>
      </div>

      <div class="grid grid-cols-1 gap-5 p-6 md:grid-cols-2">
        <!-- Left: form -->
        <div class="space-y-4">
          <div class="grid grid-cols-1 gap-3">
            <label class="space-y-1">
              <div class="text-xs font-medium text-slate-600">平台</div>
              <select
                v-model.number="form.platformType"
                class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                :disabled="mode === 'refresh'"
              >
                <option v-for="p in platformOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
              </select>
            </label>

            <label class="space-y-1">
              <div class="text-xs font-medium text-slate-600">
                账号名称（自定义）
                <span v-if="mode === 'refresh'" class="text-slate-400">（刷新模式不可改）</span>
              </div>
              <input
                v-model.trim="form.accountName"
                class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                placeholder="例如：douyin-1"
                :disabled="mode === 'refresh'"
              />
            </label>
          </div>

          <!-- Bilibili upload -->
          <div v-if="form.platformType === 5" class="rounded-2xl border border-slate-200 bg-white p-4">
            <div class="text-xs font-medium text-slate-700">Cookie 文件上传（Bilibili）</div>
            <div class="mt-2 text-xs text-slate-500">请选择 JSON 文件。新增账号需要填写账号名称。</div>
            <div class="mt-3">
              <input type="file" accept=".json,application/json" @change="onFileChange" />
            </div>
            <div class="mt-3 flex gap-2">
              <button
                class="flex-1 rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
                :disabled="running || !uploadFile || !canSubmit"
                @click="uploadBilibili"
              >
                {{ running ? '上传中...' : mode === 'refresh' ? '上传并更新账号' : '上传并创建账号' }}
              </button>
            </div>
          </div>

          <!-- Actions -->
          <div v-if="form.platformType !== 5" class="flex gap-2">
            <button
              class="flex-1 rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              :disabled="running || !canSubmit"
              @click="start"
            >
              {{ running ? '进行中...' : '开始登录' }}
            </button>
            <button
              class="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="!running"
              @click="stop"
            >
              停止
            </button>
          </div>

          <div v-if="isManualPlatform" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div class="text-xs font-medium text-slate-700">手动登录提示</div>
            <div class="mt-1 text-sm text-slate-700">{{ manualHint }}</div>
            <div class="mt-3 flex gap-2">
              <button
                class="flex-1 rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
                :disabled="!running || !sessionId"
                @click="confirmManual"
              >
                我已完成登录
              </button>
            </div>
            <div v-if="sessionId" class="mt-2 text-xs text-slate-400">session_id: {{ sessionId }}</div>
          </div>
        </div>

        <!-- Right: QR + status -->
        <div class="space-y-4">
          <div class="rounded-2xl border border-slate-200 bg-white p-4">
            <div class="text-xs font-medium text-slate-700">扫码区域</div>
            <div class="mt-3 flex items-center justify-center">
              <div v-if="qr" class="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
                <img :src="qr" class="h-56 w-56" alt="QR" />
              </div>
              <div v-else class="text-sm text-slate-500">
                {{ isQrPlatform ? '点击“开始登录”后，二维码会显示在这里' : '当前平台不是扫码登录' }}
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-white p-4">
            <div class="text-xs font-medium text-slate-700">状态</div>
            <div class="mt-1 text-sm text-slate-800">{{ status || '—' }}</div>
          </div>
        </div>
      </div>

      <div class="border-t border-slate-200/70 px-6 py-4 text-right">
        <button class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm hover:bg-slate-50" @click="close">
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { loginApi } from '@/api/login'
import { toast } from '@/utils/toast'

const props = defineProps({
  open: { type: Boolean, default: false },
  mode: { type: String, default: 'add' }, // add | refresh
  account: { type: Object, default: null } // refresh 时传入 { id, type, userName }
})

const emit = defineEmits(['update:open', 'success'])

const platformOptions = [
  { value: 1, label: '小红书（扫码）' },
  { value: 2, label: '视频号（扫码）' },
  { value: 3, label: '抖音（扫码）' },
  { value: 4, label: '快手（扫码）' },
  { value: 5, label: 'Bilibili（上传Cookie）' },
  { value: 6, label: '百家号（手动登录）' },
  { value: 7, label: 'TikTok（手动登录）' }
]

const form = ref({
  platformType: 3,
  accountName: ''
})

const running = ref(false)
const status = ref('')
const qr = ref('')
const sessionId = ref('')
const uploadFile = ref(null)

let es = null
let pollTimer = null

const isQrPlatform = computed(() => [1, 2, 3, 4].includes(form.value.platformType))
const isManualPlatform = computed(() => [6, 7].includes(form.value.platformType))

const title = computed(() => (props.mode === 'refresh' ? '刷新 Cookie' : '添加账号'))
const subtitle = computed(() => {
  if (form.value.platformType === 5) return '通过上传 Cookie 文件创建账号（仅 Bilibili）'
  if (isManualPlatform.value) return '将打开浏览器窗口，请手动登录并在前端确认'
  return '扫码登录：二维码有效期有限，请尽快扫码'
})

const manualHint = computed(() => {
  if (!isManualPlatform.value) return ''
  return '后端会打开浏览器登录页。完成登录后点击“我已完成登录”。'
})

const canSubmit = computed(() => {
  if (!form.value.accountName) return false
  if (props.mode === 'refresh' && props.account?.id) return true
  return true
})

const reset = () => {
  stop()
  running.value = false
  status.value = ''
  qr.value = ''
  sessionId.value = ''
  uploadFile.value = null
}

watch(
  () => props.open,
  (v) => {
    if (!v) return
    reset()
    if (props.mode === 'refresh' && props.account) {
      form.value.platformType = Number(props.account.type)
      form.value.accountName = String(props.account.userName || '')
    } else {
      form.value.platformType = 3
      form.value.accountName = ''
    }
  }
)

const close = () => {
  reset()
  emit('update:open', false)
}

const stop = () => {
  running.value = false
  if (es) {
    es.close()
    es = null
  }
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const normalizeImg = (raw) => {
  if (!raw) return ''
  if (raw.startsWith('data:') || raw.startsWith('http')) return raw
  return `data:image/png;base64,${raw}`
}

const handleRawMessage = (raw) => {
  try {
    const obj = JSON.parse(raw)
    if (obj?.event === 'session' && obj?.session_id) {
      sessionId.value = obj.session_id
    }
    if (obj?.event === 'qrcode' && obj?.img) {
      qr.value = normalizeImg(obj.img)
      status.value = obj?.msg || '请扫码登录'
      return { done: false }
    }
    if (obj?.event === 'manual_required' || obj?.event === 'manual') {
      if (obj?.session_id) sessionId.value = obj.session_id
      status.value = obj?.msg || '请手动登录'
      return { done: false }
    }
    if (obj?.event === 'success') {
      status.value = obj?.msg || '成功'
      return { done: true, success: true }
    }
    if (obj?.event === 'error') {
      status.value = obj?.msg || '失败'
      return { done: true, success: false }
    }
    if (obj?.msg) status.value = obj.msg
    return { done: false }
  } catch {
    status.value = raw
    if (String(raw).includes('200') || String(raw).includes('成功')) return { done: true, success: true }
    if (String(raw).includes('500') || String(raw).includes('失败')) return { done: true, success: false }
    return { done: false }
  }
}

const startWithSSE = () => {
  es = loginApi.loginWithSSE(form.value.platformType, form.value.accountName)
  es.onmessage = (evt) => {
    const r = handleRawMessage(evt.data)
    if (r?.done) {
      if (r.success) {
        toast.success(props.mode === 'refresh' ? '刷新成功' : '登录成功')
        emit('success')
        close()
      } else {
        toast.error(status.value || '失败')
      }
      stop()
    }
  }
  es.onerror = () => {
    if (running.value) toast.error('登录连接异常（可能已完成或网络问题）')
    stop()
  }
}

const startWithPoll = async () => {
  if (!props.account?.id) {
    toast.error('缺少账号信息')
    stop()
    return
  }
  status.value = '正在启动刷新...'
  const res = await loginApi.refreshCookieWithLogin(props.account.id)
  sessionId.value = res?.data?.session_id || ''
  if (!sessionId.value) {
    toast.error('启动失败')
    stop()
    return
  }
  status.value = '已启动，等待二维码/状态...'

  pollTimer = setInterval(async () => {
    try {
      const s = await loginApi.getLoginStatus(sessionId.value)
      const msgs = s?.data?.messages || []
      for (const m of msgs) {
        const r = handleRawMessage(m)
        if (r?.done) {
          if (r.success) {
            toast.success('刷新成功')
            emit('success')
            close()
          } else {
            toast.error(status.value || '刷新失败')
          }
          stop()
          return
        }
      }
      if (s?.data?.done) {
        // done 但没有明确 success/error
        stop()
      }
    } catch {
      // 轮询异常：停止，避免无限请求
      stop()
    }
  }, 800)
}

const start = async () => {
  stop()
  running.value = true
  status.value = props.mode === 'refresh' ? '准备刷新...' : '正在连接...'
  qr.value = ''
  sessionId.value = ''

  try {
    if (props.mode === 'refresh') {
      await startWithPoll()
    } else {
      startWithSSE()
    }
  } catch {
    toast.error('启动失败')
    stop()
  }
}

const confirmManual = async () => {
  if (!sessionId.value) return
  try {
    await loginApi.confirmManual(sessionId.value)
    toast.success('已确认，等待后端保存 Cookie')
  } catch {
    toast.error('确认失败')
  }
}

const onFileChange = (e) => {
  const f = e?.target?.files?.[0]
  uploadFile.value = f || null
}

const uploadBilibili = async () => {
  if (!uploadFile.value) return
  running.value = true
  status.value = '正在上传...'
  try {
    const res = await loginApi.uploadCookie({
      file: uploadFile.value,
      platformType: 5,
      accountId: props.mode === 'refresh' ? props.account?.id : null,
      accountName: props.mode === 'add' ? form.value.accountName : null
    })
    toast.success(res?.msg || '上传成功')
    running.value = false
    emit('success')
    close()
  } catch (e) {
    running.value = false
    toast.error('上传失败')
  }
}

onBeforeUnmount(() => stop())
</script>


