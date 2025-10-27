import axios from 'axios'

const API_BASE_URL = '/api/v1'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

// 配置管理API
export const configService = {
  // 获取配置分类
  getCategories: () => apiClient.get('/config/categories'),
  
  // 获取服务状态
  getStatus: () => apiClient.get('/config/status'),
  
  // 更新配置
  updateConfig: (data: any) => apiClient.post('/config/update', data),
  
  // 测试连接
  testConnection: (data: any) => apiClient.post('/config/test', data),
  
  // 同步配置
  syncConfig: () => apiClient.post('/config/sync'),
  
  // 导出配置
  exportConfig: () => apiClient.get('/config/export'),
}

// 消息管理API
export const messageService = {
  // 处理消息
  processMessage: (data: any) => apiClient.post('/messages/process', data),
  
  // 获取消息历史
  getHistory: (params: any) => apiClient.get('/messages/history', { params }),
}

// 租户管理API
export const tenantService = {
  // 创建租户
  createTenant: (data: any) => apiClient.post('/tenants', data),
  
  // 获取租户列表
  getTenants: () => apiClient.get('/tenants'),
  
  // 更新租户
  updateTenant: (id: string, data: any) => apiClient.put(`/tenants/${id}`, data),
  
  // 删除租户
  deleteTenant: (id: string) => apiClient.delete(`/tenants/${id}`),
}

// 健康检查API
export const healthService = {
  // 健康检查
  check: () => apiClient.get('/health'),
}

export default apiClient
