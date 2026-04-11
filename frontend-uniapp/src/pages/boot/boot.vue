<template>
  <view class="boot-page">
    <view class="boot-card">
      <text class="boot-title">小程序启动诊断页</text>
      <text class="boot-desc">如果你在手机预览里能看到这个页面，说明 App 本身已经启动成功，白屏问题在登录页或其依赖链。</text>

      <view class="boot-meta">
        <text class="boot-meta-line">env={{ envVersion }}</text>
        <text class="boot-meta-line">api={{ apiBaseDisplay }}</text>
      </view>

      <button class="boot-btn primary" @tap="goLogin">进入登录页</button>
      <button class="boot-btn" @tap="goChat">直接进入聊天页</button>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getApiBase } from '@/utils/api'

const envVersion = ref('unknown')

const apiBaseDisplay = computed(() => {
  return getApiBase() || '未配置'
})

const detectEnvVersion = () => {
  // #ifdef MP-WEIXIN
  try {
    const accountInfo = wx.getAccountInfoSync?.()
    envVersion.value = accountInfo?.miniProgram?.envVersion || 'unknown'
  } catch (error) {
    envVersion.value = 'unknown'
  }
  // #endif
}

const goLogin = () => {
  uni.reLaunch({ url: '/pages/login/login' })
}

const goChat = () => {
  uni.reLaunch({ url: '/pages/chat/chat' })
}

onMounted(() => {
  detectEnvVersion()
})
</script>

<style scoped>
.boot-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #eef4ff 0%, #f8fbff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
}

.boot-card {
  width: 100%;
  background: #ffffff;
  border-radius: 32rpx;
  padding: 56rpx 40rpx;
  box-shadow: 0 24rpx 56rpx rgba(37, 99, 235, 0.1);
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.boot-title {
  font-size: 42rpx;
  font-weight: 800;
  color: #0f172a;
}

.boot-desc {
  font-size: 28rpx;
  line-height: 1.7;
  color: #475569;
}

.boot-meta {
  background: #f8fafc;
  border-radius: 20rpx;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.boot-meta-line {
  font-size: 24rpx;
  color: #1e293b;
  word-break: break-all;
}

.boot-btn {
  height: 96rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e2e8f0;
  color: #0f172a;
  font-size: 30rpx;
  font-weight: 700;
}

.boot-btn::after {
  border: none;
}

.boot-btn.primary {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  color: #ffffff;
}
</style>
