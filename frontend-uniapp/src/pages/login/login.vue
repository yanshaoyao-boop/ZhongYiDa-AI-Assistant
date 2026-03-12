<template>
	<view class="login-page">
		<view class="zen-login-bg"></view>

		<view class="login-shell fade-in">
			<view class="zen-login-card login-container">
				<view class="brand-header">
					<image src="/static/zyd_logo.png" mode="widthFix" class="brand-logo" />
					<text class="brand-name">小易智能助手</text>
					<text class="brand-slogan">链接全球机遇 · 成就每个伙伴</text>
				</view>

				<view class="input-section">
					<view class="input-group" :class="{ active: focused === 'user' }">
						<text class="input-label">工号 / 用户名</text>
						<view class="input-box">
							<input
								v-model="username"
								type="text"
								placeholder="admin"
								placeholder-style="color: rgba(15, 23, 42, 0.3)"
								@focus="focused = 'user'"
								@blur="focused = ''"
							/>
						</view>
					</view>

					<view class="input-group" :class="{ active: focused === 'pass' }">
						<text class="input-label">访问密码</text>
						<view class="input-box">
							<input
								v-model="password"
								type="password"
								password
								placeholder="请输入访问密码"
								placeholder-style="color: rgba(15, 23, 42, 0.3)"
								@focus="focused = 'pass'"
								@blur="focused = ''"
								@confirm="handleLogin"
							/>
						</view>
					</view>
				</view>

				<view v-if="auth.error" class="error-tip">
					<text>{{ auth.error }}</text>
				</view>

				<button class="zen-login-btn" :class="{ disabled: auth.loading }" @tap="handleLogin">
					<text v-if="!auth.loading">登录</text>
					<text v-else>登录中...</text>
				</button>

				<view class="legal-footer">
					<text>2026仲易达集团</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()

const username = ref('')
const password = ref('')
const focused = ref('')

const handleLogin = async () => {
	if (!username.value || !password.value) {
		uni.showToast({ title: '请输入工号和密码', icon: 'none' })
		return
	}

	const success = await auth.login(username.value, password.value)
	if (success) {
		uni.setStorageSync('zyd_post_login_fresh_chat', '1')
		uni.setStorageSync('zyd_last_login_username', username.value)
		uni.reLaunch({ url: '/pages/chat/chat' })
	}
}

onMounted(() => {
	username.value = uni.getStorageSync('zyd_last_login_username') || ''
	if (auth.isAuthenticated) {
		uni.reLaunch({ url: '/pages/chat/chat' })
	}
})
</script>

<style scoped>
.login-container::before {
	content: '';
	display: block;
	max-width: 372px;
	width: 154px;
	box-shadow: 0 24px 56px rgba(77, 102, 161, 0.12);
}

.login-page {
	min-height: 100vh;
	background: linear-gradient(180deg, #edf3fb 0%, #e8eef7 100%);
	display: flex;
	align-items: center;
	justify-content: center;
	position: relative;
	overflow: hidden;
}

.zen-login-bg {
	position: absolute;
	width: 200%;
	height: 200%;
	top: -50%;
	left: -50%;
	background:
		radial-gradient(circle at center, rgba(59, 130, 246, 0.08) 0%, transparent 50%),
		radial-gradient(circle at bottom right, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
	z-index: 1;
}

.login-shell {
	width: 100%;
	padding: 72rpx 48rpx;
	z-index: 2;
	display: flex;
	justify-content: center;
}

.zen-login-card {
	width: 100%;
	max-width: 400px;
	min-height: 960rpx;
	background: #ffffff;
	border-radius: 28px;
	padding: 92rpx 48rpx 76rpx;
	box-shadow: 0 24px 56px rgba(77, 102, 161, 0.12);
	border: 1px solid rgba(15, 23, 42, 0.04);
	display: flex;
	flex-direction: column;
	justify-content: flex-start;
}

.brand-header {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-bottom: 68rpx;
	width: 100%;
}

.brand-logo {
	width: 320rpx;
	max-width: 100%;
	margin-bottom: 32rpx;
}

.brand-name {
	width: 100%;
	font-size: 68rpx;
	font-weight: 800;
	color: var(--slate-900);
	letter-spacing: -1rpx;
	margin-bottom: 18rpx;
	text-align: center;
	white-space: nowrap;
}

.brand-slogan {
	font-size: 28rpx;
	color: #25539b;
	font-weight: 700;
	text-align: center;
	letter-spacing: 1rpx;
	line-height: 1.5;
}

.input-section {
	display: flex;
	flex-direction: column;
	gap: 54rpx;
}

.input-group {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	border-bottom: 2px solid var(--slate-100);
	padding-bottom: 16rpx;
	transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.input-group.active {
	border-color: var(--slate-900);
}

.input-label {
	font-size: 24rpx;
	color: var(--slate-500);
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 2rpx;
}

.input-box {
	background: rgba(255, 255, 255, 0.9);
	border: 1px solid rgba(15, 23, 42, 0.06);
	border-radius: 16px;
	padding: 0 24rpx;
	height: 54px;
	display: flex;
	align-items: center;
}

.input-box input {
	color: var(--slate-900);
	font-size: 36rpx;
	font-weight: 600;
	height: 60rpx;
	width: 100%;
}

.zen-login-btn {
	background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
	color: #ffffff;
	height: 112rpx;
	border-radius: 999rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-weight: 800;
	font-size: 34rpx;
	margin-top: 52rpx;
	box-shadow: 0 18rpx 42rpx rgba(37, 99, 235, 0.22);
	transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.zen-login-btn::after {
	border: none;
}

.zen-login-btn:active {
	transform: scale(0.98);
	box-shadow: 0 10rpx 24rpx rgba(37, 99, 235, 0.18);
}

.zen-login-btn.disabled {
	opacity: 0.72;
	transform: none;
}

.error-tip {
	margin-top: 28rpx;
	color: #ef4444;
	font-size: 26rpx;
	text-align: center;
	background: rgba(239, 68, 68, 0.1);
	padding: 20rpx;
	border-radius: 16px;
}

.legal-footer {
	margin-top: 72rpx;
	text-align: center;
}

.legal-footer text {
	font-size: 24rpx;
	color: var(--slate-500);
}

.fade-in {
	animation: fadeIn 0.8s ease-out;
}

@keyframes fadeIn {
	from {
		opacity: 0;
		transform: translateY(40rpx);
	}

	to {
		opacity: 1;
		transform: translateY(0);
	}
}
</style>
