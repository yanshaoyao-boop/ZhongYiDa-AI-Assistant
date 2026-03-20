<template>
  <div class="logs-container">
    <header class="logs-header glass-panel">
      <div class="header-main">
        <div class="brand">
          <span class="gradient-text">小易助手会话审计</span>
        </div>
        <div class="nav-actions">
          <router-link to="/admin" class="nav-btn-outline">返回管理大厅</router-link>
        </div>
      </div>
      <p class="header-desc">查看公司全体员工与小易助手的历史对话记录，监控服务质量与业务动态。</p>
    </header>

    <div class="logs-layout">
      <!-- User Sidebar -->
      <aside class="user-sidebar glass-panel">
        <div class="sidebar-header">
          <h3>员工列表</h3>
          <span class="count-badge">{{ userStats.length }} 人活跃</span>
        </div>
        <div class="user-list">
          <div 
            class="user-item" 
            :class="{ active: selectedAuditKey === null }"
            @click="selectUser(null)"
          >
            <div class="user-main">
              <span class="user-name">全部记录</span>
            </div>
          </div>
          <div 
            v-for="stat in userStats" 
            :key="stat.audit_key" 
            class="user-item"
            :class="{ active: selectedAuditKey === stat.audit_key }"
            @click="selectUser(stat.audit_key)"
          >
            <div class="user-main">
              <span class="user-name">{{ stat.display_name || stat.username }}</span>
              <span class="msg-count">{{ stat.message_count }} 条</span>
            </div>
            <div class="user-last-active">
              最后使用: {{ formatDate(stat.last_active) }}
            </div>
          </div>
        </div>
      </aside>

      <!-- Logs Content Area -->
      <div class="logs-main-content glass-panel">
        <div class="toolbar">
          <div class="search-box">
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="搜索员工姓名或聊天内容..." 
              @keyup.enter="fetchLogs(0)"
            />
            <button @click="fetchLogs(0)" class="btn-search">搜索</button>
          </div>
          <div class="pagination">
            <button :disabled="currentPage === 0" @click="fetchLogs(currentPage - 1)" class="btn-page">上一页</button>
            <span class="page-info">第 {{ currentPage + 1 }} 页</span>
            <button :disabled="logs.length < limit" @click="fetchLogs(currentPage + 1)" class="btn-page">下一页</button>
          </div>
        </div>

        <div class="logs-scroller">
          <div v-if="loading" class="loading-state">数据加载中...</div>
          <div v-else-if="logs.length === 0" class="empty-state">目前没有找到任何对话记录。</div>
          
          <div v-for="log in logs" :key="log.id" class="log-card">
            <div class="log-header">
              <span class="user-badge">{{ log.display_name || log.username }}</span>
              <span v-if="log.login_username && log.login_username !== (log.display_name || log.username)" class="login-account">
                账号: {{ log.login_username }}
              </span>
              <span class="time">{{ new Date(log.created_at).toLocaleString() }}</span>
              <span class="cost-time" v-if="log.processing_time">耗时: {{ log.processing_time.toFixed(2) }}s</span>
            </div>
            <div class="message-bubble user-msg">
              <div class="bubble-title">员工:</div>
              <div class="bubble-content">{{ log.user_message }}</div>
            </div>
            <div class="message-bubble ai-msg">
              <div class="bubble-title">小易:</div>
              <div class="bubble-content" v-html="formatOutput(log.ai_response)"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { renderMarkdown } from '@/utils/markdown'

const logs = ref([])
const userStats = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedAuditKey = ref(null)
const currentPage = ref(0)
const limit = 20

const fetchUserStats = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('/api/admin/chat-logs/users', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    userStats.value = res.data
  } catch (e) {
    console.error("无法加载用户列表:", e)
  }
}

const fetchLogs = async (page = 0) => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('/api/admin/chat-logs', {
      params: {
        skip: page * limit,
        limit,
        audit_key: selectedAuditKey.value === null ? undefined : selectedAuditKey.value,
        search: searchQuery.value || undefined
      },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    logs.value = res.data
    currentPage.value = page
  } catch (e) {
    console.error("查无记录或发生错误:", e)
  } finally {
    loading.value = false
  }
}

const selectUser = (auditKey) => {
  selectedAuditKey.value = auditKey
  fetchLogs(0)
}

const formatDate = (dateStr) => {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}-${d.getDate()} ${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`
}

const formatOutput = (text) => {
  return renderMarkdown(text)
}

onMounted(() => {
  fetchUserStats()
  fetchLogs()
})
</script>

<style scoped>
.logs-container {
  height: 100vh;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: radial-gradient(circle at top right, rgba(16, 185, 129, 0.08), transparent 40%),
              radial-gradient(circle at bottom left, rgba(59, 130, 246, 0.08), transparent 40%);
  overflow: hidden; /* Prevent body scroll */
}

.logs-layout {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0; /* Important for flex children to scroll */
}

.user-sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}
.sidebar-header h3 { font-size: 16px; color: var(--text-primary); margin: 0; }
.count-badge { font-size: 11px; color: var(--text-secondary); background: #f1f5f9; padding: 2px 8px; border-radius: 10px; }

.user-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 4px;
}

.user-item {
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.user-item:hover { background: rgba(59, 130, 246, 0.05); }
.user-item.active { 
  background: white; 
  border-color: var(--accent-color); 
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.user-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.user-name { font-weight: 700; color: var(--text-primary); font-size: 14px; }
.msg-count { font-size: 11px; color: var(--accent-color); font-weight: 600; }
.user-last-active { font-size: 11px; color: var(--text-secondary); }

.logs-main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  min-width: 0;
}

.logs-header {
  padding: 10px 0 20px 0;
}
.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.brand .gradient-text {
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.header-desc {
  color: var(--text-secondary);
  font-size: 13px;
  margin: 0;
}

.nav-btn-outline {
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
  background: white;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  margin-bottom: 16px;
}

.search-box {
  display: flex;
  gap: 8px;
}
.search-box input {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  width: 260px;
  font-size: 13px;
}
.btn-search {
  padding: 8px 16px;
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 12px;
}
.btn-page {
  padding: 6px 12px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}
.page-info { font-size: 12px; color: var(--text-secondary); }

.logs-scroller {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-right: 8px;
}

.log-card {
  background: white;
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.log-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 8px;
}

.user-badge {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 600;
}

.login-account {
  font-size: 12px;
  color: var(--text-secondary);
}

.message-bubble {
  padding: 12px;
  border-radius: 8px;
}

.user-msg {
  background: rgba(59, 130, 246, 0.03);
  border-left: 3px solid #60a5fa;
}

.ai-msg {
  background: rgba(16, 185, 129, 0.03);
  border-left: 3px solid #34d399;
}

.bubble-title {
  font-weight: 700;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text-primary);
}

.bubble-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.bubble-content :deep(p) { margin: 0 0 0.8em 0; }
.bubble-content :deep(p:last-child) { margin-bottom: 0; }
.bubble-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin: 10px 0;
}
.bubble-content :deep(th), .bubble-content :deep(td) {
  border: 1px solid #e2e8f0;
  padding: 6px 10px;
}
.bubble-content :deep(th) { background: #f8fafc; }
</style>
