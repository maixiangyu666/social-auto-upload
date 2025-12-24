<template>
  <div v-if="selectedCount > 0" class="batch-actions bg-white border-t border-slate-200 p-4 rounded-b-lg">
    <div class="flex items-center justify-between">
      <span class="text-sm text-slate-600">
        已选择 <strong class="text-slate-900">{{ selectedCount }}</strong> 个账号
      </span>
      <div class="flex gap-2">
        <Button @click="handleBatchVerify" :loading="loading" variant="secondary" size="sm">
          批量验证
        </Button>
        <Button @click="handleBatchRefresh" :loading="loading" variant="secondary" size="sm">
          批量刷新
        </Button>
        <Button @click="handleBatchAssign" :loading="loading" variant="secondary" size="sm">
          分配分组
        </Button>
        <Button @click="handleBatchDelete" :loading="loading" variant="danger" size="sm">
          批量删除
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { accountApi, groupApi } from '@/api'
import { toast } from '@/utils/toast'
import Button from '@/components/ui/Button.vue'
import Modal from '@/components/ui/Modal.vue'
import Select from '@/components/ui/Select.vue'

const props = defineProps({
  selectedIds: {
    type: Array,
    default: () => []
  },
  groups: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['refresh'])

const selectedCount = computed(() => props.selectedIds.length)
const loading = ref(false)
const showAssignModal = ref(false)
const selectedGroupId = ref(null)

const handleBatchVerify = async () => {
  if (props.selectedIds.length === 0) return
  
  loading.value = true
  try {
    const res = await accountApi.batchVerifyAccounts(props.selectedIds)
    if (res.data.code === 200) {
      toast.success('批量验证完成')
      emit('refresh')
    } else {
      toast.error(res.data.msg || '批量验证失败')
    }
  } catch (error) {
    toast.error('批量验证失败')
  } finally {
    loading.value = false
  }
}

const handleBatchRefresh = async () => {
  if (props.selectedIds.length === 0) return
  
  if (!confirm('确定要批量刷新Cookie吗？这可能需要较长时间。')) return
  
  loading.value = true
  try {
    const res = await accountApi.batchRefreshCookies(props.selectedIds)
    if (res.data.code === 200) {
      toast.success('批量刷新完成')
      emit('refresh')
    } else {
      toast.error(res.data.msg || '批量刷新失败')
    }
  } catch (error) {
    toast.error('批量刷新失败')
  } finally {
    loading.value = false
  }
}

const handleBatchAssign = () => {
  if (props.selectedIds.length === 0) return
  showAssignModal.value = true
}

const handleBatchDelete = async () => {
  if (props.selectedIds.length === 0) return
  
  if (!confirm(`确定要删除选中的 ${props.selectedIds.length} 个账号吗？此操作不可恢复。`)) return
  
  loading.value = true
  try {
    const res = await accountApi.batchDeleteAccounts(props.selectedIds)
    if (res.data.code === 200) {
      toast.success('批量删除成功')
      emit('refresh')
    } else {
      toast.error(res.data.msg || '批量删除失败')
    }
  } catch (error) {
    toast.error('批量删除失败')
  } finally {
    loading.value = false
  }
}

const confirmAssign = async () => {
  if (!selectedGroupId.value && selectedGroupId.value !== 0) {
    toast.error('请选择分组')
    return
  }
  
  loading.value = true
  try {
    const groupId = selectedGroupId.value === 0 ? null : selectedGroupId.value
    const res = await groupApi.batchAssignAccounts(props.selectedIds, groupId)
    if (res.data.code === 200) {
      toast.success('分配成功')
      showAssignModal.value = false
      selectedGroupId.value = null
      emit('refresh')
    } else {
      toast.error(res.data.msg || '分配失败')
    }
  } catch (error) {
    toast.error('分配失败')
  } finally {
    loading.value = false
  }
}
</script>


<style scoped>
.batch-actions {
  @apply sticky bottom-0 z-10;
}
</style>

