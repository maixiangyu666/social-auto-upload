<template>
  <div class="group-manager">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-slate-900">分组管理</h3>
      <Button @click="showCreateModal = true" size="sm" variant="primary">
        + 新建分组
      </Button>
    </div>

    <div class="space-y-2">
      <div
        v-for="group in groups"
        :key="group.id"
        @click="selectGroup(group.id)"
        :class="[
          'group-item p-3 rounded-lg cursor-pointer transition-all',
          selectedGroupId === group.id ? 'bg-slate-100 border-2 border-slate-300' : 'bg-white border border-slate-200 hover:border-slate-300'
        ]"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div
              class="w-3 h-3 rounded-full"
              :style="{ backgroundColor: group.color || '#94a3b8' }"
            ></div>
            <span class="font-medium text-slate-900">{{ group.name }}</span>
            <Badge variant="default" size="sm">{{ group.account_count || 0 }}</Badge>
          </div>
          <div class="flex gap-2">
            <button
              @click.stop="handleEdit(group)"
              class="text-slate-400 hover:text-slate-600"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              @click.stop="handleDelete(group)"
              class="text-red-400 hover:text-red-600"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        <p v-if="group.description" class="text-xs text-slate-500 mt-1">{{ group.description }}</p>
      </div>
    </div>

    <!-- 创建/编辑分组模态框 -->
    <Modal v-model="showCreateModal" :title="editingGroup ? '编辑分组' : '新建分组'">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">分组名称</label>
          <Input v-model="groupForm.name" placeholder="请输入分组名称" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">分组描述</label>
          <Input v-model="groupForm.description" placeholder="请输入分组描述（可选）" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">分组颜色</label>
          <Input v-model="groupForm.color" type="color" />
        </div>
        <div class="flex gap-3 justify-end">
          <Button @click="showCreateModal = false" variant="ghost">取消</Button>
          <Button @click="handleSave" variant="primary">保存</Button>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { groupApi } from '@/api'
import { toast } from '@/utils/toast'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Input from '@/components/ui/Input.vue'
import Modal from '@/components/ui/Modal.vue'

const props = defineProps({
  selectedGroupId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:selectedGroupId', 'refresh'])

const groups = ref([])
const showCreateModal = ref(false)
const editingGroup = ref(null)
const groupForm = ref({
  name: '',
  description: '',
  color: '#94a3b8'
})

const loadGroups = async () => {
  try {
    const res = await groupApi.getGroups({ limit: 200, offset: 0 })
    if (res?.code === 200) {
      groups.value = res.data?.items || []
    }
  } catch (error) {
    toast.error('加载分组失败')
  }
}

const selectGroup = (groupId) => {
  emit('update:selectedGroupId', groupId)
}

const handleEdit = (group) => {
  editingGroup.value = group
  groupForm.value = {
    name: group.name,
    description: group.description || '',
    color: group.color || '#94a3b8'
  }
  showCreateModal.value = true
}

const handleDelete = async (group) => {
  if (!confirm(`确定要删除分组"${group.name}"吗？`)) return
  
  try {
    const res = await groupApi.deleteGroup(group.id)
    if (res?.code === 200) {
      toast.success('删除成功')
      loadGroups()
      emit('refresh')
    } else {
      toast.error(res?.msg || '删除失败')
    }
  } catch (error) {
    toast.error('删除失败')
  }
}

const handleSave = async () => {
  if (!groupForm.value.name.trim()) {
    toast.error('分组名称不能为空')
    return
  }
  
  try {
    let res
    if (editingGroup.value) {
      res = await groupApi.updateGroup(editingGroup.value.id, groupForm.value)
    } else {
      res = await groupApi.createGroup(groupForm.value)
    }
    
    if (res?.code === 200) {
      toast.success(editingGroup.value ? '更新成功' : '创建成功')
      showCreateModal.value = false
      editingGroup.value = null
      groupForm.value = { name: '', description: '', color: '#94a3b8' }
      loadGroups()
      emit('refresh')
    } else {
      toast.error(res?.msg || '操作失败')
    }
  } catch (error) {
    toast.error('操作失败')
  }
}

onMounted(() => {
  loadGroups()
})
</script>

<style scoped>
.group-manager {
  @apply w-full;
}
</style>

