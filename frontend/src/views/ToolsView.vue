<template>
  <div class="tools-page">
    <header class="tools-hero glass-panel">
      <div class="hero-copy">
        <router-link to="/" class="back-link">← 返回小易助手</router-link>
        <p class="eyebrow">Xiao Yi Tool Hub</p>
        <h1>智能工具中心</h1>
        <p class="hero-desc">
          这里统一整理小易当前可用的业务工具与行政工具。工具页面保持原有 UI，不重绘、不改版。
        </p>
      </div>
      <div class="hero-badge">
        <span>{{ totalTools }} 个工具</span>
        <small>H5 Only</small>
      </div>
    </header>

    <section v-if="loading" class="state-card glass-panel">
      <p>正在加载工具目录...</p>
    </section>

    <section v-else-if="errorMessage" class="state-card glass-panel error">
      <p>{{ errorMessage }}</p>
      <button class="retry-btn" @click="fetchTools">重新加载</button>
    </section>

    <section v-else class="group-list">
      <article
        v-for="group in groups"
        :key="group.key"
        class="group-card glass-panel"
      >
        <div class="group-header">
          <div>
            <p class="group-kicker">{{ group.key === 'business' ? 'Business Tools' : 'Admin Tools' }}</p>
            <h2>{{ group.title }}</h2>
          </div>
          <span class="group-count">{{ group.tools.length }} 个</span>
        </div>

        <div class="tool-grid">
          <div
            v-for="tool in group.tools"
            :key="tool.slug"
            class="tool-card"
          >
            <div class="tool-meta">
              <h3>{{ tool.title }}</h3>
              <p>{{ tool.summary }}</p>
              <div class="tool-badges">
                <span v-if="tool.is_new" class="badge-new">NEW</span>
                <span v-if="tool.version" class="badge-meta">v{{ tool.version }}</span>
                <span v-if="tool.updated_at" class="badge-meta">更新 {{ formatDate(tool.updated_at) }}</span>
              </div>
              <p v-if="tool.changelog" class="tool-changelog">{{ tool.changelog }}</p>
            </div>
            <button class="open-btn" @click="openTool(tool.runtime_path)">
              打开工具
            </button>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'

const groups = ref([])
const loading = ref(false)
const errorMessage = ref('')

const totalTools = computed(() =>
  groups.value.reduce((count, group) => count + (group.tools?.length || 0), 0)
)

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString('zh-CN')
}

const fetchTools = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await axios.get('/api/tools/')
    groups.value = Array.isArray(response.data?.groups) ? response.data.groups : []
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || error.message || '工具目录加载失败'
  } finally {
    loading.value = false
  }
}

const openTool = (runtimePath) => {
  if (!runtimePath) return
  const link = document.createElement('a')
  link.href = runtimePath
  link.target = '_blank'
  link.rel = 'noopener noreferrer'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

onMounted(fetchTools)
</script>

<style scoped>
.tools-page {
  min-height: 100vh;
  padding: 36px;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 32%),
    radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.12), transparent 28%),
    linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
  overflow-y: auto;
}

.tools-hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 32px;
  margin-bottom: 24px;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 760px;
}

.back-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  width: fit-content;
}

.eyebrow {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.24em;
  color: #2563eb;
  font-weight: 700;
}

.tools-hero h1 {
  font-size: 34px;
  line-height: 1.1;
  color: var(--text-primary);
}

.hero-desc {
  color: var(--text-secondary);
  max-width: 640px;
}

.hero-badge {
  min-width: 160px;
  align-self: flex-start;
  padding: 18px 20px;
  border-radius: 20px;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
  color: white;
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: right;
}

.hero-badge span {
  font-size: 30px;
  font-weight: 800;
}

.hero-badge small {
  color: rgba(255, 255, 255, 0.72);
  text-transform: uppercase;
  letter-spacing: 0.18em;
}

.state-card {
  padding: 28px 32px;
  color: var(--text-secondary);
}

.state-card.error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.retry-btn,
.open-btn {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.retry-btn {
  color: white;
  background: #2563eb;
}

.group-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.group-card {
  padding: 28px;
}

.group-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.group-kicker {
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #64748b;
  margin-bottom: 8px;
}

.group-header h2 {
  font-size: 24px;
  color: var(--text-primary);
}

.group-count {
  padding: 8px 14px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 700;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.tool-card {
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.18);
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 18px;
  min-height: 180px;
}

.tool-meta {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tool-meta h3 {
  font-size: 18px;
  color: var(--text-primary);
}

.tool-meta p {
  color: var(--text-secondary);
  font-size: 14px;
}

.tool-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.badge-new,
.badge-meta {
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
}

.badge-new {
  background: #dc2626;
  color: #fff;
}

.badge-meta {
  background: #eef2ff;
  color: #1e3a8a;
}

.tool-changelog {
  margin-top: 2px;
  font-size: 13px;
  color: #475569;
}

.open-btn {
  width: fit-content;
  color: white;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.18);
}

.open-btn:hover,
.retry-btn:hover {
  transform: translateY(-1px);
}

@media (max-width: 900px) {
  .tools-page {
    padding: 18px;
  }

  .tools-hero {
    flex-direction: column;
    padding: 24px;
  }

  .hero-badge {
    text-align: left;
  }
}
</style>
