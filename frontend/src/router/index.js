import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tools',
    name: 'Tools',
    component: () => import('../views/ToolsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/AdminView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/notices',
    name: 'NoticeManager',
    component: () => import('../views/NoticeView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/staff',
    name: 'Staff',
    component: () => import('../views/StaffView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/lab',
    name: 'Lab',
    component: () => import('../views/LabView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/chat-logs',
    name: 'ChatLogs',
    component: () => import('../views/ChatLogsView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, requiresChatAudit: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation Guard
import { useAuthStore } from '../store/auth'

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  // 检查是否需要登录
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/login')
  }
  // 检查是否需要管理员权限
  else if (to.meta.requiresAdmin && !auth.isAdmin) {
    next('/')
  }
  else if (to.meta.requiresChatAudit && !auth.canViewChatAudit) {
    next('/admin')
  }
  // 已登录状态访问登录页，跳转首页
  else if (to.name === 'Login' && auth.isAuthenticated) {
    next('/')
  }
  else {
    next()
  }
})

export default router
