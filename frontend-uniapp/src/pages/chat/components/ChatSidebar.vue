<template>
  <view>
    <view v-if="isOpen" class="sidebar-overlay" @tap="$emit('close')"></view>

    <view v-if="isOpen" class="sidebar glass-panel">
      <view class="sidebar-header">
        <button class="new-chat-btn" @tap="$emit('newchat')">
          <text class="new-chat-plus">+</text>
          <text>新对话</text>
        </button>
      </view>

      <scroll-view scroll-y class="session-list">
        <view
          v-for="session in sessions"
          :key="session.id"
          :class="['session-item', { active: session.id === currentSessionId }]"
          @tap="$emit('switchsession', session.id)"
        >
          <text class="session-title">{{ session.title || '新对话' }}</text>
          <button class="delete-btn" @tap.stop="$emit('deletesession', session.id)">×</button>
        </view>
      </scroll-view>

      <view class="sidebar-footer">
        <button class="sidebar-settings-btn" @tap="$emit('opensettings')">设置</button>
        <button v-if="isAdmin" class="sidebar-admin-btn" @tap="$emit('gotoadmin')">管理后台</button>

        <view class="sidebar-user-info">
          <view class="user-avatar-sidebar">{{ userInitial }}</view>
          <view class="user-details">
            <text class="user-name-sidebar">{{ userName }}</text>
            <button class="logout-link-sidebar" @tap="$emit('logout')">退出登录</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  sessions: {
    type: Array,
    default: () => []
  },
  currentSessionId: {
    type: [String, Number],
    default: ''
  },
  userName: {
    type: String,
    default: ''
  },
  userInitial: {
    type: String,
    default: ''
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close', 'newchat', 'switchsession', 'deletesession', 'opensettings', 'gotoadmin', 'logout'])
</script>

<style scoped>
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 99;
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 280px;
  height: 100vh;
  background: rgba(255, 255, 255, 0.96);
  z-index: 100;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 10px 0 30px rgba(0, 0, 0, 0.05);
}

.sidebar-header {
  padding: 24px 16px 12px;
}

.new-chat-btn {
  width: 100%;
  height: 48px;
  background: #2563eb;
  color: #ffffff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 500;
  border: none;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.new-chat-btn::after,
.delete-btn::after,
.sidebar-settings-btn::after,
.sidebar-admin-btn::after,
.logout-link-sidebar::after {
  border: none;
}

.new-chat-plus {
  font-size: 20px;
  margin-right: 8px;
  margin-top: -2px;
}

.session-list {
  flex: 1;
  padding: 8px 12px;
  overflow: hidden;
}

.session-item {
  padding: 12px 14px;
  border-radius: 12px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: transparent;
}

.session-item.active {
  background: rgba(37, 99, 235, 0.08);
}

.session-item.active .session-title {
  color: #2563eb;
  font-weight: 600;
}

.session-title {
  font-size: 14px;
  color: #475569;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.delete-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  line-height: 22px;
  font-size: 18px;
  color: #94a3b8;
  background: transparent;
  border: none;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  background: rgba(255, 255, 255, 0.7);
}

.sidebar-settings-btn,
.sidebar-admin-btn {
  width: 100%;
  height: 40px;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 10px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-user-info {
  display: flex;
  align-items: center;
  padding-top: 8px;
}

.user-avatar-sidebar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
  box-shadow: 0 4px 8px rgba(37, 99, 235, 0.2);
}

.user-details {
  margin-left: 12px;
  display: flex;
  flex-direction: column;
}

.user-name-sidebar {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.logout-link-sidebar {
  font-size: 11px;
  color: #ef4444;
  background: transparent;
  padding: 0;
  border: none;
  text-align: left;
  margin-top: 2px;
  line-height: 1;
}
</style>
