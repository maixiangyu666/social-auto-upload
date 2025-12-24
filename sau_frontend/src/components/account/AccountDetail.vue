<template>
  <div v-if="account" class="account-detail">
    <div class="detail-header">
      <h3 class="text-lg font-semibold text-slate-900">账号详情</h3>
      <button
        @click="$emit('close')"
        class="text-slate-400 hover:text-slate-600 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div class="detail-content space-y-6">
      <!-- 基本信息 -->
      <Card class="p-6">
        <h4 class="text-sm font-semibold text-slate-700 mb-4">基本信息</h4>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-xs text-slate-500">平台</label>
            <p class="text-sm font-medium text-slate-900">{{ account.platform_name || getPlatformName(account.type) }}</p>
          </div>
          <div>
            <label class="text-xs text-slate-500">账号名称</label>
            <p class="text-sm font-medium text-slate-900">{{ account.userName }}</p>
          </div>
          <div>
            <label class="text-xs text-slate-500">状态</label>
            <Badge :variant="getStatusVariant(account.status)">
              {{ getStatusText(account.status) }}
            </Badge>
          </div>
          <div v-if="account.group_id">
            <label class="text-xs text-slate-500">分组</label>
            <p class="text-sm font-medium text-slate-900">{{ groupName }}</p>
          </div>
        </div>
      </Card>

      <!-- 统计信息 -->
      <Card class="p-6">
        <h4 class="text-sm font-semibold text-slate-700 mb-4">统计信息</h4>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="text-xs text-slate-500">发布次数</label>
            <p class="text-2xl font-bold text-slate-900">{{ statistics.publish_count || 0 }}</p>
          </div>
          <div>
            <label class="text-xs text-slate-500">成功次数</label>
            <p class="text-2xl font-bold text-green-600">{{ statistics.success_count || 0 }}</p>
          </div>
          <div>
            <label class="text-xs text-slate-500">成功率</label>
            <p class="text-2xl font-bold text-blue-600">{{ statistics.success_rate || 0 }}%</p>
          </div>
        </div>
        <div class="mt-4 pt-4 border-t border-slate-200">
          <label class="text-xs text-slate-500">最后使用时间</label>
          <p class="text-sm text-slate-700">{{ formatTime(statistics.last_used_time) || '未使用' }}</p>
        </div>
      </Card>

      <!-- Cookie信息 -->
      <Card class="p-6">
        <h4 class="text-sm font-semibold text-slate-700 mb-4">Cookie信息</h4>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-slate-500">最后验证时间</label>
            <p class="text-sm text-slate-700">{{ formatTime(account.last_verify_time) || '未验证' }}</p>
          </div>
          <div v-if="account.auto_refresh_enabled">
            <label class="text-xs text-slate-500">下次刷新时间</label>
            <p class="text-sm text-slate-700">{{ formatTime(account.next_refresh_time) || '未设置' }}</p>
          </div>
          <div>
            <label class="text-xs text-slate-500">自动刷新</label>
            <Badge :variant="account.auto_refresh_enabled ? 'success' : 'default'">
              {{ account.auto_refresh_enabled ? '已启用' : '未启用' }}
            </Badge>
          </div>
        </div>
      </Card>

      <!-- 操作按钮 -->
      <div class="flex gap-3">
        <Button @click="handleVerify" :loading="verifying" variant="secondary" size="sm">
          验证Cookie
        </Button>
        <Button @click="handleRefresh" :loading="refreshing" variant="secondary" size="sm">
          刷新Cookie
        </Button>
        <Button @click="handleEdit" variant="secondary" size="sm">
          编辑
        </Button>
        <Button @click="handleDelete" variant="danger" size="sm">
          删除
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { accountApi, groupApi } from '@/api'
import { toast } from '@/utils/toast'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'

const props = defineProps({
  account: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'refresh', 'edit', 'delete'])

const statistics = ref({})
const groupName = ref('')
const verifying = ref(false)
const refreshing = ref(false)

const platformNames = {
  1: '小红书',
  2: '视频号',
  3: '抖音',
  4: '快手',
  5: 'Bilibili',
  6: '百家号',
  7: 'TikTok'
}

const getPlatformName = (type) => platformNames[type] || '未知'

const getStatusText = (status) => {
  const statusMap = {
    0: '无效',
    1: '有效',
    2: '验证中'
  }
  return statusMap[status] || '未知'
}

const getStatusVariant = (status) => {
  const variantMap = {
    0: 'danger',
    1: 'success',
    2: 'warning'
  }
  return variantMap[status] || 'default'
}

const formatTime = (timeStr) => {
  if (!timeStr) return null
  return new Date(timeStr).toLocaleString('zh-CN')
}

const loadStatistics = async () => {
  if (!props.account?.id) return
  
  try {
    const res = await accountApi.getAccountStatistics(props.account.id)
    if (res.data.code === 200) {
      statistics.value = res.data.data
    }
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

const loadGroupName = async () => {
  if (!props.account?.group_id) return
  
  try {
    const res = await groupApi.getGroupDetail(props.account.group_id)
    if (res.data.code === 200) {
      groupName.value = res.data.data.name
    }
  } catch (error) {
    console.error('获取分组名称失败:', error)
  }
}

const handleVerify = async () => {
  verifying.value = true
  try {
    const res = await accountApi.batchVerifyAccounts([props.account.id])
    if (res.data.code === 200) {
      toast.success('验证完成')
      emit('refresh')
    } else {
      toast.error(res.data.msg || '验证失败')
    }
  } catch (error) {
    toast.error('验证失败')
  } finally {
    verifying.value = false
  }
}

const handleRefresh = async () => {
  refreshing.value = true
  try {
    const res = await accountApi.refreshCookie(props.account.id)
    if (res.data.code === 200) {
      toast.success('刷新成功')
      emit('refresh')
    } else {
      toast.error(res.data.msg || '刷新失败')
    }
  } catch (error) {
    toast.error('刷新失败')
  } finally {
    refreshing.value = false
  }
}

const handleEdit = () => {
  emit('edit', props.account)
}

const handleDelete = () => {
  if (confirm('确定要删除此账号吗？')) {
    emit('delete', props.account.id)
  }
}

onMounted(() => {
  if (props.account) {
    loadStatistics()
    loadGroupName()
  }
})
</script>

<style scoped>
.account-detail {
  @apply w-full max-w-md bg-white rounded-2xl shadow-xl p-6;
}

.detail-header {
  @apply flex items-center justify-between mb-6;
}

.detail-content {
  @apply space-y-4;
}
</style>

