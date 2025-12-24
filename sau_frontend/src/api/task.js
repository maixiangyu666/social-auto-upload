import { http } from '@/utils/request'

// 任务管理相关API
export const taskApi = {
  // 获取任务详情
  getTask(taskId) {
    return http.get(`/getTask/${taskId}`)
  },

  // 查询任务列表
  listTasks(params = {}) {
    return http.get('/listTasks', { params })
  },

  // 取消任务
  cancelTask(taskId) {
    return http.post(`/cancelTask/${taskId}`)
  },

  // 重试任务
  retryTask(taskId) {
    return http.post(`/retryTask/${taskId}`)
  }
}

