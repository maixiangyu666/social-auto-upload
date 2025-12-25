<template>
  <div class="space-y-4">
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div class="text-lg font-semibold text-slate-900">素材管理</div>
        <div class="text-xs text-slate-600">上传视频/图片/文本，发布时从这里选择</div>
      </div>
      <div class="flex gap-2">
        <button
          type="button"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50"
          @click="load"
        >
          刷新
        </button>
      </div>
    </header>

    <section class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div class="flex-1">
          <input
            v-model.trim="keyword"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
            placeholder="搜索：文件名"
            @keyup.enter="page = 1; load()"
          />
        </div>

        <div class="flex items-center gap-2">
          <label class="inline-flex cursor-pointer items-center rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800">
            <input class="hidden" type="file" @change="onChooseFile" />
            上传素材
          </label>
        </div>
      </div>

      <div v-if="uploading" class="mt-3 text-xs text-slate-600">上传中：{{ uploadProgress }}%</div>
    </section>

    <section class="rounded-2xl border border-slate-200 bg-white">
      <div class="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
        素材（{{ total }}）
      </div>
      <div class="p-4">
        <div v-if="loading" class="text-sm text-slate-500">加载中...</div>
        <div v-else-if="filtered.length === 0" class="text-sm text-slate-500">暂无素材</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-xs text-slate-500">
              <tr>
                <th class="py-2 pr-4">ID</th>
                <th class="py-2 pr-4">文件名</th>
                <th class="py-2 pr-4">大小(MB)</th>
                <th class="py-2 pr-4">上传时间</th>
                <th class="py-2 pr-4">路径</th>
                <th class="py-2">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="m in filtered" :key="m.id" class="hover:bg-slate-50">
                <td class="py-3 pr-4 text-slate-700">{{ m.id }}</td>
                <td class="py-3 pr-4 font-medium text-slate-900">{{ m.filename }}</td>
                <td class="py-3 pr-4 text-slate-600">{{ m.filesize }}</td>
                <td class="py-3 pr-4 text-slate-600">{{ m.upload_time }}</td>
                <td class="py-3 pr-4 text-slate-600">{{ m.file_path }}</td>
                <td class="py-3">
                  <button class="text-xs font-medium text-slate-700 hover:text-slate-900" @click="preview(m)">
                    预览
                  </button>
                  <button class="ml-3 text-xs font-medium text-slate-700 hover:text-slate-900" @click="download(m)">
                    下载
                  </button>
                  <button class="ml-3 text-xs font-medium text-rose-700 hover:text-rose-900" @click="remove(m)">
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
            <select v-model.number="pageSize" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm" @change="page = 1; load()">
              <option :value="10">10 / 页</option>
              <option :value="20">20 / 页</option>
              <option :value="50">50 / 页</option>
              <option :value="100">100 / 页</option>
            </select>
            <button
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="page <= 1"
              @click="page = Math.max(1, page - 1); load()"
            >
              上一页
            </button>
            <button
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
              :disabled="page >= Math.max(1, Math.ceil(total / pageSize))"
              @click="page = page + 1; load()"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { materialApi } from '@/api/material'
import { toast } from '@/utils/toast'

const loading = ref(false)
const list = ref([])
const keyword = ref('')
const total = ref(0)
const pageSize = ref(20)
const page = ref(1)

const uploading = ref(false)
const uploadProgress = ref(0)

const filtered = computed(() => list.value)

const load = async () => {
  loading.value = true
  try {
    const res = await materialApi.getAllMaterials({
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
      keyword: keyword.value.trim() || undefined,
    })
    if (res?.code !== 200) {
      toast.error(res?.msg || '加载失败')
      list.value = []
      total.value = 0
      return
    }
    const data = res.data || {}
    list.value = data.items ?? []
    total.value = data.total ?? list.value.length
  } catch (e) {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

const onChooseFile = async (e) => {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return

  const formData = new FormData()
  // 后端 /uploadSave 读取 request.files['file']
  formData.append('file', file)

  uploading.value = true
  uploadProgress.value = 0
  try {
    const res = await materialApi.uploadMaterial(formData, (evt) => {
      if (!evt.total) return
      uploadProgress.value = Math.round((evt.loaded / evt.total) * 100)
    })
    if (res?.code === 200) {
      toast.success('上传成功')
      page.value = 1
      await load()
    } else {
      toast.error(res?.msg || '上传失败')
    }
  } catch (err) {
    toast.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const preview = (m) => {
  const url = materialApi.getMaterialPreviewUrl(m.file_path)
  window.open(url, '_blank')
}

const download = (m) => {
  const url = materialApi.downloadMaterial(m.file_path)
  window.open(url, '_blank')
}

const remove = async (m) => {
  if (!confirm(`确定删除素材「${m.filename}」吗？`)) return
  const res = await materialApi.deleteMaterial(m.id)
  if (res?.code === 200) {
    toast.success('已删除')
    const maxPage = Math.max(1, Math.ceil((total.value - 1) / pageSize.value))
    if (page.value > maxPage) page.value = maxPage
    await load()
  } else {
    toast.error(res?.msg || '删除失败')
  }
}

onMounted(load)
</script>


