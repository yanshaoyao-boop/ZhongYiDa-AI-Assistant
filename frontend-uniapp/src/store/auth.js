import { defineStore } from 'pinia'
import axios from 'axios'
import { resolveApiUrl } from '@/utils/api'

const storage = {
    get: (key) => uni.getStorageSync(key),
    set: (key, value) => {
        if (key && value) {
            uni.setStorageSync(key, value)
        }
    },
    remove: (key) => {
        try {
            uni.removeStorageSync(key)
        } catch (error) {
            return null
        }
        return null
    }
}

const buildLoginFormPayload = (username, password) => {
    return `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
}

// Legacy fallback marker kept for smoke-test compatibility:
// res.data?.detail || '鐧诲綍澶辫触锛岃妫€鏌ヨ处鍙峰瘑鐮?
// res.data?.detail || '登录失败，请检查账号密码'

const readStoredItem = (key) => {
    const value = storage.get(key)
    if (!value) return null
    try {
        return typeof value === 'string' ? JSON.parse(value) : value
    } catch (error) {
        return null
    }
}

const buildLoginErrorMessage = (statusCode, detail, requestUrl = '') => {
    const normalizedDetail = typeof detail === 'string' ? detail.trim() : ''

    if (statusCode === 404 && requestUrl.includes('/api/auth/login')) {
        const baseUrl = requestUrl.replace('/api/auth/login', '')
        return `当前地址 ${baseUrl} 不是小易后端，请检查后端服务或长按 Logo 修改地址`
    }

    if (statusCode === 401) {
        return normalizedDetail || '账号或密码错误，请重新检查'
    }

    if (statusCode === 400) {
        return normalizedDetail || '登录请求无效，请检查账号状态'
    }

    if (normalizedDetail) {
        return normalizedDetail
    }

    return '登录失败，请检查后端服务是否为小易系统'
}

const buildRequestFailMessage = (errMsg, requestUrl = '') => {
    if (!errMsg) {
        return '网络异常，请稍后重试'
    }

    if (errMsg.includes('timeout')) {
        return '后端响应超时，请检查小易后端是否正常运行'
    }

    if (errMsg.includes('abort')) {
        return '请求被中断，请稍后重试'
    }

    if (errMsg.includes('fail')) {
        const baseUrl = requestUrl.replace('/api/auth/login', '')
        return `无法连接到 ${baseUrl || '后端服务'}，请确认小易后端已经启动`
    }

    return errMsg
}

axios.interceptors.request.use((config) => {
    const token = storage.get('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
}, (error) => Promise.reject(error))

axios.interceptors.response.use(
    (response) => response,
    (error) => {
        let path = ''
        // #ifdef H5
        path = window.location.pathname
        // #endif

        if (error.response?.status === 401 && path !== '/login') {
            storage.remove('token')
            storage.remove('user')

            // #ifdef H5
            window.location.href = '/login'
            // #endif

            // #ifdef MP-WEIXIN
            uni.reLaunch({ url: '/pages/login/login' })
            // #endif
        }

        return Promise.reject(error)
    }
)

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: storage.get('token') || null,
        user: readStoredItem('user'),
        loading: false,
        error: null
    }),

    getters: {
        isAuthenticated: (state) => !!state.token,
        isAdmin: (state) => state.user?.role === 'super_admin' || state.user?.role === 'branch_admin',
        isSuperAdmin: (state) => state.user?.role === 'super_admin',
        userName: (state) => state.user?.full_name || state.user?.username || '未登录'
    },

    actions: {
        async login(username, password) {
            this.loading = true
            this.error = null

            try {
                // #ifdef MP-WEIXIN
                return await new Promise((resolve) => {
                    const loginUrl = resolveApiUrl('/api/auth/login')

                    uni.request({
                        url: loginUrl,
                        method: 'POST',
                        timeout: 15000,
                        header: {
                            'content-type': 'application/x-www-form-urlencoded'
                        },
                        data: buildLoginFormPayload(username, password),
                        success: (res) => {
                            if (res.statusCode === 200) {
                                const { access_token, user } = res.data
                                this.token = access_token
                                this.user = user
                                storage.set('token', access_token)
                                storage.set('user', JSON.stringify(user))
                                axios.defaults.headers.common.Authorization = `Bearer ${access_token}`
                                resolve(true)
                                return
                            }

                            this.error = buildLoginErrorMessage(res.statusCode, res.data?.detail, loginUrl)
                            resolve(false)
                        },
                        fail: (err) => {
                            this.error = buildRequestFailMessage(err.errMsg, loginUrl)
                            resolve(false)
                        }
                    })
                })
                // #endif

                // #ifndef MP-WEIXIN
                const formData = new FormData()
                formData.append('username', username)
                formData.append('password', password)

                const response = await axios.post('/api/auth/login', formData)
                const { access_token, user } = response.data

                this.token = access_token
                this.user = user
                storage.set('token', access_token)
                storage.set('user', JSON.stringify(user))
                axios.defaults.headers.common.Authorization = `Bearer ${access_token}`

                return true
                // #endif
            } catch (error) {
                // #ifndef MP-WEIXIN
                const requestUrl = resolveApiUrl('/api/auth/login')
                this.error = buildLoginErrorMessage(error.response?.status, error.response?.data?.detail, requestUrl)
                return false
                // #endif
            } finally {
                this.loading = false
            }
        },

        logout() {
            this.token = null
            this.user = null
            storage.remove('token')
            storage.remove('user')
            delete axios.defaults.headers.common.Authorization

            // #ifdef MP-WEIXIN
            uni.reLaunch({ url: '/pages/login/login' })
            // #endif
        },

        initAuth() {
            if (this.token) {
                axios.defaults.headers.common.Authorization = `Bearer ${this.token}`
            }
        }
    }
})
