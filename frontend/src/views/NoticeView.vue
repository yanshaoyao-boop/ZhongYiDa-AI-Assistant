<template>
  <div class="notice-container">
    <header class="notice-header glass-panel">
      <div class="header-main">
        <div class="header-left">
          <router-link to="/admin" class="back-link">← 返回后台</router-link>
          <h1>重要通知管理</h1>
        </div>
        <div class="header-right">
          <button class="btn-primary notice-btn" :disabled="!noticeContent.trim() || noticeSending" @click="sendNotice">
            <span v-if="noticeSending">发布中...</span>
            <span v-else>发布新通知</span>
          </button>
        </div>
      </div>
    </header>

    <div class="notice-content">
      <section class="notice-input-section glass-panel">
        <div class="section-header">
          <IconBell class="icon-lg text-orange" />
          <h2>发布新通知</h2>
        </div>
        <p class="section-desc">请输入需要向全体成员展示的内容，发布后将立即出现在“小易助手”的通知模块中。</p>
        
        <textarea 
          v-model="noticeContent" 
          placeholder="请输入通知的具体内容..." 
          class="notice-textarea"
          rows="6"
        ></textarea>
      </section>

      <section class="notice-history-section glass-panel">
        <div class="section-header">
          <IconHistory class="icon-lg text-blue" />
          <h2>历史通知记录清单</h2>
        </div>
        
        <div v-if="loading" class="notice-loading">正在读取历史记录...</div>
        <div v-else-if="historyNotices.length === 0" class="notice-empty">暂无历史通知</div>
        <div v-else class="notice-table-container">
          <table class="notice-table">
            <thead>
              <tr>
                <th>发布时间</th>
                <th>发布人</th>
                <th>通知内容</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="n in historyNotices" :key="n.id">
                <td class="date-cell">{{ formatDate(n.created_at) }}</td>
                <td class="publisher-cell">{{ n.created_by_name || '系统发布' }}</td>
                <td class="content-cell">{{ n.content }}</td>
                <td class="action-cell">
                  <button class="btn-delete" @click="deleteNotice(n.id)">🗑️ 删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Bell as IconBell, History as IconHistory } from 'lucide-vue-next'

const noticeContent = ref('')
const noticeSending = ref(false)
const historyNotices = ref([])
const loading = ref(true)

const fetchHistoryNotices = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/notices/history')
    historyNotices.value = res.data
  } catch (err) {
    console.error('Failed to fetch notices:', err)
  } finally {
    loading.value = false
  }
}

const sendNotice = async () => {
  if (!noticeContent.value.trim()) return
  noticeSending.value = true
  try {
    await axios.post('/api/notices/', { content: noticeContent.value })
    noticeContent.value = ''
    fetchHistoryNotices()
    alert('通知发布成功！')
  } catch (err) {
    alert(`发布失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    noticeSending.value = false
  }
}

const deleteNotice = async (id) => {
  if (!confirm('确定要永久删除这条记录吗？')) return
  try {
    await axios.delete(`/api/notices/${id}`)
    fetchHistoryNotices()
  } catch (err) {
    alert(`删除失败: ${err.message}`)
  }
}

const formatDate = (dateStr) => {
  const d = new Date(dateStr)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(fetchHistoryNotices)
</script>

<style scoped>
.notice-container {
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
  min-height: 100vh;
}

.notice-header {
  padding: 24px 32px;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h1 {
  font-size: 24px;
  margin-top: 8px;
}

.back-link {
  font-size: 14px;
  color: var(--text-secondary);
  text-decoration: none;
}

.notice-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.icon-lg {
  width: 24px;
  height: 24px;
}

.text-orange { color: #f97316; }
.text-blue { color: #3b82f6; }

.section-desc {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 20px;
}

.notice-textarea {
  width: 100%;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: white;
  font-family: inherit;
  font-size: 15px;
  outline: none;
  resize: vertical;
  line-height: 1.6;
}

.notice-textarea:focus {
  border-color: var(--accent-color);
}

.notice-input-section, .notice-history-section {
  padding: 32px;
}

.notice-loading, .notice-empty {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.notice-table-container {
  margin-top: 8px;
}

.notice-table {
  width: 100%;
  border-collapse: collapse;
}

.notice-table th {
  text-align: left;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 14px;
}

.notice-table td {
  padding: 16px;
  border-bottom: 1px solid rgba(0,0,0,0.03);
  font-size: 14px;
}

.date-cell {
  white-space: nowrap;
  color: var(--text-secondary);
  width: 200px;
}

.publisher-cell {
  width: 140px;
  white-space: nowrap;
  color: var(--text-secondary);
  font-weight: 600;
}

.content-cell {
  color: var(--text-primary);
  line-height: 1.5;
  white-space: pre-wrap;
}

.action-cell {
  width: 100px;
  text-align: right;
}

.btn-primary {
  background: var(--primary-gradient);
  color: white;
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
}

.notice-btn {
  background: linear-gradient(135deg, #f97316 0%, #fb923c 100%);
}

.btn-delete {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete:hover {
  background: var(--danger-color);
  color: white;
}
</style>
