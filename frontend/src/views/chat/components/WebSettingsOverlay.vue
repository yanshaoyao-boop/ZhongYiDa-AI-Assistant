<template>
	<Teleport to="body">
		<div v-if="show" class="premium-modal-backdrop" @click.self="$emit('update:show', false)">
			<div class="premium-modal settings-modal animate-modal">
				<div class="modal-header">
					<div class="header-top">
						<div class="header-main">
							<Settings class="header-icon" />
							<h3>用户设置</h3>
						</div>
						<button class="close-btn-inner" @click="$emit('update:show', false)"><X /></button>
					</div>
				</div>

				<div class="modal-body custom-scrollbar">
					<!-- 输出长度 -->
					<div class="settings-section">
						<div class="settings-label">📝 小易回复长度偏好</div>
						<p class="settings-desc">控制小易每次回答内容的详尽程度</p>
						<div class="output-length-group">
							<button
								v-for="opt in outputLengthOptions"
								:key="opt.value"
								:class="['length-btn', { active: outputLength === opt.value }]"
								@click="$emit('update:outputLength', opt.value)"
							>
								<span class="length-icon">{{ opt.icon }}</span>
								<span class="length-label">{{ opt.label }}</span>
								<span class="length-desc">{{ opt.desc }}</span>
							</button>
						</div>
					</div>

					<div class="settings-divider"></div>

					<!-- 修改密码 -->
					<div class="settings-section">
						<div class="settings-label">🔑 修改密码</div>
						<p class="settings-desc">修改您的登录密码（至少 6 位）</p>
						<div class="pwd-form">
							<input
								:value="pwdForm.oldPwd"
								type="password"
								placeholder="请输入当前密码"
								class="settings-input"
								@input="updateField('oldPwd', $event)"
							/>
							<input
								:value="pwdForm.newPwd"
								type="password"
								placeholder="请输入新密码（至少 6 位）"
								class="settings-input"
								@input="updateField('newPwd', $event)"
							/>
							<input
								:value="pwdForm.confirmPwd"
								type="password"
								placeholder="再次确认新密码"
								class="settings-input"
								@input="updateField('confirmPwd', $event)"
							/>
							<div v-if="pwdMsg" :class="['pwd-msg', pwdMsg.type]">{{ pwdMsg.text }}</div>
							<button class="pwd-submit-btn" @click="$emit('submitPwd')" :disabled="pwdLoading">
								{{ pwdLoading ? '提交中...' : '确认修改' }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<script setup>
import { Settings, X } from 'lucide-vue-next'

defineProps({
	show: {
		type: Boolean,
		default: false
	},
	outputLength: {
		type: String,
		default: 'medium'
	},
	pwdForm: {
		type: Object,
		default: () => ({ oldPwd: '', newPwd: '', confirmPwd: '' })
	},
	pwdMsg: {
		type: Object,
		default: null
	},
	pwdLoading: {
		type: Boolean,
		default: false
	}
})

const emit = defineEmits(['update:show', 'update:outputLength', 'update:pwdForm', 'submitPwd'])

const outputLengthOptions = [
	{ value: 'short', icon: '⚡', label: '简洁', desc: '精炼核心要点，适合快速查询' },
	{ value: 'medium', icon: '📋', label: '标准', desc: '均衡详细，适合日常对话' },
	{ value: 'long', icon: '📄', label: '详细', desc: '完整展开，适合复杂分析' }
]

const updateField = (field, event) => {
	emit('update:pwdForm', { field, value: event.target.value })
}
</script>

<style scoped>
.premium-modal-backdrop {
	position: fixed;
	inset: 0;
	background: rgba(15, 23, 42, 0.45);
	backdrop-filter: blur(8px);
	z-index: 1000;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 24px;
}

.premium-modal {
	width: 100%;
	max-width: 500px;
	background: rgba(255, 255, 255, 0.98);
	border-radius: 24px;
	box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.animate-modal {
	animation: slideZoomIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideZoomIn {
	from { opacity: 0; transform: scale(0.95) translateY(20px); }
	to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-header {
	padding: 24px 28px;
	border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.header-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.header-main {
	display: flex;
	align-items: center;
	gap: 12px;
}

.header-icon {
	color: #64748b;
}

h3 {
	margin: 0;
	font-size: 20px;
	font-weight: 700;
	color: #1e293b;
}

.close-btn-inner {
	background: #f1f5f9;
	border: none;
	width: 32px;
	height: 32px;
	border-radius: 10px;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #64748b;
	cursor: pointer;
}

.modal-body {
	flex: 1;
	overflow-y: auto;
	padding: 24px 28px;
}

.settings-section {
	margin-bottom: 24px;
}

.settings-label {
	font-size: 15px;
	font-weight: 700;
	color: #1e293b;
	margin-bottom: 6px;
}

.settings-desc {
	font-size: 13px;
	color: #94a3b8;
	margin-bottom: 16px;
}

.output-length-group {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.length-btn {
	display: flex;
	flex-direction: column;
	text-align: left;
	padding: 12px 16px;
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	cursor: pointer;
	transition: all 0.2s;
}

.length-btn.active {
	background: #eff6ff;
	border-color: #3b82f6;
	box-shadow: 0 4px 12px rgba(37, 99, 235, 0.05);
}

.length-icon { margin-right: 8px; font-size: 18px; }
.length-label { font-weight: 700; color: #1e293b; font-size: 14px; }
.length-desc { font-size: 12px; color: #64748b; margin-top: 4px; }

.settings-divider {
	height: 1px;
	background: rgba(0, 0, 0, 0.05);
	margin: 24px 0;
}

.pwd-form {
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.settings-input {
	height: 44px;
	padding: 0 16px;
	background: #f1f5f9;
	border-radius: 10px;
	border: 1px solid transparent;
	font-size: 14px;
	color: #1e293b;
}
.settings-input:focus {
	outline: none;
	border-color: #3b82f6;
	background: #ffffff;
}

.pwd-msg {
	font-size: 12px;
	padding: 8px 12px;
	border-radius: 6px;
}
.pwd-msg.error { background: #fee2e2; color: #b91c1c; }
.pwd-msg.success { background: #dcfce7; color: #15803d; }

.pwd-submit-btn {
	height: 46px;
	background: #2563eb;
	color: white;
	border-radius: 10px;
	border: none;
	font-weight: 600;
	cursor: pointer;
	margin-top: 8px;
}
.pwd-submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
