import { defineStore } from 'pinia'
import axios from 'axios'

// 拦截器：确保每个请求都带上最新的 Token
axios.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
}, (error) => {
    return Promise.reject(error)
})

// 拦截器：统一处理 401 鉴权失败，自动跳转登录页
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
        // 除了 employee 之外的所有角色都具有管理后台入口权限
        isAdmin: (state) => state.user?.role && state.user?.role !== 'employee',
        // owner 和 历史遗留的 super_admin 视为超级管理员
        isSuperAdmin: (state) => state.user?.role === 'owner' || state.user?.role === 'super_admin',
        canViewChatAudit: (state) => ['owner', 'executive', 'super_admin'].includes(state.user?.role),
        canManageAllBranches: (state) => ['owner', 'super_admin', 'daily_admin'].includes(state.user?.role),
        userName: (state) => state.user?.full_name || state.user?.username || '未登录',
        roleName: (state) => {
            const roleMap = {
                'owner': '老板',
                'super_admin': '超级管理员',
                'executive': '高管',
                'daily_admin': '日常管理员',
                'staff_admin': '人事管理员',
                'branch_admin': '分公司管理员',
                'employee': '普通员工'
            }
            return roleMap[state.user?.role] || '未知角色'
        }
    },

    actions: {
        async login(username, password) {
            this.loading = true
            this.error = null
            try {
                const formData = new FormData()
                formData.append('username', username)
                formData.append('password', password)

                const response = await axios.post('/api/auth/login', formData)

                const { access_token, user } = response.data

                this.token = access_token
                this.user = user

                localStorage.setItem('token', access_token)
                localStorage.setItem('user', JSON.stringify(user))

                // 设置 axios 默认 header
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

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
            delete axios.defaults.headers.common['Authorization']
        },

        initAuth() {
            if (this.token) {
                axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
            }
        }
    }
})
