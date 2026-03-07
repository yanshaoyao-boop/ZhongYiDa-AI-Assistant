<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-box">
          <img src="/logo.png" alt="Logo" />
        </div>
        <h1>小易智能助手</h1>
        <p class="slogan">链接全球机遇 · 成就每个伙伴</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input 
            id="username"
            v-model="username" 
            type="text" 
            placeholder="请输入用户名" 
            required 
            :disabled="auth.loading"
          />
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <input 
            id="password"
            v-model="password" 
            type="password" 
            placeholder="请输入密码" 
            required 
            :disabled="auth.loading"
          />
        </div>

        <div v-if="auth.error" class="error-msg">
          {{ auth.error }}
        </div>

        <button type="submit" :disabled="auth.loading" class="login-btn">
          <span v-if="auth.loading" class="loader"></span>
          <span v-else>立即登录</span>
        </button>
      </form>

      <div class="login-footer">
        <p>&copy; 2026 仲易达集团</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const hasLogo = ref(true)

const handleLogin = async () => {
  if (!username.value || !password.value) return
  
  const success = await auth.login(username.value, password.value)
  if (success) {
    router.push('/')
  }
}

onMounted(() => {
  // 如果已登录，直接跳首页
  if (auth.isAuthenticated) {
    router.push('/')
  }
})
</script>

<style scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
  color: #334e68;
  overflow: hidden;
}

.login-card {
  width: 420px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 32px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-box {
  width: 180px;
  height: auto;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-box img {
  width: 100%;
  height: auto;
  object-fit: contain;
}

h1 {
  font-size: 28px;
  margin-bottom: 12px;
  color: #102a43;
  font-weight: 800;
  letter-spacing: 1px;
}

.slogan {
  color: #243b53;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(to right, #2563eb, #7c3aed);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-top: 4px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  color: #486581;
  font-weight: 600;
  margin-left: 4px;
}

input {
  background: white;
  border: 1.5px solid #d9e2ec;
  border-radius: 14px;
  padding: 14px 18px;
  color: #102a43;
  font-size: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.error-msg {
  color: #ef4444;
  background: #fee2e2;
  padding: 12px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  text-align: center;
}

.login-btn {
  margin-top: 8px;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: white;
  border: none;
  border-radius: 14px;
  padding: 16px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3);
}

.login-btn:active {
  transform: translateY(0);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.login-footer {
  margin-top: 32px;
  text-align: center;
  color: #829ab1;
  font-size: 13px;
  font-weight: 500;
}

.loader {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
