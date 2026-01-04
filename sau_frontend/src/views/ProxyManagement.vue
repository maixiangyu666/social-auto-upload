<template>
  <div class="space-y-4">
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div class="text-lg font-semibold text-slate-900">代理管理</div>
        <div class="text-xs text-slate-600">添加和管理代理服务器</div>
      </div>
      <button
        type="button"
        class="rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
        @click="openAddModal()"
      >
        添加代理
      </button>
    </header>

    <section class="rounded-2xl border border-slate-200 bg-white">
      <div class="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
        代理列表（{{ total }}）
      </div>
      <div class="p-4">
        <div v-if="loading" class="text-sm text-slate-500">加载中...</div>
        <div v-else-if="proxies.length === 0" class="text-sm text-slate-500">暂无代理</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-xs text-slate-500">
              <tr>
                <th class="py-2 pr-4">ID</th>
                <th class="py-2 pr-4">代理名称</th>
                <th class="py-2 pr-4">类型</th>
                <th class="py-2 pr-4">地址</th>
                <th class="py-2 pr-4">端口</th>
                <th class="py-2 pr-4">状态</th>
                <th class="py-2">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="p in proxies" :key="p.id" class="hover:bg-slate-50">
                <td class="py-3 pr-4 text-slate-700">{{ p.id }}</td>
                <td class="py-3 pr-4 font-medium text-slate-900">{{ p.proxy_name }}</td>
                <td class="py-3 pr-4">
                  <span class="inline-flex rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">
                    {{ p.proxy_type.toUpperCase() }}
                  </span>
                </td>
                <td class="py-3 pr-4 text-slate-600">{{ p.host }}</td>
                <td class="py-3 pr-4 text-slate-600">{{ p.port }}</td>
                <td class="py-3 pr-4">
                  <span class="inline-flex rounded-full px-2 py-1 text-xs" :class="p.is_enabled ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'">
                    {{ p.is_enabled ? '启用' : '禁用' }}
                  </span>
                </td>
                <td class="py-3">
                  <button
                    type="button"
                    class="text-xs font-medium text-slate-700 hover:text-slate-900"
                    @click="openEditModal(p)"
                  >
                    编辑
                  </button>
                  <button
                    type="button"
                    class="ml-3 text-xs font-medium text-rose-700 hover:text-rose-900"
                    @click="deleteProxy(p.id)"
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
            <select v-model.number="pageSize" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm" @change="page = 1; loadProxies()">
              <option :value="10">10 / 页</option>
              <option :value="20">20 / 页</option>
              <option :value="50">50 / 页</option>
              <option :value="100">100 / 页</option>
            </select>
            <button
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="page <= 1"
              @click="page = Math.max(1, page - 1); loadProxies()"
            >
              上一页
            </button>
            <button
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="page >= Math.max(1, Math.ceil(total / pageSize))"
              @click="page = page + 1; loadProxies()"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Add/Edit Modal -->
    <Modal :open="modalOpen" :title="editingProxy ? '编辑代理' : '添加代理'" @close="modalOpen = false">
      <div class="space-y-4">
        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">代理名称 *</div>
          <input
            v-model.trim="form.proxy_name"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            placeholder="例如：美国代理1"
          />
        </label>

        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">代理类型 *</div>
          <select v-model="form.proxy_type" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">
            <option value="http">HTTP</option>
            <option value="https">HTTPS</option>
            <option value="socks5">SOCKS5</option>
          </select>
        </label>

        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">主机地址 *</div>
          <input
            v-model.trim="form.host"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            placeholder="例如：192.168.1.1 或 proxy.example.com"
          />
        </label>

        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">端口 *</div>
          <input
            v-model.number="form.port"
            type="number"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            placeholder="例如：8080"
          />
        </label>

        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">用户名（可选）</div>
          <input
            v-model.trim="form.username"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            placeholder="代理服务器认证用户名"
          />
        </label>

        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">密码（可选）</div>
          <input
            v-model="form.password"
            type="password"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            placeholder="代理服务器认证密码"
          />
        </label>

        <label class="space-y-1">
          <div class="text-xs font-medium text-slate-600">备注（可选）</div>
          <input
            v-model.trim="form.remark"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            placeholder="备注信息"
          />
        </label>

        <div class="flex gap-2">
          <button class="rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800" @click="saveProxy">
            保存
          </button>
          <button class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50" @click="modalOpen = false">
            取消
          </button>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { proxyApi } from '@/api/proxy'
import { toast } from '@/utils/toast'
import Modal from '@/components/ui/Modal.vue'

const loading = ref(false)
const proxies = ref([])
const total = ref(0)
const pageSize = ref(20)
const page = ref(1)

const modalOpen = ref(false)
const editingProxy = ref(null)
const form = ref({
  proxy_name: '',
  proxy_type: 'http',
  host: '',
  port: '',
  username: '',
  password: '',
  remark: ''
})

const loadProxies = async () => {
  loading.value = true
  try {
    const res = await proxyApi.getProxies({
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value
    })
    if (res?.code !== 200) {
      toast.error(res?.msg || '加载失败')
      return
    }
    proxies.value = res.data?.items || []
    total.value = res.data?.total || proxies.value.length
  } catch (e) {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  editingProxy.value = null
  form.value = {
    proxy_name: '',
    proxy_type: 'http',
    host: '',
    port: '',
    username: '',
    password: '',
    remark: ''
  }
  modalOpen.value = true
}

const openEditModal = (p) => {
  editingProxy.value = p
  form.value = {
    proxy_name: p.proxy_name,
    proxy_type: p.proxy_type,
    host: p.host,
    port: p.port,
    username: p.username || '',
    password: '', // 不显示密码
    remark: p.remark || ''
  }
  modalOpen.value = true
}

const saveProxy = async () => {
  if (!form.value.proxy_name || !form.value.host || !form.value.port) {
    toast.error('请填写必填字段')
    return
  }

  const data = { ...form.value }
  if (!data.username) delete data.username
  if (!data.password) delete data.password
  if (!data.remark) delete data.remark

  let res
  if (editingProxy.value) {
    res = await proxyApi.updateProxy(editingProxy.value.id, data)
  } else {
    res = await proxyApi.createProxy(data)
  }

  if (res?.code === 200) {
    toast.success(editingProxy.value ? '更新成功' : '添加成功')
    modalOpen.value = false
    await loadProxies()
  } else {
    toast.error(res?.msg || '保存失败')
  }
}

const deleteProxy = async (id) => {
  if (!confirm('确定删除该代理吗？')) return
  const res = await proxyApi.deleteProxy(id)
  if (res?.code === 200) {
    toast.success('已删除')
    const maxPage = Math.max(1, Math.ceil((total.value - 1) / pageSize.value))
    if (page.value > maxPage) page.value = maxPage
    await loadProxies()
  } else {
    toast.error(res?.msg || '删除失败')
  }
}

onMounted(() => {
  loadProxies()
})
</script>
