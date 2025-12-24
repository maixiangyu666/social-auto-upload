<template>
  <div class="space-y-4">
    <header class="flex items-center justify-between">
      <div>
        <div class="text-lg font-semibold text-slate-900">任务详情</div>
        <div class="text-xs text-slate-600">查看任务信息、错误原因，支持取消/重试</div>
      </div>
      <button
        type="button"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50"
        @click="goBack"
      >
        返回
      </button>
    </header>

    <section class="rounded-2xl border border-slate-200 bg-white p-4">
      <div v-if="loading" class="text-sm text-slate-500">加载中...</div>
      <div v-else-if="!task" class="text-sm text-slate-500">任务不存在</div>
      <div v-else class="space-y-4">
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
          <InfoItem label="任务ID" :value="String(task.id)" />
          <InfoItem label="任务名称" :value="task.task_name || '-'" />
          <InfoItem label="标题" :value="task.title" class="md:col-span-2" />
          <InfoItem label="平台" :value="platformName(task.platform_type)" />
          <InfoItem label="状态">
            <span class="inline-flex rounded-full px-2 py-1 text-xs" :class="statusPill(task.status)">
              {{ statusName(task.status) }}
            </span>
          </InfoItem>
          <InfoItem label="账号ID" :value="String(task.account_id)" />
          <InfoItem label="文件ID" :value="String(task.file_id)" />
          <InfoItem label="重试次数" :value="`${task.retry_count ?? 0} / ${task.max_retry ?? 3}`" />
          <InfoItem label="创建时间" :value="task.create_time || '-'" />
          <InfoItem label="更新时间" :value="task.update_time || '-'" />
          <InfoItem v-if="task.scheduled_time" label="计划发布时间" :value="task.scheduled_time" />
          <InfoItem v-if="task.publish_time" label="实际发布时间" :value="task.publish_time" />
          <InfoItem v-if="task.platform_video_url" label="平台视频链接" class="md:col-span-2">
            <a :href="task.platform_video_url" target="_blank" class="text-sm font-medium text-indigo-700 hover:text-indigo-900">
              打开链接
            </a>
          </InfoItem>
        </div>

        <div v-if="task.error_message" class="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
          <div class="text-xs font-semibold">错误信息</div>
          <div class="mt-1 whitespace-pre-wrap">{{ task.error_message }}</div>
        </div>

        <div class="flex flex-wrap gap-2">
          <button
            v-if="task.status === 0 || task.status === 1"
            type="button"
            class="rounded-xl bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700"
            @click="cancel"
          >
            取消任务
          </button>
          <button
            v-if="task.status === 3"
            type="button"
            class="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            @click="retry"
          >
            重试任务
          </button>
          <button
            type="button"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm hover:bg-slate-50"
            @click="reload"
          >
            刷新
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { taskApi } from '@/api/task'
import { toast } from '@/utils/toast'

const route = useRoute()
const router = useRouter()

const id = computed(() => route.params.id)
const loading = ref(false)
const task = ref(null)

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

const reload = async () => {
  loading.value = true
  try {
    const res = await taskApi.getTask(id.value)
    if (res?.code === 200) task.value = res.data
    else {
      task.value = null
      toast.error(res?.msg || '加载失败')
    }
  } catch {
    task.value = null
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

const cancel = async () => {
  if (!task.value) return
  if (!confirm(`确定取消任务「${task.value.title}」吗？`)) return
  const res = await taskApi.cancelTask(task.value.id)
  if (res?.code === 200) {
    toast.success('已取消')
    await reload()
  } else {
    toast.error(res?.msg || '取消失败')
  }
}

const retry = async () => {
  if (!task.value) return
  if (!confirm(`确定重试任务「${task.value.title}」吗？`)) return
  const res = await taskApi.retryTask(task.value.id)
  if (res?.code === 200) {
    toast.success('已重新执行')
    await reload()
  } else {
    toast.error(res?.msg || '重试失败')
  }
}

const goBack = () => router.push('/task-management')

onMounted(reload)

const InfoItem = {
  props: { label: String, value: String },
  template: `
    <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
      <div class="text-xs font-medium text-slate-600">{{ label }}</div>
      <div class="mt-1 text-sm text-slate-900">
        <slot>{{ value }}</slot>
      </div>
    </div>
  `,
}
</script>


