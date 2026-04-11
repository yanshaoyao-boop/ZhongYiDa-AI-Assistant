<template>
  <div class="notice-container">
    <header class="notice-header glass-panel">
      <div class="header-main">
        <div class="header-left">
          <router-link to="/admin" class="back-link">← 返回后台</router-link>
          <h1>重要通知与行业资讯管理</h1>
        </div>
      </div>
    </header>

    <div class="notice-content">
      <section class="notice-input-section glass-panel">
        <div class="section-header">
          <IconBell class="icon-lg text-orange" />
          <h2>发布重要通知</h2>
        </div>
        <p class="section-desc">发布后将出现在“小易助手”重要通知窗口。</p>

        <textarea
          v-model="noticeContent"
          placeholder="请输入通知的具体内容..."
          class="notice-textarea"
          rows="5"
        ></textarea>
        <div class="section-action">
          <button class="btn-primary notice-btn" :disabled="!noticeContent.trim() || noticeSending" @click="sendNotice">
            <span v-if="noticeSending">发布中...</span>
            <span v-else>发布通知</span>
          </button>
        </div>
      </section>

      <section class="notice-history-section glass-panel">
        <div class="section-header">
          <IconHistory class="icon-lg text-blue" />
          <h2>历史通知记录</h2>
        </div>

        <div v-if="loadingNotices" class="notice-loading">正在读取历史记录...</div>
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

      <section class="notice-input-section glass-panel">
        <div class="section-header">
          <IconNewspaper class="icon-lg text-cyan" />
          <h2>上传行业资讯</h2>
        </div>
        <p class="section-desc">上传后将出现在“行业资讯”窗口，列表仅展示发布时间与内容。</p>

        <textarea
          v-model="industryNewsContent"
          placeholder="请输入行业资讯内容..."
          class="notice-textarea"
          rows="5"
        ></textarea>
        <div class="section-action">
          <button class="btn-primary industry-btn" :disabled="!industryNewsContent.trim() || industryNewsSending" @click="sendIndustryNews">
            <span v-if="industryNewsSending">上传中...</span>
            <span v-else>上传资讯</span>
          </button>
        </div>
      </section>

      <section class="notice-history-section glass-panel">
        <div class="section-header">
          <IconHistory class="icon-lg text-cyan" />
          <h2>行业资讯记录</h2>
        </div>

        <div v-if="loadingIndustryNews" class="notice-loading">正在读取资讯记录...</div>
        <div v-else-if="historyIndustryNews.length === 0" class="notice-empty">暂无行业资讯</div>
        <div v-else class="notice-table-container">
          <table class="notice-table">
            <thead>
              <tr>
                <th>发布时间</th>
                <th>资讯内容</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="n in historyIndustryNews" :key="n.id">
                <td class="date-cell">{{ formatDate(n.created_at) }}</td>
                <td class="content-cell">{{ n.content }}</td>
                <td class="action-cell">
                  <button class="btn-delete" @click="deleteIndustryNews(n.id)">🗑️ 删除</button>
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
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { Bell as IconBell, History as IconHistory, Newspaper as IconNewspaper } from 'lucide-vue-next'

const noticeContent = ref('')
const noticeSending = ref(false)
const historyNotices = ref([])
const loadingNotices = ref(true)

const industryNewsContent = ref('')
const industryNewsSending = ref(false)
const historyIndustryNews = ref([])
const loadingIndustryNews = ref(true)

const fetchHistoryNotices = async () => {
  loadingNotices.value = true
  try {
    const res = await axios.get('/api/notices/history')
    historyNotices.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    console.error('Failed to fetch notices:', err)
  } finally {
    loadingNotices.value = false
  }
}

const fetchHistoryIndustryNews = async () => {
  loadingIndustryNews.value = true
  try {
    const res = await axios.get('/api/industry-news/history')
    historyIndustryNews.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    console.error('Failed to fetch industry news:', err)
  } finally {
    loadingIndustryNews.value = false
  }
}

const sendNotice = async () => {
  if (!noticeContent.value.trim()) return
  noticeSending.value = true
  try {
    await axios.post('/api/notices/', { content: noticeContent.value })
    noticeContent.value = ''
    await fetchHistoryNotices()
    alert('通知发布成功！')
  } catch (err) {
    alert(`发布失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    noticeSending.value = false
  }
}

const sendIndustryNews = async () => {
  if (!industryNewsContent.value.trim()) return
  industryNewsSending.value = true
  try {
    await axios.post('/api/industry-news/', { content: industryNewsContent.value })
    industryNewsContent.value = ''
    await fetchHistoryIndustryNews()
    alert('行业资讯上传成功！')
  } catch (err) {
    alert(`上传失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    industryNewsSending.value = false
  }
}

const deleteNotice = async (id) => {
  if (!confirm('确定要永久删除这条通知吗？')) return
  try {
    await axios.delete(`/api/notices/${id}`)
    await fetchHistoryNotices()
  } catch (err) {
    alert(`删除失败: ${err.message}`)
  }
}

const deleteIndustryNews = async (id) => {
  if (!confirm('确定要永久删除这条资讯吗？')) return
  try {
    await axios.delete(`/api/industry-news/${id}`)
    await fetchHistoryIndustryNews()
  } catch (err) {
    alert(`删除失败: ${err.message}`)
  }
}

const formatDate = (dateStr) => {
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return String(dateStr || '')
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
    .format(d)
    .replace(/\//g, '-')
}

onMounted(() => {
  fetchHistoryNotices()
  fetchHistoryIndustryNews()
})
</script>

<style scoped>
.notice-container {
  height: 100vh;
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
}

@supports (height: 100dvh) {
  .notice-container {
    height: 100dvh;
  }
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
  gap: 24px;
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
.text-cyan { color: #0891b2; }

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

.section-action {
  margin-top: 14px;
}

.notice-input-section, .notice-history-section {
  padding: 28px;
}

.notice-loading, .notice-empty {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.notice-table-container {
  margin-top: 8px;
  overflow-x: auto;
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
  width: 120px;
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

.industry-btn {
  background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
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

@media (max-width: 768px) {
  .notice-container {
    padding: 20px;
    gap: 20px;
  }

  .notice-header {
    padding: 18px 20px;
  }

  .header-left h1 {
    font-size: 22px;
  }

  .notice-input-section,
  .notice-history-section {
    padding: 20px;
  }

  .notice-table {
    min-width: 760px;
  }
}
</style>
