<template>
  <div class="lab-container">
    <header class="lab-header glass-panel">
      <div class="header-main">
        <div class="header-left">
          <router-link to="/admin" class="back-link">← 返回后台</router-link>
          <h1>小易实验室 (Xiao Yi Lab)</h1>
        </div>
        <div class="header-right">
          <button @click="saveSettings" class="btn-primary" :disabled="saving">
            <span v-if="saving">正在保存...</span>
            <span v-else>💾 保存全局配置</span>
          </button>
        </div>
      </div>
      <p class="header-desc">调节“小易智能助手”的核心大脑参数，实时生效。</p>
    </header>

    <div class="lab-content">
      <!-- 核心性格参数 -->
      <section class="config-card glass-panel">
        <div class="card-header">
          <IconZap class="icon-blue" />
          <h2>核心性格与智商</h2>
        </div>
        
        <div class="form-item">
          <div class="label-box">
            <label>严谨度 (Temperature)</label>
            <span class="value-badge">{{ settings.ai_temperature }}</span>
          </div>
          <input type="range" v-model="settings.ai_temperature" min="0" max="1" step="0.1" class="slider" />
          <p class="tip">越低越严谨（适合查报价），越高越有创造力（适合对练话术）。</p>
        </div>

        <div class="form-item">
          <div class="label-box">
            <label>上下文记忆长度 (Max History)</label>
            <span class="value-badge">{{ settings.ai_max_history }}</span>
          </div>
          <input type="range" v-model="settings.ai_max_history" min="2" max="30" step="2" class="slider" />
          <p class="tip">记得之前多少轮对话。过长会消耗更多流量且响应变慢。</p>
        </div>
      </section>

      <!-- 搜索与能力开关 -->
      <section class="config-card glass-panel">
        <div class="card-header">
          <IconSearch class="icon-purple" />
          <h2>搜索与 RAG 能力</h2>
        </div>

        <div class="form-item row">
          <div class="info">
            <label>内部知识库库检索 (RAG)</label>
            <p class="tip">开启后，小易会查阅你上传的 PDF/Excel 信息。</p>
          </div>
          <label class="switch">
            <input type="checkbox" v-model="settings.ai_enable_rag_bool">
            <span class="slider-round"></span>
          </label>
        </div>

        <div class="form-item">
          <div class="label-box">
            <label>检索参考深度 (Top K)</label>
            <span class="value-badge">{{ settings.ai_search_top_k }}</span>
          </div>
          <input type="range" v-model="settings.ai_search_top_k" min="1" max="10" step="1" class="slider" />
          <p class="tip">每次回答参考多少条内部资料。默认建议 5 条。</p>
        </div>

        <div class="form-item row">
          <div class="info">
            <label>Web 联网搜索能力</label>
            <p class="tip">允许小易在找不到答案时搜索实时航运新闻、汇率等。</p>
          </div>
          <label class="switch">
            <input type="checkbox" v-model="settings.ai_enable_search_bool">
            <span class="slider-round"></span>
          </label>
        </div>
      </section>

      <!-- 品牌与文案 -->
      <section class="config-card glass-panel full-width">
        <div class="card-header">
          <IconMessageSquare class="icon-green" />
          <h2>欢迎辞与引导语</h2>
        </div>
        
        <div class="form-item">
          <label>新对话欢迎辞</label>
          <textarea 
            v-model="settings.ai_welcome_message" 
            placeholder="请输入小易在开启新对话时的自我介绍..."
            rows="4"
          ></textarea>
          <p class="tip">这能影响用户对小易的第一印象，支持 Markdown 格式。</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch } from 'vue'
import axios from 'axios'
import { Zap as IconZap, Search as IconSearch, MessageSquare as IconMessageSquare } from 'lucide-vue-next'

const settings = reactive({
  ai_temperature: "0.3",
  ai_max_history: "10",
  ai_enable_rag_bool: true,
  ai_enable_search_bool: true,
  ai_search_top_k: "5",
  ai_welcome_message: ""
})

const saving = ref(false)

const fetchSettings = async () => {
  try {
    const res = await axios.get('/api/settings/')
    const data = res.data
    // Map string values to our reactive object
    if (data.ai_temperature) settings.ai_temperature = data.ai_temperature
    if (data.ai_max_history) settings.ai_max_history = data.ai_max_history
    if (data.ai_search_top_k) settings.ai_search_top_k = data.ai_search_top_k
    if (data.ai_welcome_message) settings.ai_welcome_message = data.ai_welcome_message
    
    settings.ai_enable_rag_bool = data.ai_enable_rag === 'true'
    settings.ai_enable_search_bool = data.ai_enable_search === 'true'
  } catch (err) {
    console.error("Failed to fetch settings:", err)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const payload = {
      settings: {
        ai_temperature: settings.ai_temperature.toString(),
        ai_max_history: settings.ai_max_history.toString(),
        ai_search_top_k: settings.ai_search_top_k.toString(),
        ai_welcome_message: settings.ai_welcome_message,
        ai_enable_rag: settings.ai_enable_rag_bool ? 'true' : 'false',
        ai_enable_search: settings.ai_enable_search_bool ? 'true' : 'false'
      }
    }
    await axios.patch('/api/settings/', payload)
    alert("设置已成功保存，并在下次对话中生效。")
  } catch (err) {
    alert("保存失败: " + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

onMounted(fetchSettings)
</script>

<style scoped>
.lab-container {
  height: 100vh;
  overflow-y: auto;
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  background: radial-gradient(circle at top right, rgba(16, 185, 129, 0.08), transparent 40%),
              radial-gradient(circle at bottom left, rgba(37, 99, 235, 0.08), transparent 40%);
}

.lab-header {
  padding: 24px 32px;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.back-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
}

.lab-header h1 {
  font-size: 28px;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
  margin: 0;
}

.header-desc {
  color: var(--text-secondary);
  font-size: 14px;
}

.lab-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 24px;
}

.config-card {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.full-width {
  grid-column: 1 / -1;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.card-header h2 {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.icon-blue { color: #3b82f6; }
.icon-purple { color: #8b5cf6; }
.icon-green { color: #10b981; }

.form-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-item.row {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.label-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label-box label {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.value-badge {
  background: var(--bg-tertiary);
  color: var(--accent-color);
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 700;
  border: 1px solid var(--border-color);
}

.tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
}

textarea {
  width: 100%;
  padding: 16px;
  border-radius: 12px;
  border: 1.5px solid var(--border-color);
  background: white;
  font-family: inherit;
  font-size: 14px;
  color: var(--text-primary);
  resize: vertical;
}

textarea:focus {
  outline: none;
  border-color: var(--accent-color);
}

/* Slider Style */
.slider {
  -webkit-appearance: none;
  width: 100%;
  height: 6px;
  background: var(--border-color);
  border-radius: 5px;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  background: var(--accent-color);
  cursor: pointer;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

/* Switch Style */
.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 26px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider-round {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-color);
  transition: .4s;
  border-radius: 34px;
}

.slider-round:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider-round {
  background: var(--accent-color);
}

input:checked + .slider-round:before {
  transform: translateX(24px);
}

.btn-primary {
  background: var(--primary-gradient);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

</style>
