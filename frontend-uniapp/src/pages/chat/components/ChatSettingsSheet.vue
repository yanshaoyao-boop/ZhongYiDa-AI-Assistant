<template>
  <view v-if="show" class="settings-overlay" @tap="$emit('setshow', false)">
    <view class="settings-sheet" @tap.stop>
      <view class="settings-sheet-header">
        <view class="header-main-info">
          <text class="settings-sheet-title">用户设置</text>
          <text class="settings-sheet-desc">管理回复长度偏好与账号安全</text>
        </view>
        <text class="settings-sheet-close" @tap="$emit('setshow', false)">×</text>
      </view>

      <view class="settings-section">
        <text class="settings-section-title">回复详略程度</text>
        <text class="settings-section-desc">控制小易每次回答内容的精简或详细程度</text>
        <view class="length-option-list">
          <button
            v-for="option in outputLengthOptions"
            :key="option.value"
            :class="['length-option-btn', { active: outputLength === option.value }]"
            @tap="$emit('setoutputlength', option.value)"
          >
            <view class="length-option-main">
              <text class="length-option-icon">{{ option.icon }}</text>
              <text class="length-option-label">{{ option.label }}</text>
            </view>
            <text class="length-option-desc">{{ option.desc }}</text>
          </button>
        </view>
      </view>

      <view class="settings-section">
        <text class="settings-section-title">修改登录密码</text>
        <text class="settings-section-desc">定期更换密码有助于保障您的账号安全</text>
        <view class="pwd-form-group">
          <input
            :value="pwdForm.oldPwd"
            class="settings-input"
            type="password"
            password
            placeholder="当前旧密码"
            @input="updatePwd('oldPwd', $event)"
          />
          <input
            :value="pwdForm.newPwd"
            class="settings-input"
            type="password"
            password
            placeholder="新密码（至少 6 位）"
            @input="updatePwd('newPwd', $event)"
          />
          <input
            :value="pwdForm.confirmPwd"
            class="settings-input"
            type="password"
            password
            placeholder="再次确认新密码"
            @input="updatePwd('confirmPwd', $event)"
          />
          <button class="settings-submit-btn" :disabled="pwdLoading" @tap="$emit('submitpwd')">
            {{ pwdLoading ? '正在提交中...' : '确认修改新密码' }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
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
  pwdLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['setshow', 'setoutputlength', 'updatepwdform', 'submitpwd'])

const outputLengthOptions = [
  { value: 'short', icon: '·', label: '简洁', desc: '精炼核心要点，适合快速查看' },
  { value: 'medium', icon: '●', label: '标准', desc: '均衡详略，适合日常对话' },
  { value: 'long', icon: '▮', label: '详细', desc: '完整展开，适合复杂分析' }
]

const updatePwd = (field, event) => {
  emit('updatepwdform', { field, value: event.detail.value })
}
</script>

<style scoped>
.settings-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
}

.settings-sheet {
  width: 100%;
  background: #ffffff;
  border-radius: 24px 24px 0 0;
  padding: 24px;
  padding-bottom: calc(24px + env(safe-area-inset-bottom));
  max-height: 85vh;
  overflow-y: auto;
}

.settings-sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.settings-sheet-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  display: block;
  margin-bottom: 4px;
}

.settings-sheet-desc {
  font-size: 13px;
  color: #94a3b8;
}

.settings-sheet-close {
  font-size: 28px;
  color: #94a3b8;
  padding: 4px;
  line-height: 1;
}

.settings-section {
  margin-bottom: 32px;
}

.settings-section-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
  display: block;
}

.settings-section-desc {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 20px;
  display: block;
}

.length-option-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.length-option-btn {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px 16px;
  text-align: left;
  display: flex;
  flex-direction: column;
}

.length-option-btn.active {
  background: #eff6ff;
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
}

.length-option-btn::after,
.settings-submit-btn::after {
  border: none;
}

.length-option-main {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.length-option-icon {
  margin-right: 8px;
  font-size: 16px;
}

.length-option-label {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.length-option-desc {
  font-size: 12px;
  color: #64748b;
}

.pwd-form-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.settings-input {
  height: 48px;
  padding: 0 16px;
  background: #f1f5f9;
  border-radius: 12px;
  font-size: 15px;
  color: #1e293b;
}

.settings-submit-btn {
  height: 50px;
  background: #2563eb;
  color: #ffffff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
  margin-top: 8px;
  border: none;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.settings-submit-btn:disabled {
  opacity: 0.6;
}
</style>
