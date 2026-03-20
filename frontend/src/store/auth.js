import { defineStore } from 'pinia'
import axios from 'axios'

const DAILY_ADMIN_IMPLICIT_PERMISSIONS = new Set([
  'manage_staff',
  'edit_notices',
  'edit_prices',
  'edit_cases',
  'edit_settings',
  'edit_knowledge'
])

const ADMIN_PERMISSIONS = [
  'manage_staff',
  'edit_notices',
  'edit_prices',
  'edit_cases',
  'edit_settings',
  'view_logs',
  'edit_knowledge'
]

function getUserPermissions(user) {
  return Array.isArray(user?.permissions) ? user.permissions : []
}

function userHasPermission(user, permission) {
  if (!user || !permission) {
    return false
  }

  if (user.role === 'owner' || user.role === 'super_admin') {
    return true
  }

  if (user.role === 'daily_admin' && DAILY_ADMIN_IMPLICIT_PERMISSIONS.has(permission)) {
    return true
  }

  return getUserPermissions(user).includes(permission)
}

axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => Promise.reject(error))

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => ADMIN_PERMISSIONS.some((permission) => userHasPermission(state.user, permission)),
    isSuperAdmin: (state) => state.user?.role === 'owner' || state.user?.role === 'super_admin',
    hasPermission: (state) => (permission) => userHasPermission(state.user, permission),
    canManageStaff: (state) => userHasPermission(state.user, 'manage_staff'),
    canEditNotices: (state) => userHasPermission(state.user, 'edit_notices'),
    canEditSettings: (state) => userHasPermission(state.user, 'edit_settings'),
    canViewChatAudit: (state) => userHasPermission(state.user, 'view_logs'),
    canManageAllBranches: (state) => {
      return ['owner', 'super_admin', 'daily_admin'].includes(state.user?.role) && userHasPermission(state.user, 'manage_staff')
    },
    userName: (state) => state.user?.full_name || state.user?.username || '未登录',
    roleName: (state) => {
      const roleMap = {
        owner: '老板',
        super_admin: '超级管理员',
        executive: '高管',
        daily_admin: '日常管理员',
        staff_admin: '普通管理员',
        branch_admin: '分公司管理员',
        employee: '员工'
      }
      return roleMap[state.user?.role] || '未知角色'
    }
  },

  actions: {
    async login(username, password, rememberMe = false) {
      this.loading = true
      this.error = null
      try {
        const formData = new FormData()
        formData.append('username', username)
        formData.append('password', password)
        formData.append('remember_me', rememberMe ? 'true' : 'false')

        const response = await axios.post('/api/auth/login', formData)
        const { access_token, user } = response.data

        this.token = access_token
        this.user = user

        localStorage.setItem('token', access_token)
        localStorage.setItem('user', JSON.stringify(user))
        axios.defaults.headers.common.Authorization = `Bearer ${access_token}`

        return true
      } catch (err) {
        this.error = err.response?.data?.detail || '登录失败，请检查网络或账号密码'
        return false
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      delete axios.defaults.headers.common.Authorization
    },

    initAuth() {
      if (this.token) {
        axios.defaults.headers.common.Authorization = `Bearer ${this.token}`
      }
    }
  }
})
